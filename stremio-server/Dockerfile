# Use Node 20 Alpine — has AbortController/fetch needed by certificate.js
FROM node:20-alpine

LABEL org.opencontainers.image.source=https://github.com/Mother-Goose/stremio-ha-addon
LABEL org.opencontainers.image.description="Stremio Web Player and Server"
LABEL org.opencontainers.image.licenses=MIT
LABEL version=v4.20.3

WORKDIR /stremio

# Install bash, ffmpeg, wget, ca-certificates
RUN apk add --no-cache bash wget ca-certificates ffmpeg

# Copy download script + fetch server.js
COPY download_server.sh download_server.sh
RUN chmod +x download_server.sh && BUILD=desktop VERSION=v4.20.3 ./download_server.sh

# Copy certificate.js and start script
COPY . .
RUN chmod +x start.sh certificate.js

# Persist data
VOLUME ["/root/.stremio-server"]

# Expose service ports (mapped via config.yaml)
EXPOSE 11470 8080 12470

# Environment defaults (can be overridden via HA config options)
ENV FFMPEG_BIN=/usr/bin/ffmpeg
ENV FFPROBE_BIN=/usr/bin/ffprobe
ENV APP_PATH=/config/stremio

ENTRYPOINT ["/stremio/start.sh"]