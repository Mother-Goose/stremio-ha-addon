# Stremio Server Home Assistant Add-on — Design Spec

**Date:** 2026-10-24
**Status:** Approved for implementation
**Author:** Claude Code
**Project Root:** `/Users/Rob/streamioserver/stremio-ha-addon/`

---

## Purpose & Scope

Package [Stremio/server-docker](https://github.com/Stremio/server-docker) as a
Home Assistant add-on that:

1. Builds a container from the official upstream Dockerfile + logic
2. Exposes HTTP (`11470`) and HTTPS (`12470`) ports on localhost
3. Mounts the Jellyfin ffmpeg/ffprobe binaries read-only (matching upstream
   `docker-compose.yml`)
4. Persists `~/.stremio-server` to a local HA volume for upgrade survival
5. Sets HA-specific defaults (`NO_CORS`, `APP_PATH`, `CASTING_DISABLED`)
6. Supports bumping to new Stremio releases via a single `VERSION` arg change

### Non-goals

- No automatic CI/CD pipeline (manual update step is acceptable)
- No custom transcoding logic (the upstream ffmpeg install handles this)
- No web UI proxy (HA users typically run their own reverse proxy)

---

## Background — Upstream Structure

The upstream `Dockerfile` ([source](https://github.com/Stremio/server-docker/blob/master/Dockerfile))
does these things:

1. `FROM node:14` (pinned; Node 14 is EOL but matches upstream)
2. Downloads jellyfin-ffmpeg `.deb` from `repo.jellyfin.org` → installs
3. `COPY download_server.sh download_server.sh`
4. Runs `download_server.sh` — which, when `$VERSION` is set, curls
   `https://dl.strem.io/server/$VERSION/$BUILD/server.js`
5. `COPY . .` (overlays repo files for custom builds)
6. Exposes `11470` (HTTP), `12470` (HTTPS)
7. ENV vars: `FFMPEG_BIN`, `FFPROBE_BIN`, `APP_PATH`, `NO_CORS`,
   `CASTING_DISABLED=1`
8. `ENTRYPOINT ["node", "server.js"]`
9. `VOLUME ["/root/.stremio-server"]`

The upstream `docker-compose.yml` mounts:
- `/bin/ffmpeg:/bin/ffmpeg:ro`
- `/bin/ffprobe:/bin/ffprobe:ro`
- Sets `FFMPEG_BIN=/bin/ffmpeg`, `FFPROBE_BIN=/bin/ffprobe`

**Key insight:** jellyfin-ffmpeg installs to `/usr/lib/jellyfin-ffmpeg/ffmpeg`
on Debian ([source][1]), not `/usr/bin/ffmpeg`. Upstream's compose assumes the
host has ffmpeg/ffprobe at those paths. For HA (which may not), we should
prefer the **baked-in** jellyfin-ffmpeg binary at the standard Debian path and
set `FFMPEG_BIN`/`FFPROBE_BIN` to point at it.

[1]: https://github.com/jellyfin/jellyfin-ffmpeg "jellyfin-ffmpeg packaging repo"

---

## Selected Approach: Forked Dockerfile (Option A)

We copy the upstream file and adapt it for HA instead of wrapping the remote URL.

**Why not Option B (remote Dockerfile URL)?**
The upstream Dockerfile uses `COPY download_server.sh download_server.sh`, which
fails when HA builds from a remote URL (build context ≠ upstream repo). Making
it work requires shipping `download_server.sh` locally anyway → lands back at
Option A.

**Why not Option C (prebuilt image)?**
Adds CI + registry complexity; update flow already simple with Option A.

### Update Flow

When Stremio releases a new version (e.g., `v4.21.1`):

1. **Check upstream** — did `Dockerfile` or `download_server.sh` change?
   - If yes → merge changes into our copies.
   - If no → just bump.
2. **Bump `VERSION`** arg in `Dockerfile` to the new release tag.
3. **Bump `addon.yaml` version** (e.g., `2` → `3`).
4. **HA users** — if registered as a repository, they get a notification to
   update. No data loss (volume mounted).

This is **minimal ongoing maintenance** because the upstream Dockerfile is
small and stable.

---

## File Structure

```
stremio-ha-addon/
├── Dockerfile
├── download_server.sh      (copied from upstream, unchanged)
├── addon.yaml              (HA add-on manifest)
├── README.md
├── CHANGELOG.md
└── docs/
    └── config.md
```

---

## File-by-File Design

### `Dockerfile` — adapted from upstream

```dockerfile
# Pin Node 14 to match upstream; EOL is acceptable here
FROM node:14

# --- Build-time args — bump VERSION here to update upstream release ---
ARG VERSION=v4.20.3
ARG BUILD=desktop
ARG JELLYFIN_VERSION=4.4.1-4

LABEL com.stremio.vendor="Smart Code Ltd."
LABEL version=${VERSION}
LABEL description="Stremio's streaming Server (HA add-on)"

SHELL ["/bin/sh", "-c"]
WORKDIR /stremio

# Install wget (needed for server.js fetch)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ——— ffmpeg install (kept identical to upstream) ———
# Fixes archive.debian.org issue present in upstream Dockerfile
RUN sed -i 's/deb\.debian/archive.debian/g' /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends wget

RUN wget https://repo.jellyfin.org/archive/ffmpeg/debian/${JELLYFIN_VERSION}/jellyfin-ffmpeg_${JELLYFIN_VERSION}-buster_$(dpkg --print-architecture).deb \
    && apt-get install -y ./jellyfin-ffmpeg_${JELLYFIN_VERSION}-buster.deb \
    && rm jellyfin-ffmpeg_${JELLYFIN_VERSION}-buster.deb

# ——— Copy download script + fetch server.js via build arg ———
COPY download_server.sh download_server.sh
RUN VERSION=${VERSION} ./download_server.sh

# Overlay any local files for custom builds
COPY . .

# Persist data
VOLUME ["/root/.stremio-server"]

# Expose service ports
EXPOSE 11470 12470

# Environment defaults — HA-specific overrides allowed via addon.yaml
ENV FFMPEG_BIN=/usr/lib/jellyfin-ffmpeg/ffmpeg
ENV FFPROBE_BIN=/usr/lib/jellyfin-ffmpeg/ffprobe
ENV APP_PATH=/config/stremio
ENV NO_CORS=1
ENV CASTING_DISABLED=1

ENTRYPOINT ["node", "server.js"]
```

**Notes:**
- `VOLUME ["/root/.stremio-server"]` + `APP_PATH=/config/stremio` in HA means
  HA maps `/config` → `/root/.stremio-server`. We must confirm HA volume logic
  in `addon.yaml` ensures this works.
- `FFMPEG_BIN`/`FFPROBE_BIN` point to the baked-in jellyfin-ffmpeg path, so users
  don't need ffmpeg on the host.
- `NO_CORS=1` is HA-friendly (lets the HA web UI reach the server).

### `download_server.sh`

Exact upstream copy → **no divergence risk**.

### `addon.yaml`

```yaml
---
name: "Stremio Server"
slug: "stremio-server"
version: "4.20.3-1"
version_str: "4.20.3-1"
description: "Self-hosted Stremio streaming server"
url: "https://github.com/Stremio/server-docker"

# --- Build config — bump `args.VERSION` to update upstream ---
build:
  dockerfile: ./Dockerfile
  args:
    VERSION: "v4.20.3"
    JELLYFIN_VERSION: "4.4.1-4"

# --- Ports exposed to HA host ---
ports:
  - port: 11470  # HTTP
  - port: 12470  # HTTPS

# --- Environment overrides ---
environment:
  - FFMPEG_BIN=/usr/lib/jellyfin-ffmpeg/ffmpeg
  - FFPROBE_BIN=/usr/lib/jellyfin-ffmpeg/ffprobe
  - APP_PATH=/config/stremio
  - NO_CORS=1

# --- Persistent data volume ---
volumes:
  - /config/stremio:/root/.stremio-server:rw

# Required by HA add-on runtime
host_network: false
arch: [amd64, arm64, armv7]
```

**Versioning scheme:** `<stremio-version>-<addon-build>` (e.g., `4.20.3-1`).
- `4.20.3` = upstream server.js version
- `-1` = revision of this add-on packaging

**Architecture support:** `amd64` (x86), `arm64` (AArch64), `armv7` (32-bit ARM)
match HA-supported boards. The upstream Dockerfile doesn't multi-arch build, so
HA's builder handles cross-compilation via its own infrastructure.

> **Open Questions (post-spec review)**:
1. Does HA's `@Supervisor` builder run QEMU emulation for `arm64`/`armv7` for Node 14 images, since upstream only ships multi-arch via community builds?

### `README.md`

Sections:
- **Overview** — what this is
- **Installation** — steps to add repo + install
- **Configuration** — configurable env vars (table)
- **Updating** — how to bump to new Stremio version
- **Usage** — port URLs, connecting Stremio app
- **Troubleshooting** — common issues

### `CHANGELOG.md`

Keep-a-changelog format, keyed by add-on version:

```
## [4.20.3-1] — 2026-10-24
- Updated to Stremio server.js v4.20.3
- Initial HA add-on packaging
```

### `docs/config.md`

Detailed configuration reference — full env var list with upstream docs links.

---

## Volume Mapping — Critical Detail

HA exposes `/config` in the add-on container as the persistent storage root.
The Stremio server writes to `$APP_PATH` (default `~/.stremio-server`).

Mapping:
| HA Side | Container Side | Purpose |
|---|---|---|
| `/config/stremio` | `/root/.stremio-server` | Persistent Stremio data/config |

In `addon.yaml`:
```yaml
volumes:
  - /config/stremio:/root/.stremio-server:rw
```

And set `APP_PATH=/config/stremio` so the app writes directly there instead of
`~/.stremio-server`.

---

## Security Considerations

| Threat | Mitigation |
|---|---|
| Server.js binary fetched at build time | Pin `VERSION` to a tagged release, not `master` |
| ffmpeg package fetched from repo.jellyfin.org | Pin exact `JELLYFIN_VERSION` |
| No TLS by default | Document that users must put a reverse proxy (NGINX/etc) in front |
| Binding to ports | Limited to localhost exposure via HA's supervisor (default) |

---

## Testing Plan

Before marking the spec complete:

1. **Build succeeds** — `docker build` with `VERSION=v4.20.3`
2. **server.js downloads** — confirm `RUN ./download_server.sh` fetched it
3. **Container starts** — `docker run` → `node server.js` runs without crash
4. **Port reachable** — `curl http://localhost:11470` returns JSON API spec
5. **ffmpeg available** — `ffmpeg -version` inside container works
6. **Config persists** — write settings.json, restart container → file survives

---

## Open Questions (for post-spec review)

1. Does HA's builder support Node 14 base images for all 3 arches?
   - If not, pin `amd64` only in `arch:` list and document.
2. Should we include `SO_REUSEADDR` workaround? (Some HA installs report port-binding lag for the Stremio server during HA restart.)
3. Health check — add a minimal check that the container responds on 11470?
