#!/bin/sh -e

# First, run certificate fetch if IPADDRESS is set
if [ -n "${IPADDRESS}" ]; then
    cd /stremio
    node certificate.js --action fetch
    FETCH_STATUS=$?

    if [ "${FETCH_STATUS}" -eq 0 ] && [ -f "/stremio-server/certificates.pem" ]; then
        echo "[cert] Certificate fetched successfully"
        # If IPADDRESS is 0-0-0-0, read the detected IP from file
        if [ "${IPADDRESS}" = "0-0-0-0" ] && [ -f "/stremio-server/detected-ip.txt" ]; then
            RESOLVED_IP=$(cat /stremio-server/detected-ip.txt)
        else
            RESOLVED_IP="${IPADDRESS}"
        fi
        # Add /etc/hosts entry so the *.stremio.rocks domain resolves
        IP_DOMAIN=$(echo "${RESOLVED_IP}" | sed 's/\./-/g')
        echo "${RESOLVED_IP} ${IP_DOMAIN}.519b6502d940.stremio.rocks" >> /etc/hosts
        # Load the cert into the config
        node certificate.js --action load --pem-path "/stremio-server/certificates.pem" --domain "${IP_DOMAIN}.519b6502d940.stremio.rocks" --json-path "/root/.stremio-server/httpsCert.json"
    else
        echo "[cert] Failed to fetch certificate — falling back to HTTP only"
    fi
fi

# Now start the server
exec node --no-deprecation server.js