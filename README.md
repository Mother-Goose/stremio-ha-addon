# Stremio Server Home Assistant Add-on

This add-on packages the official [Stremio/server-docker](https://github.com/Stremio/server-docker)
service as a Home Assistant add-on. It lets you self-host a Stremio streaming
server inside your HA environment.

## Features

- Exposes HTTP (`11470`) and HTTPS (`12470`) ports
- Includes Jellyfin ffmpeg/ffprobe binaries (no host ffmpeg required)
- Persists server data under `/config/stremio` (survives restarts/upgrades)
- CORS disabled by default for HA web UI access
- Casting detection disabled (irrelevant in an HA sandbox)

## Installation

1. Add the add-on repository to Home Assistant:

   ```yaml
   addons:
     - name: Stremio HA Add-on
       url: https://github.com/<your-org>/stremio-ha-addon
       repository: <your-org>/stremio-ha-addon
   ```

2. Install the `stremio-server` add-on from the repository.

3. Start the add-on. The server boots on ports 11470 (HTTP) and 12470 (HTTPS).

## Configuration

| Field | Default | Description |
|---|---|---|
| `version` | `4.20.3-1` | Add-on release version. Bump this when updating. |
| `build.args.VERSION` | `v4.20.3` | Upstream server.js release tag. |
| `build.args.JELLYFIN_VERSION` | `4.4.1-4` | Jellyfin ffmpeg package version. |
| `NO_CORS` | `1` | Disable CORS checks (needed for HA web UI). |
| `APP_PATH` | `/config/stremio` | Where server settings/certificates are stored. |
| `FFMPEG_BIN` | `/usr/lib/jellyfin-ffmpeg/ffmpeg` | Path to ffmpeg binary inside the container. |
| `FFPROBE_BIN` | `/usr/lib/jellyfin-ffmpeg/ffprobe` | Path to ffprobe binary inside the container. |

You can override `NO_CORS`, `APP_PATH`, `FFMPEG_BIN`, or `FFPROBE_BIN` per
instance via the HA add-on configuration editor.

## Updating to a new Stremio release

When Stremio publishes a new tagged release (e.g., `v4.21.1`):

1. Edit `version:` in `addon.yaml` from `4.20.3-1` to `4.21.1-1`.
2. Edit `build.args.VERSION` from `v4.20.3` to `v4.21.1`.
3. Bump the add-on `version` field — see CHANGELOG pattern `[4.20.3-1]`.
4. Publish via HA repository manifest.

That's it — one line for the server.js tag, one for the add-on version.

## Usage

- **HTTP API:** `http://<your-ha-host>:11470`
- **HTTPS API:** `https://<your-ha-host>:12470`
- **Stremio desktop app:** download from [strem.io](https://www.strem.io/) and
  connect to the server URL above.

> Tip: put a reverse proxy (NGINX, Traefik, etc.) in front of the HTTPS port
> if you want TLS termination and a friendly hostname.

## Troubleshooting

- **Server won't start:** confirm `/config/stremio` is writable on the HA host.
- **Permission denied:** the volume mount must be `rw` (see `addon.yaml`).
- **ffmpeg missing:** the Jellyfin ffmpeg package is baked into the image at
  `/usr/lib/jellyfin-ffmpeg/ffmpeg`; you don't need a host ffmpeg install.
- **Port already bound:** HA's supervisor manages the port mapping — if
  another service uses 11470/12470, stop it first.