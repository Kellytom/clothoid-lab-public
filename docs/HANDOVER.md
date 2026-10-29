# clothoid-lab handover

**Updated:** 2026-10-25  
**Status:** local MVP and public remote MVP are both live.  
**Current code:** latest commit in this repository; run `git log -1` on the handover machine.

## Public endpoints

| What | URL |
|---|---|
| Local MVP | `http://127.0.0.1:8000/` |
| Remote MVP | `https://<your-service>.run.app` |
| Alternate Cloud Run URL | `https://<your-service>-<project-number>.us-central1.run.app` |

Both remote URLs work; the `...uc.a.run.app` form is the canonical
`status.url` from Cloud Run.

The remote page and `/api/render` were smoke-tested after deployment:

- home: HTTP 200, ~0.12 s warm
- render: HTTP 200, ~0.69 s over the network, ~0.37 s server-side
- test design: G2, inside tolerance

## Google Cloud resources

| Item | Value |
|---|---|
| Account | `kelly.aquinas.tom@gmail.com` |
| Project | `<your-gcp-project>` |
| Region | `us-central1` |
| Cloud Run service | `clothoid-web` |
| Current revision | `clothoid-web-00002-wsp` |
| Runtime | Linux container, Python 3.12, Debian slim |
| Image repository | `us-central1-docker.pkg.dev/<your-gcp-project>/cloud-run-source-deploy/clothoid-web` |
| Min / max instances | `0` / `1` |
| Concurrency | `2` |
| CPU / memory | `1 vCPU` / `512 MiB` |
| Request timeout | `60 s` |
| Authentication | public, unauthenticated |
| Budget guardrail | `clothoid-lab guardrail`, **$1/month**, alerts at 50%, 90%, 100% |

## What the MVP is

A deliberately small web harness around the existing geometry engine:

- `web/server.py` — Python standard-library HTTP server. No FastAPI, no
  requirements, no database.
- `web/static/index.html`, `app.js`, `style.css` — plain HTML/CSS/JS page.
- `/api/render` accepts a design JSON, width, page, tolerance and split; calls
  `clothoid_lab.cli.render`; returns the SVG, report text, summary info and
  elapsed milliseconds.
- `/api/presets` and `/api/cap` expose the four presets and the existing cap
  families; `/api/caps` lists `out/caps`.
- The native Clothoids engine is reached through `ctypes`
  (`clothoid_lab/backend/bertolazzi.py`).
- The page can load presets/caps, edit the design JSON, preview the SVG,
  download SVG/JSON, and show the engine report.

The design semantics are unchanged: millimetres at 1:1, **+y up**, standard
200 × 250 mm sheet, 10 mm ribbon (5 mm each side) where selected, 0.5 mm cap
stroke. The SVG writer flips at output; design and JSON remain y-up.

Class I caps are `cap-1` … `cap-27`; class II leaves are `cap-pt-1` … `cap-pt-9`.
In the UI, class II caps leave the ribbon width empty on purpose: adding constant
width rails to a two-edge leaf puts a diamond at its point.

Tests: **96 pass**, including 4 web tests (`tests/test_web.py`).

## Local versus remote

| Capability | Local Mac | Cloud Run |
|---|---|---|
| Run Python | yes | yes |
| Run the native C++ library | yes, `.dylib` | yes, `.so` built into image |
| Compile C++ | yes, locally | only during Cloud Build, never at runtime |
| Edit source and see it immediately | yes | no; rebuild/redeploy required |
| Interactive shell / SSH | yes | no |
| Persistent local files | yes | no; image files are read-only, `/tmp` is ephemeral |
| Background daemons / long-lived workers | yes | no; HTTP request driven |
| Public HTTPS URL | no (unless a tunnel is added) | yes |
| Arbitrary TCP/UDP | yes | no; HTTP(S) on `$PORT` only |
| Install OS packages at runtime | yes | no; packages must be in the image |
| Docker inside the runtime | no local Docker | no Docker-in-container |
| Scale | one Mac | 0 → 1 instance currently |
| Cost model | electricity | free allowance, then pay-as-you-go |
| Availability | dies when Mac sleeps | available while service exists |
| Data | Mac filesystem | stateless; no database or disk |

### The local MVP

Start it from the repository root:

```sh
.venv/bin/python web/server.py
open http://127.0.0.1:8000/
```

It uses the locally built `build/libclothoidlab.dylib`. The server is still
running in the original session at `127.0.0.1:8000`; a new session can start it
again with the command above.

### The remote MVP

Cloud Run runs the same Python server in a Linux container. The build is split
into two images:

1. **Engine base** (`engine/Dockerfile`, built by `cloudbuild.engine.yaml`): a
   Debian bookworm stage installs `clang` and compiles the vendored Clothoids
   sources and `csrc/` into `libclothoidlab.so`; the runtime stage is
   `python:3.12-slim` plus `libstdc++6` and that `.so`. Pushed to
   `us-central1-docker.pkg.dev/<your-gcp-project>/cloud-run-source-deploy/clothoid-engine:2026-10-26`.
   Rebuild only when `vendor/`, `csrc/`, or `scripts/build-native.sh` changes.
2. **App image** (root `Dockerfile`): starts FROM the engine base and copies
   `clothoid_lab/`, `web/`, and `out/caps/`. Every UI or Python change rebuilds
   only this thin layer.

The app build uses an app-only `.gcloudignore` that drops `vendor/`, `csrc/`,
`scripts/`, and `engine/`, so an app deploy uploads about 100 files and never
runs the C++ compiler. The engine build uses `.gcloudignore.engine`, which keeps
the vendored tree and drops `web/`, `clothoid_lab/`, and `out/`.

The process listens on `$PORT` (`8080`), with `HOST=0.0.0.0`.

The Linux `.so` is deliberately built inside Debian bookworm. A locally
downloaded Ubuntu 24.04 artifact requires glibc 2.38 and will **not** run on the
Debian bookworm runtime; do not substitute it without changing the runtime base.

## Local/remote parity

The local and remote apps are the same app at the same level: same `web/` code,
same 36 caps, same presets, and the same rendered result.

`scripts/check-parity.py` verifies:

- `index.html`, `app.js`, `style.css` are byte-identical;
- `/api/presets` and `/api/caps` match;
- a `cap-14` render produces the same SVG and report on both.

Run it while the local server is up:

```sh
.venv/bin/python scripts/check-parity.py
```

The last check passed all seven comparisons. The two native libraries differ
only by platform (Mach-O `.dylib` locally, ELF `.so` remotely); the output is
identical at the app’s precision.

## The limiting factor

It is **not** “Cloud Run cannot run binaries or Python.” It can. The limits are
the shape of the runtime and the free allowance:

1. **Stateless, request-driven container.** No persistent disk, no daemon, no
   long-running background process, no shell. State must live in a database,
   object store, or the client.
2. **One small instance.** Current ceiling is 1 vCPU, 512 MiB, concurrency 2,
   and a 60-second request timeout. Rendering takes ~0.37 s server-side, so this
   is comfortable for this tool, not for batch or heavy CPU work.
3. **Cold starts at min instances 0.** First request after idle is roughly
   1–3 seconds; later requests are warm.
4. **Public unauthenticated endpoint.** Anyone with the URL can spend the free
   allowance. This is the biggest practical risk, not the language.
5. **Build, not runtime.** C++ is compiled by Cloud Build. The deployed
   container cannot compile, install, or mutate itself.
6. **Source upload.** The Docker build context includes the ~240 MB vendored
   Clothoids tree, so deploys are slower than a typical small Python app.

### Do we need a faster/paid tier for a few days?

**No.** Cloud Run is the same service; the free tier is a usage allowance, not a
slower plan. Warm renders are already sub-second. The only useful “speed”
purchase for a demo is **min instances = 1** to remove cold starts; it costs a
few dollars if left running and should be set back to 0. More CPU or memory is
not justified for the current 0.37 s render.

## What Cloud Build does

- Runs the Docker builds on Google infrastructure.
- Compiles the C++ engine for Linux, but only for the engine base image.
- Pushes images to Artifact Registry.
- Is ephemeral: it is a build machine, not the running service.
- Has a free build-minutes allowance (commonly 120 build-minutes/day; check
  current pricing and the project’s usage).
- Is not required locally: no Docker installation is needed on the Mac.

Two builds are kept separate on purpose:

```sh
# engine base — rare; only when vendor/, csrc/, or build-native.sh changes
gcloud builds submit --config cloudbuild.engine.yaml \
  --ignore-file=.gcloudignore.engine .

# app — every UI/Python change; thin upload, no compiler
gcloud run deploy clothoid-web --source . ...
```

## What Cloud Run does

- Runs the container as an HTTP service.
- Provides HTTPS, a public URL, request routing and autoscaling.
- Scales between **0 and 1** instance under the current guardrail.
- Bills request/CPU/memory usage against the free allowance.
- Does not provide SSH, persistent storage, arbitrary ports, or a general VPS.

## Lock-in: low

The application is a standard OCI container. The only Google-specific pieces are
the project, billing, Cloud Build, Artifact Registry and the Cloud Run service
configuration. The code itself does not import a Google SDK and reads only the
standard `PORT` environment variable.

To move to Fly.io, Render, Railway, a VPS, Kubernetes, or another container host:

1. Build the same `Dockerfile` there.
2. Run it with `PORT` set to the host’s expected port and `HOST=0.0.0.0`.
3. Point the host at the container.

The public URL and IAM/billing plumbing change; the geometry engine, UI and tests
do not. There is no database or proprietary data store to migrate. The
commercial “marriage” is to the Google account/billing setup, not the code.

To stop everything:

```sh
gcloud run services delete clothoid-web --region us-central1
# Optional and destructive: removes the whole project.
gcloud projects delete <your-gcp-project>
```

Deleting the Cloud Run service stops runtime charges. The $1 budget is only an
alert; it does **not** shut the service down.

## Free-tier controls

Already applied:

- `min-instances=0` — scale to zero.
- `max-instances=1` — one instance ceiling while the URL is public.
- `concurrency=2`.
- `cpu=1`, `memory=512Mi`, `timeout=60s`.
- `$1/month` budget with 50/90/100% alerts.

Typical free allowances (verify in the current Google Cloud pricing pages):

- Cloud Run: 2 million requests, 180k vCPU-seconds, 360k GiB-seconds per month.
- Cloud Build: 120 build-minutes/day for the standard machine type.
- Artifact Registry: 0.5 GB storage.

Normal phone testing should fit comfortably. The risk is sharing an
unauthenticated URL widely, not the app’s ordinary use.

## Repository map

| Path | Purpose |
|---|---|
| `web/server.py` | stdlib HTTP server, render API, presets/caps endpoints |
| `web/static/index.html` | MVP page |
| `web/static/app.js` | fetch/render/editor/download logic |
| `web/static/style.css` | page styling |
| `web/README.md` | local and container usage |
| `Dockerfile` | thin app image; starts FROM the engine base |
| `engine/Dockerfile` | engine base: C++ build + Python runtime + `.so` |
| `cloudbuild.engine.yaml` | build and push the engine base |
| `.dockerignore` | local Docker build context |
| `.gcloudignore` | small app-only Cloud Build upload |
| `.gcloudignore.engine` | engine-base build context |
| `scripts/check-parity.py` | local/remote parity smoke test |
| `tests/test_web.py` | web API tests |
| `tests/test_auth.py` | token auth and rate-limit tests |
| `clothoid_lab/` | existing geometry/policy layer |
| `clothoid_lab/piece.py` | `Piece`/`Trace` multi-trace model and renderer |
| `docs/piece-model.html` | W01 visual proof: traces, rails, mirror |
| `out/caps/` | existing cap SVGs and JSON, baked into remote image |
| `docs/HANDOVER.md` | this durable handover |
| `docs/HANDOVER.html` | browser-readable mirror |
| `docs/HANDOFF.md` | compact current-session continuation brief |
| `docs/BACKLOG.md` | execution detail for W01–W26 |
| `docs/ornament-board.html` | visual board: 85 plates, 26 work, 11 decisions |
| `docs/fleur-studies.html` | subpage: the twenty fleur studies, P01–P20 |
| `scripts/board/` | board generator, template, extractors and README |
| `next-fhandoff.md` | two-line focused handoff pointer |
| `.opencode/commands/fhandoff.md` | focused handoff command |
| `.opencode/commands/fhandon.md` | focused handon command |
| `.opencode/commands/morsel.md` | do the next backlog item |

`out/play-template.svg` is an untracked user file; leave it alone.

## Update and deploy

Local edit loop:

```sh
cd /Users/thomaskelly/developer/clothoid-lab
.venv/bin/python -m unittest discover tests
.venv/bin/python web/server.py
```

Remote deploy (rebuilds the Linux image and updates the service):

```sh
cd /Users/thomaskelly/developer/clothoid-lab
gcloud config set project <your-gcp-project>
gcloud run deploy clothoid-web \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi --cpu 1 --concurrency 2 \
  --min-instances 0 --max-instances 1 \
  --timeout 60 --port 8080 \
  --set-env-vars HOST=0.0.0.0 \
  --quiet
```

Check the service:

```sh
gcloud run services describe clothoid-web --region us-central1 \
  --format='value(status.url,status.latestReadyRevisionName)'
```

The remote service does **not** see local edits until it is redeployed. The cap
list is baked into the image; adding a cap JSON requires a rebuild.

## Security and operations

- Every route except `/health` requires **HTTP Basic auth** with a shared token.
  The username is ignored; the password is the token. The token is stored in
  Secret Manager as `clothoid-token` and mounted as `CLOTHOID_TOKEN`; the local
  copy is `~/.config/<app>/token`, outside the repository.
- `/health` is public and returns `{"ok": true}` for uptime checks. `/healthz`
  is intercepted by Google's frontend and is not used.
- Bodies are bounded at 1 MB and designs at 200 segments. `POST /api/render` is
  limited to 60 requests/minute with a burst of 20 per client address; excess
  returns 429 with `Retry-After`. The limiter is in-process, so it resets on a
  cold start and is per instance.
- There are no accounts, roles or saved designs; the token is the whole access
  model. Rotate it by adding a new Secret Manager version and redeploying.
- No secrets or service-account keys are in the repository or image.
- Cloud Run request logs and metrics are visible in the Google Cloud console.
- The budget is an alert only. Delete the service to guarantee zero runtime
  spend.

## Known issues and next steps

1. **Accounts and roles are still absent.** A shared token now gates the URL
   (W11) and a per-address render limit guards the allowance (W12), but there
   are no named users, no saved designs and no audit trail. Keep the token
   private and rotate it if it leaks.
2. **Cold starts** are visible with min instances 0. Use min 1 only for a demo
   window, then set it back.
3. **Build upload is large** because the full vendored C++ tree is sent. A
   future optimization is to build the Linux `.so` in GitHub Actions, copy only
   the runtime artifacts into an Ubuntu 24.04-compatible image, and deploy that
   smaller context. The current Debian build is the safer correctness choice.
4. **Caps are static at deploy time.** Adding `out/caps/cap-*.json` needs a
   rebuild/redeploy.
5. **Class II width behavior.** The UI intentionally clears ribbon width for
   `cap-pt-*`; do not add constant rails to the point.
6. **Local and remote native libraries differ.** Local is Mach-O `.dylib`;
   remote is ELF `.so`. Keep them platform-specific.
7. **Mobile polish** is untested beyond the responsive CSS; the page is usable
   but not yet tuned as a phone-first editor.
8. **No database, accounts, sharing, or saved designs.** This is an MVP, not a
   multi-user product.

## Continuation commands

Two **project-scoped, focused** OpenCode commands make the next session cheap to
start. They are modelled on the existing `handoff`/`handon` pattern in
`grid-8` and `ornaments`, but they carry only one action:

- **`/fhandoff [focus]`** — squares the record in `docs/HANDOFF.md`, chooses one
  focused action, writes `next-fhandoff.md` with a two-line pointer, and commits
  only the handoff files.
- **`/fhandon`** — reads `next-fhandoff.md`, follows its doc pointers, performs
  that single action, and stops. The operator runs `/fhandoff` when it is time
  to put the work down again.

They live in `.opencode/commands/` and are available when OpenCode is opened in
this repository. They are **not global**, so they do not appear in the other
projects. The `grid-8` and `ornaments` commands were not touched.

## Handoff checklist

- [ ] Open OpenCode in `clothoid-lab` and start the next session with `/fhandon`.
- [ ] Open the remote URL on the phone; load a class I cap and a `cap-pt` leaf.
- [ ] Confirm the $1 budget alert email reaches the billing admin.
- [ ] Run `git log -1` and `git status`; commit/push the MVP/handover files.
- [ ] Run `.venv/bin/python -m unittest discover tests` (expect 96 pass).
- [ ] Run `.venv/bin/python scripts/check-parity.py` (expect `PARITY OK`).
- [ ] Keep the public URL private; auth/rate limiting is deferred.
- [ ] Keep `out/play-template.svg` untouched.
