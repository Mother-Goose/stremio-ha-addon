# Stremio Server Add-on Configuration Reference

This document maps every configuration field from the HA add-on manifest to its
value inside the container, with upstream defaults explained.

## HA manifest → Container ENV mapping

| HA manifest field | Container-side effect | Dockerfile ENV it overwrites |
|---|---|---|
| `build.args.VERSION` | Selects which upstream `server.js` gets downloaded at build time | Arg `VERSION` |
| `build.args.JELLYFIN_VERSION` | Selects the Jellyfin ffmpeg `.deb` version to install | Arg `JELLYFIN_VERSION` |
| `environment.NO_CORS=1` | Sets `ENV NO_CORS=1` (already baked into Dockerfile) | `ENV NO_CORS=1` |
| `environment.APP_PATH=/config/stremio` | Sets `ENV APP_PATH=/config/stremio` (already baked into Dockerfile) | `ENV APP_PATH=/config/stremio` |
| `volumes /config/stremio:/root/.stremio-server:rw` | Makes `/root/.stremio-server` writable on the HA host via `/config` | — |
| `host_network: false` | Uses default user-network mode (not bridged) | — |

## Container ENV defaults (from Dockerfile, not overridable from HA manifest)

| ENV | Value | Source |
|---|---|---|
| `FFMPEG_BIN` | `/usr/lib/jellyfin-ffmpeg/ffmpeg` | Dockerfile — baked-in jellyfin-ffmpeg Debian package |
| `FFPROBE_BIN` | `/usr/lib/jellyfin-ffmpeg/ffprobe` | Dockerfile — baked-in jellyfin-ffmpeg Debian package |
| `CASTING_DISABLED` | `1` | Dockerfile — disables device detection |

## Overriding from the HA config editor

You can set these in the add-on's "Configuration" editor (YAML):

```yaml
FFMPEG_BIN: /custom/path/to/ffmpeg
FFPROBE_BIN: /custom/path/to/ffprobe
APP_PATH: /some/other/path
```

However, note:
- `FFMPEG_BIN` and `FFPROBE_BIN` are already correctly set inside the Dockerfile
  to the Debian jellyfin-ffmpeg paths. Override only if you have a custom ffmpeg
  installation on the HA host.
- `APP_PATH` — HA users who want to use a different data directory can set this,
  but be aware the default persists data under `/config/stremio` (recommended).
```