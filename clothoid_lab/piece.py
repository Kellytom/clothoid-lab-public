"""A piece: several named traces, a mirror, and one SVG.

The engine's `Design` is one chain. An ornament is usually more than one: a
half-stroke, a band, two parallel edges, and the mirror of the ink. `Piece`
holds those traces in one object and hands the SVG writer a single set of
groups, so the page, frame and y-flip are decided once.

This is the W01 model. Terminals and the fleur grammar build on it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from . import bezier, engine, svg
from .contact import Contact
from .model import Design
from .offsets import build_rails
from .terminals import check_terminal, terminal_extension, terminal_spans


def _terminals(value) -> tuple[str, str]:
    """Normalise start/end terminals from a name, a pair, or a dict."""
    if isinstance(value, str):
        pair = (value, value)
    elif isinstance(value, dict):
        pair = (value.get("start", "butt"), value.get("end", "butt"))
    else:
        pair = tuple(value)
    if len(pair) != 2:
        raise ValueError("terminals need one kind for each end")
    return check_terminal(pair[0]), check_terminal(pair[1])


@dataclass
class Trace:
    """One named chain in a piece, optionally with a ribbon width."""

    name: str
    design: Design
    width: float | None = None
    # None follows the piece; True/False overrides it. A centred band usually
    # sets False so the mirror does not draw it twice.
    mirror: bool | None = None
    layer: str = "ink"
    # (start, end). Only ribbon traces can take a terminal other than `butt`.
    terminals: tuple[str, str] = ("butt", "butt")

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("a trace needs a name")
        if self.width is not None and self.width <= 0:
            raise ValueError("trace width must be positive")
        if not self.layer.strip():
            raise ValueError("a trace needs a layer")
        self.terminals = _terminals(self.terminals)
        if self.width is None and any(k != "butt" for k in self.terminals):
            raise ValueError("a terminal needs a ribbon width")

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "layer": self.layer,
            "width": self.width,
            "mirror": self.mirror,
            "terminals": list(self.terminals),
            "design": self.design.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Trace":
        return cls(
            name=str(data["name"]),
            design=Design.from_dict(data["design"]),
            width=None if data.get("width") is None else float(data["width"]),
            mirror=data.get("mirror"),
            layer=str(data.get("layer", "ink")),
            terminals=data.get("terminals", ("butt", "butt")),
        )


@dataclass
class Piece:
    """A named set of traces, mirrored as one drawing."""

    name: str
    traces: list[Trace]
    mirror: bool = False
    stroke: float = 1.0
    # Declared junctions: places where ink is allowed to meet. Part of the
    # model, not an argument to the measurement, so a piece remembers them.
    contacts: list[Contact] = field(default_factory=list)

    def __post_init__(self):
        if not self.traces:
            raise ValueError("a piece needs at least one trace")
        if self.stroke <= 0:
            raise ValueError("stroke width must be positive")
        if any(not isinstance(c, Contact) for c in self.contacts):
            raise ValueError("contacts must be Contact objects")

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "mirror": self.mirror,
            "stroke": self.stroke,
            "contacts": [
                {"point": list(c.point), "radius": c.radius,
                 "a": c.a, "b": c.b, "waives_clearance": c.waives_clearance}
                for c in self.contacts
            ],
            "traces": [trace.to_dict() for trace in self.traces],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict) -> "Piece":
        return cls(
            name=str(data.get("name", "untitled")),
            mirror=bool(data.get("mirror", False)),
            stroke=float(data.get("stroke", 1.0)),
            contacts=[
                Contact(tuple(c["point"]), float(c["radius"]),
                        c.get("a"), c.get("b"),
                        bool(c.get("waives_clearance", True)))
                for c in data.get("contacts", [])
            ],
            traces=[Trace.from_dict(t) for t in data.get("traces", [])],
        )


def _mirror_spans(spans: list[dict]) -> list[dict]:
    """Mirror every control point across x = 0, preserving the span order."""
    mirrored = []
    for span in spans:
        copy = dict(span)
        for key in ("p0", "c1", "c2", "p3"):
            x, y = span[key]
            copy[key] = (-x, y)
        mirrored.append(copy)
    return mirrored


class Group:
    """One drawn path in a piece: a spine, a rail or a terminal cap.

    `instance` names the drawing the path belongs to — a trace, or the mirror
    of one — so a measurement can tell "this ribbon's own two rails" from "this
    ribbon and the one beside it". `distance` is the offset a rail was built at,
    and is None for spines and caps.
    """

    __slots__ = ("name", "spans", "distance", "instance", "role")

    def __init__(self, name: str, spans: list[dict], distance: float | None = None,
                 instance: str = "", role: str = "spine"):
        self.name = name
        self.spans = spans
        self.distance = distance
        self.instance = instance or name
        self.role = role

    def __repr__(self) -> str:
        return f"Group({self.name!r}, {len(self.spans)} spans, {self.role})"


def build_piece(piece: Piece, tol: float = 0.02, max_spans: int = 64,
                split: int = 2, backend: str | None = None):
    """Build the geometry of every trace and return `(groups, info)`.

    This is the step that costs the engine calls, and it is deliberately
    separate from writing SVG: a measurement needs the same groups without a
    document, and a writer should not have to rebuild them.
    """
    groups: list[Group] = []
    report = []

    for trace in piece.traces:
        chain = engine.build(trace.design, backend=backend)
        spine, fit = bezier.fit_chain(
            chain, tol=tol, max_spans_per_segment=max_spans, split=split,
        )
        distances = list(trace.design.offsets)
        if trace.width is not None:
            distances.extend([trace.width / 2.0, -trace.width / 2.0])
        rails = build_rails(
            chain, distances, tol=tol,
            max_spans_per_segment=max_spans, split=split,
        )

        base = f"{trace.layer}/{trace.name}"
        groups.append(Group(base, spine, None, base, "spine"))
        for rail in rails:
            groups.append(Group(
                f"{base} rail {svg.num(rail['distance'], 3)}",
                rail["spans"], rail["distance"], base, "rail",
            ))

        # Terminals close the ribbon ends. They are extra geometry, so a butt
        # end adds nothing and the pre-W02 drawings stay byte-identical.
        terminals = []
        caps: list[tuple[str, list[dict]]] = []
        folded = False
        for index, end in enumerate(("start", "end")):
            kind = trace.terminals[index]
            extension = 0.0 if trace.width is None else terminal_extension(kind, trace.width)
            if kind != "butt":
                rail_pos, rail_neg = rails[-2], rails[-1]
                folded = bool(rail_pos["folds"] or rail_neg["folds"])
                if folded:
                    raise ValueError(
                        f"{base}: the {kind} terminal needs a ribbon that does "
                        f"not fold ({trace.width:g} mm wide)"
                    )
                spans = terminal_spans(rail_pos, rail_neg, kind, end=end)
                caps.append((f"{base} {end} {kind}", spans))
                groups.append(Group(caps[-1][0], spans, None, base, "cap"))
            terminals.append({
                "end": end,
                "kind": kind,
                "extension": extension,
                "fold": folded,
            })

        entry = {
            "name": trace.name,
            "layer": trace.layer,
            "fit_error": fit["error_max"],
            "rails": len(rails),
            "mirrored": piece.mirror if trace.mirror is None else bool(trace.mirror),
            "terminals": terminals,
        }
        report.append(entry)

        if entry["mirrored"]:
            mirrored_instance = f"{base} mirrored"
            groups.append(Group(mirrored_instance, _mirror_spans(spine), None,
                                mirrored_instance, "spine"))
            for rail in rails:
                groups.append(Group(
                    f"{mirrored_instance} rail {svg.num(rail['distance'], 3)}",
                    _mirror_spans(rail["spans"]), rail["distance"],
                    mirrored_instance, "rail",
                ))
            for name, spans in caps:
                suffix = name[len(base):]
                groups.append(Group(f"{mirrored_instance}{suffix}",
                                    _mirror_spans(spans), None,
                                    mirrored_instance, "cap"))

    info = {
        "piece": piece.name,
        "traces": report,
        "fit_ok": all(t["fit_error"] <= tol for t in report),
        "mirror": piece.mirror,
    }
    return groups, info


def render_piece(piece: Piece, tol: float = 0.02, prec: int = 4,
                 margin: float = 5.0, max_spans: int = 64, split: int = 2,
                 backend: str | None = None,
                 page: tuple[float, float] | None = None,
                 frame: tuple[float, float] | None = None,
                 view: str | None = None,
                 annotations: list[dict] | None = None) -> tuple[str, dict]:
    """Build every trace, mirror where asked, and write one SVG."""
    groups, info = build_piece(piece, tol=tol, max_spans=max_spans, split=split,
                               backend=backend)
    text = svg.document(
        piece, groups=[(g.name, g.spans, g.distance) for g in groups],
        prec=prec, margin=margin, page=page, frame=frame, view=view,
        annotations=annotations, linecap="butt",
    )
    return text, info
