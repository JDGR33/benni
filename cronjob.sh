#!/bin/sh
set -e

. /etc/profile.d/container_env.sh

cd /app
python main.py
