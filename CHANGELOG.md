# Changelog

All notable changes to this Home Assistant add-on will be documented here.

## [Unreleased]

## [4.20.3-1] - 2026-10-24

- Initial HA add-on package for Stremio server v4.20.3.
- Package wraps `Stremio/server-docker` upstream Dockerfile with HA-specific
  defaults (`APP_PATH=/config/stremio`, `NO_CORS=1`, `CASTING_DISABLED=1`).
- Exposes ports 11470 (HTTP) and 12470 (HTTPS).
- Persists `~/.stremio-server` under `/config/stremio` via HA volume mount.
- Upgrade procedure: bump `version:` + `build.args.VERSION` in `addon.yaml`.

### Upgrading from Stremio releases

See `docs/config.md` and README section "Updating to a new Stremio release".
