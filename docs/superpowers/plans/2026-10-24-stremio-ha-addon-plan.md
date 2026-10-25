# Stremio Server Home Assistant Add-on Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package Stremio/server-docker as a self-contained, updatable Home Assistant add-on with pinned upstream Dockerfile, HA-specific defaults, and persistent local storage.

**Architecture:** HA add-on repo replicating the upstream Dockerfile + a small `addon.yaml` manifest. When Stremio releases a new tag, edit one `VERSION` arg in `Dockerfile` and bump the add-on version — one-line-push updates.

**Tech Stack:** Dockerfile (Node 14), shell script, YAML manifest.

**Spec:** `docs/stremio-ha-addon-design.md`

---

## Global Constraints

| Item | Exact value |
|---|---|
| Initial Stremio server.js version | `v4.20.3` (pinned; matches existing `/Users/Rob/streamioserver/server-settings.json: serverVersion: "4.21.0"` — update to 4.21.0 on first release when confirmed stable) |
| Jellyfin ffmpeg deb | `4.4.1-4-buster` (pinned exact) |
| Node base image | `node:14` (upstream-pinned; EOL but required to match upstream) |
| Default `NO_CORS` | `1` |
| Default `APP_PATH` | `/config/stremio` |
| Default data dir | `/root/.stremio-server` |
| Allowed arches | `[amd64, arm64, armv7]` |
| Supported OS | Linux (HA hosts) |
| No CI/CD pipeline (manual step acceptable) | Must ship without automated test hooks |

## Review Focus

| Input / failure mode | Expected behavior | Test owner |
|---|---|---|
| No host ffmpeg/ffprobe installed | Add-on container uses baked-in jellyfin-ffmpeg at `/usr/lib/jellyfin-ffmpeg/ffmpeg` instead of falling back to `/bin/ffmpeg` | Task 3 |
| Build fails at `RUN ./download_server.sh` | Fails loudly with error message; not silently killed | Task 5 |
| User changes only `args.VERSION` in `addon.yaml` | Manifest updates pull new server.js tag without touching Dockerfile or add-on version | Task 7 |
| Upstream publishes `master` without tag | Not pulled — `VERSION` arg must be set to a tagged release; build fails if bad tag given | Task 5 |

---

## Task 1: Scaffold project + acquire upstream files

**Files:**
- Create: `/Users/Rob/streamioserver/stremio-ha-addon/Dockerfile`
- Create: `/Users/Rob/streamioserver/stremio-ha-addon/download_server.sh`
- Modify: `/Users/Rob/streamioserver/stremio-ha-addon/.gitignore` (if needed — optional later)

**Interfaces:** N/A — this is file setup only.

- [ ] **Step 1:** Create directory `/Users/Rob/streamioserver/stremio-ha-addon/` with `Dockerfile`, `download_server.sh`, plus empty stubs `README.md`, `CHANGELOG.md`, and `docs/config.md`.
- [ ] **Step 2:** Copy upstream `Dockerfile` from `https://raw.githubusercontent.com/Stremio/server-docker/master/Dockerfile` into the new `Dockerfile`.
- [ ] **Step 3:** Copy upstream `download_server.sh` from `https://raw.githubusercontent.com/Stremio/server-docker/master/download_server.sh` into the new file (exact copy, no edits).

Run verification: `cat /Users/Rob/streamioserver/stremio-ha-addon/download_server.sh` should match the upstream content.

---

## Task 2: Adapt Dockerfile for HA defaults

**Files:**
- Modify: `/Users/Rob/streamioserver/stremio-ha-addon/Dockerfile`

**Interfaces:** Produces a working Dockerfile that accepts a `VERSION` build arg. Later tasks consume it via `build.dockerfile: ./Dockerfile`.

- [ ] **Step 1:** Patch the upstream Dockerfile. Specifically make these changes:
  1. Replace `ENV FFMPEG_BIN=` with `ENV FFMPEG_BIN=/usr/lib/jellyfin-ffmpeg/ffmpeg` (point at baked-in Debian package binary, since hosts may not ship `/bin/ffmpeg`).
  2. Replace `ENV FFPROBE_BIN=` with `ENV FFPROBE_BIN=/usr/lib/jellyfin-ffmpeg/ffprobe`.
  3. Replace `ENV APP_PATH=()` with `ENV APP_PATH=/config/stremio`.
  4. Set `ENV NO_CORS=1` (HA web UI needs plain HTTP access).
  5. Set `ENV CASTING_DISABLED=1` (casting devices are usually irrelevant inside an HA sandbox).
  6. Add explicit labels for vendor + description referencing the HA packaging.
  7. Keep `VOLUME ["/root/.stremio-server"]` intact so the default path is still expected.
  8. Keep build args `VERSION`, `BUILD`, `JELLYFIN_VERSION`, defaults as `v4.20.3`, `desktop`, `4.4.1-4`.
  9. Don't touch the existing `RUN sed ... /etc/apt/sources.list` workaround — leave the archive.debian fix in place (match upstream, simplify later if HA needs it too).
- [ ] **Step 2:** Run `docker build -f /Users/Rob/streamioserver/stremio-ha-addon/Dockerfile --tag tmp/test-stremio .` locally in a Docker-enabled environment. If Docker is unavailable here, note that task and delegate to a Docker host or skip — the design is Dockerfile-only.
- [ ] **Step 3:** Confirm build succeeds and inspect resulting image: `docker run --rm tmp/test-stremio sh -c 'ls /usr/lib/jellyfin-ffmpeg/ && cat /root/.stremio-server/serverVersion'` — expect both the binary presence and a "version tag" string showing v4.20.3 was fetched.

Verification: The Dockerfile's final ENV lines should include the four HA overrides.

---

## Task 3: Write addon.yaml manifest

**Files:**
- Create: `/Users/Rob/streamioserver/stremio-ha-addon/addon.yaml`

**Interfaces:** AHA-compatible manifest. Consumes everything from Tasks 1 & 2 and exposes them correctly. Bumps are intentionally isolated to `version:` and `build.args.VERSION`.

- [ ] **Step 1:** Define schema defaults:
```yaml
---
name: "Stremio Server"
slug: "stremio-server"
version: "4.20.3-1"
version_str: "4.20.3-1"
description: "Self-hosted Stremio streaming server for Home Assistant"
url: "https://github.com/Stremio/server-docker"
```
- [ ] **Step 2:** Add `build:` block using local Dockerfile:
```yaml
build:
  dockerfile: ./Dockerfile
  args:
    VERSION: "v4.20.3"
    JELLYFIN_VERSION: "4.4.1-4"
```
- [ ] **Step 3:** Add `ports`:
```yaml
ports:
  - port: 11470
  - port: 12470
```
- [ ] **Step 4:** Add `environment` (with comment describing override policy):
```yaml
environment:
  - NO_CORS=1
  - APP_PATH=/config/stremio
  # Users can override FFMPEG_BIN / FFPROBE_BIN / NO_CORS per-instance via
  #   homeassistant addon config editor if desired.
```
Note: keep `FFMPEG_BIN` and `FFPROBE_BIN` out of `environment:` because they already land from `Dockerfile` ENV; HA doesn't merge them again.
- [ ] **Step 5:** Add `volumes`:
```yaml
volumes:
  - /config/stremio:/root/.stremio-server:rw
```
- [ ] **Step 6:** Add arch/host config at top level:
```yaml
host_network: false
arch: [amd64, arm64, armv7]
```
- [ ] **Step 7:** Validate against HA manifest schema mentally — `name`, `slug`, `version`, `description`, `url`, `build.dockerfile`, `ports`, `environment`, `volumes` are all HA recognized fields.

Verification: `homeassistant addons validate addon.yaml` if available; otherwise eyeball checklist.

---

## Task 4: Write README.md

**Files:**
- Create: `/Users/Rob/streamioserver/stremio-ha-addon/README.md`

- [ ] **Step 1:** Document the "What this is" section: that it wraps `https://github.com/Stremio/server-docker` with HA-specific defaults.
- [ ] **Step 2:** Write "Installation" section: exact HA-repo instructions (deb URL, `addons.yaml` host entry).
- [ ] **Step 3:** Write "Configuration" table: `port`, `app_path`, `no_cors`, `ffmpeg_bin`, `ffprobe_bin`, `version` fields with description of what they map into inside the container.
- [ ] **Step 4:** Write "Updating" section: clear single-step flow that matches the one-line upgrade we claim — bump `version`, pull latest.
- [ ] **Step 5:** Write "Usage" section: default ports `http://<ha-host>:11470`, HTTPS `https://<ha-host>:12470`, Stremio desktop app download URL.
- [ ] **Step 6:** Write "Troubleshooting" section: (1) server fails to start → confirm `APP_PATH` mapping is actually mounting. (2) "permission denied / root" → volume mount must be rw; verify `/config` exists on HA host.

Verification: Paragraph count ≥ 6 sections visible.

---

## Task 5: Validate the build end-to-end (try where possible)

**Files:**
- None created; validates existing artifacts.

**Interfaces:** Confirms `Dockerfile + download_server.sh + addon.yaml` produce a working image + runnable container. This task owns the three HA gates.

- [ ] **Step 1:** Build with args pointing at the v4.20.3 tag:
```bash
docker build -t stremio-ha-preview . \
  -f Dockerfile \
  --build-arg VERSION=v4.20.3 \
  --build-arg JELLYFIN_VERSION=4.4.1-4
```
Check the output of every `RUN` line. If any returns exit code 1 with a non-zero returncode, fix immediately before moving on — do not skip.
- [ ] **Step 2:** Launch a container detached and wait 30 seconds:
```bash
docker run --rm -d \
  --name stremio-preview \
  -p 127.0.0.1:11470:11470 \
  -e APP_PATH=/tmp/stremio-cfg \
  stremio-ha-preview
```
Then:
- [ ] **Step 3:** Health probe via curl: `curl -s http://localhost:11470/api/...` — expect some JSON. Capture first 500 chars of body for debugging.
- [ ] **Step 4:** Check ffmpeg works: `docker exec stremio-preview ffprobe -version` — expect version line printed.
- [ ] **Step 5:** Inspect jar presence: `docker exec stremio-preview ls /root/.stremio-server | grep server` — expect `server.jar` there.
- [ ] **Step 6:** Exit the container: `docker stop stremio-preview`.

This task is the design-spec section "Testing Plan." It is non-negotiable: the spec promises build+run gates; if those don't pass in your environment, the design needs a deviation note before going live.

---

## Task 6: Write CHANGELOG.md

**Files:**
- Create: `/Users/Rob/streamioserver/stremio-ha-addon/CHANGELOG.md`

- [ ] **Step 1:** Start with `## [Unreleased]` header.
- [ ] **Step 2:** Add entry under Unreleased:
```markdown
- Initial HA add-on package: Stremio v4.20.3-1. Package `stremio-server`; exposes ports 11470/12470; persists `~/.stremio-server` under `/config/stremio`. Upgrade = bump `addons.yaml` `version:` and reload the add-on repository.
```
- [ ] **Step 3:** Leave room for future releases. Do NOT add anything else here — the changelog must stay accurate without risk of stale claims.

Verification: File contains exactly the Unreleased entry plus headers.

---

## Task 7: Document single-update procedure in README

**Files:**
- Modify: `/Users/Rob/streamioserver/stremio-ha-addon/README.md`

- [ ] **Step 1:** Under "Updating", write the one-change workflow explicitly:
```markdown
### Updating to a new Stremio release

When Stremio publishes a new tagged release (e.g., `v4.21.1`):
1. Edit `version:` in `addon.yaml` from `4.20.3-1` to `4.21.1-1`.
2. Edit `build.args.VERSION` from `v4.20.3` to `v4.21.1`.
3. Bump the add-on `version` field — see CHANGELOG pattern `[4.20.3-1]`.
4. Publish via HA repository manifest.
```
- [ ] **Step 2:** Document the manual alternative: `cp /var/lib/homeassistant/data/addons/stremio-server/addon.yaml.bak <repo>/addon.yaml` then apply only the version + args diff.

Verification: README contains the "one-change" claim.

---

## Task 8: Write docs/config.md (optional but recommended)

**Files:**
- Create: `/Users/Rob/streamioserver/stremio-ha-addon/docs/config.md`

- [ ] **Step 1:** Enumerate env vars accepted by upstream server.js with explanations: `APP_PATH`, `NO_CORS`, `CASTING_DISABLED`, `FFMPEG_BIN`, `FFPROBE_BIN`, plus any extra ones added in our Dockerfile patch.
- [ ] **Step 2:** Explain the HA-specific field mapping: where each HA manifest field lands inside the container (`build.args.*` → ENV, `environment.*` → container ENV, `volumes.*` → mounts).
- [ ] **Step 3:** Reference upstream GitHub URL for any env var definitions the HA side doesn't wrap.

Verification: Table count ≥ 5 rows, one explanatory paragraph per field.

---

## Post-implementation checklists

Before declaring done, one final round of mechanical checks:

- [ ] Every file in `stremio-ha-addon/` lives at the top level except `docs/` and `tests/` subdirs
- [ ] `download_server.sh` content == upstream bytes exactly (compare with `diff` against what we fetched earlier)
- [ ] `addon.yaml` parses cleanly with `python3 -c 'import yaml; yaml.safe_load(open("addon.yaml"))'`
- [ ] No placeholder markers (`TBD`, `FIXME`, `TODO`) remain anywhere in the project
- [ ] README mentions port 11470/12470 somewhere by name
- [ ] Dockerfile's last ENV block reads naturally and matches the design doc's file-by-file design

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-10-24-stremio-ha-addon-plan.md`. Please review the plan. Which execution approach would you prefer?

- **Subagent-driven** - A fresh subagent implements each task and a fresh reviewer checks it before the next one starts, then a whole-branch review at the end. Most thorough; costs a fresh context per task and per review.
- **Native** - I implement every task myself in this session, the way this harness runs work, then one fresh reviewer on the most capable model checks the whole branch. Cheapest and fastest; no independent review until the end.

**For this plan I recommend Native**, because the tasks depend little on each other's interfaces — each builds independently on the three shared artifacts from Tasks 1–3, and a subagent context per task would only duplicate the verification calls. Does the plan capture what you want, and which approach should we use?
