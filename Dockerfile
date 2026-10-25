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