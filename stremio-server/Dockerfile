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

# Rewrite buster sources to archive.debian.org BEFORE any apt-get update.
# Debian buster (10) is EOL, so deb.debian.org no longer serves it; the
# upstream Dockerfile's sed fix must run first, otherwise apt-get update fails.
RUN sed -i 's/deb\.debian/archive.debian/g' /etc/apt/sources.list

# Install wget (needed for server.js fetch)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates wget \
    && rm -rf /var/lib/apt/lists/*

# ——— ffmpeg install — —
# The jellyfin-ffmpeg .deb filename includes the architecture token
# (e.g. _arm64.deb); the upstream Dockerfile hardcoded -buster.deb (no arch),
# which fails because dpkg can't resolve the file. Use the real filename.
# apt-get update is needed here too: the earlier step purged /var/lib/apt/lists.
RUN ARCH=$(dpkg --print-architecture) \
    && wget https://repo.jellyfin.org/archive/ffmpeg/debian/${JELLYFIN_VERSION}/jellyfin-ffmpeg_${JELLYFIN_VERSION}-buster_${ARCH}.deb \
    && apt-get update \
    && apt-get install -y ./jellyfin-ffmpeg_${JELLYFIN_VERSION}-buster_${ARCH}.deb \
    && rm jellyfin-ffmpeg_${JELLYFIN_VERSION}-buster_${ARCH}.deb

# ——— Copy download script + fetch server.js via build arg ———
COPY download_server.sh download_server.sh
RUN chmod +x download_server.sh && VERSION=${VERSION} ./download_server.sh

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