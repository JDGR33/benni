#!/bin/sh

# Exit immediately if any command fails.
set -e

# Load environment variables captured at container startup.
. /etc/profile.d/container_env.sh

# Ensure relative paths in main.py resolve from the app directory.
cd /app

# Execute the Python job once per cron trigger.
python main.py
