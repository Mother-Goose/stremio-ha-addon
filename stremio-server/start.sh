#!/bin/sh
# Wrapper to ensure environment variables reach the Stremio server process
export IPADDRESS=0-0-0-0
export AUTO_SERVER_URL=1
exec node server.js
