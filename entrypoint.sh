#!/bin/sh
set -e

: "${TZ:=UTC}"
export TZ

echo "[entrypoint] Starting benni scheduler (TZ=${TZ})"
printenv | sed 's/^/export /' > /etc/profile.d/container_env.sh
chmod +x /etc/profile.d/container_env.sh

echo "[entrypoint] Installed crontab:"
crontab /etc/cron.d/benni-cron
crontab -l

exec cron -f
