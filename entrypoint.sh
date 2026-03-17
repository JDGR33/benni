#!/bin/sh

# Exit immediately if any command fails.
set -e

# Default timezone to UTC if TZ is not provided from outside.
: "${TZ:=UTC}"
export TZ

# Startup log line for observability.
echo "[entrypoint] Starting benni scheduler (TZ=${TZ})"

# Persist current environment as shell exports so cron jobs can source it.
printenv | sed 's/^/export /' > /etc/profile.d/container_env.sh
chmod +x /etc/profile.d/container_env.sh

# Install the cron schedule and print it for verification at startup.
echo "[entrypoint] Installed crontab:"
crontab /etc/cron.d/benni-cron
crontab -l

# Run cron in the foreground so it becomes the container's main process.
exec cron -f
