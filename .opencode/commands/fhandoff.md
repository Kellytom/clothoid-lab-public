---
description: Focused handoff — square the record fast, then write next-fhandoff.md with one action
---

Focused handoff for clothoid-lab. Work in
`/Users/thomaskelly/developer/clothoid-lab`. Do not start new feature work.

**Be fast.** Target a minute, not a session. One batched probe instead of six
calls, and no network round-trips for facts that only change when you deploy.
Anything you carry forward instead of re-checking must be labelled carried, with
the date it was last checked.

1. **Probe once.** Read `docs/HANDOFF.md`, then run a single shell block with
   `--max-time 5` that prints: `git log -1 --format=%h`, `git status
   --porcelain`, and the HTTP status of local and remote. That is the whole
   default probe. Do not run `git diff` over the tree, and do not explore.
2. **Re-verify only what moved.**
   - **Tests:** run `.venv/bin/python -m unittest discover tests` only if
     something under `web/`, `clothoid_lab/`, `csrc/`, or `tests/` differs from
     HEAD. Otherwise carry the recorded count and label it carried.
   - **Cloud:** skip `gcloud` entirely (revision, limits, budget) unless this
     session deployed or changed Cloud Run, Cloud Build, or billing. Carry the
     recorded values and label them carried.
   - **Parity:** never run `scripts/check-parity.py` here; it is its own check.
   - **Handover:** read `docs/HANDOVER.md` only if a durable fact actually
     changed, and then keep `docs/HANDOVER.html` in step with it.
   - If something is genuinely ambiguous, write the uncertainty in one line
     rather than investigating it.
3. **Update `docs/HANDOFF.md`** to the current truth: local, remote, tests,
   git state, risks, and the next move. Keep it to edits, not a rewrite.
4. **Choose exactly one focused action.** If `$ARGUMENTS` is not empty, use it.
   Otherwise take the single next move from `docs/HANDOFF.md`. Do not bundle
   multiple tasks.
5. **Write `next-fhandoff.md` at the repo root.** One fenced block with exactly
   two lines:

   ```text
   Read docs/HANDOFF.md. Read docs/HANDOVER.md only for durable detail.
   You are <the single focused action>.
   ```

   Below the fence, add one line: the source doc, the date, and the commit that
   wrote it. Change nothing else in that file, and do not read it back.
6. **Commit only the handoff files** — `docs/HANDOFF.md`, `docs/HANDOVER.md`,
   `docs/HANDOVER.html`, `next-fhandoff.md`. Never add `out/play-template.svg`.
   Do not run the tests after committing.
7. **Reply with at most five bullets:** current state, the focused action, any
   blocker, the commit hash, and the next command (`/fhandon`).
