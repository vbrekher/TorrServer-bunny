#!/bin/sh
set -eu
# TorrServer upstream image uses /docker-entrypoint.sh and /opt/ts/config.
: "${TS_AUTH_USER:?TS_AUTH_USER required}"
: "${TS_AUTH_PASSWORD:?TS_AUTH_PASSWORD required}"
: "${BUNNY_WATCHDOG_TOKEN:?BUNNY_WATCHDOG_TOKEN required}"
mkdir -p /opt/ts/config /opt/ts/torrents
# Username and password are restricted to JSON-safe characters by the installer.
# Generated password is URL-safe and contains no quotes.
printf '{"%s":"%s"}\n' "$TS_AUTH_USER" "$TS_AUTH_PASSWORD" > /opt/ts/config/accs.db
chmod 600 /opt/ts/config/accs.db
export TS_PORT=8090 TS_HTTPAUTH=1 TS_CONF_PATH=/opt/ts/config
/docker-entrypoint.sh &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true' INT TERM EXIT
# Foreground proxy; if it fails the Magic Containers pod will not be considered healthy.
exec /usr/local/bin/torr-bunny-gateway
