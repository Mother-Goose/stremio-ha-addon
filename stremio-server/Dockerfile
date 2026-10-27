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

# Expose service ports
EXPOSE 11470 12470

# Environment defaults
ENV FFMPEG_BIN=/usr/bin/ffmpeg
ENV FFPROBE_BIN=/usr/bin/ffprobe
ENV APP_PATH=/config/stremio
ENV NO_CORS=1
ENV CASTING_DISABLED=1
ENV IPADDRESS=87.74.111.100
ENV AUTO_SERVER_URL=1

ENTRYPOINT ["/stremio/start.sh"]