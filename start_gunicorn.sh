#!/bin/bash
# Manual gunicorn start script
# Use this when systemd is not available or you can't use sudo.
#
# Usage:
#   chmod +x start_gunicorn.sh
#   nohup ./start_gunicorn.sh > /dev/null 2>&1 &

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# Activate virtualenv if present
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi

# Use production settings
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-core.settings_production}"

# Load .env if python-dotenv is available
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Start gunicorn
exec gunicorn \
    --workers 3 \
    --bind unix:${SCRIPT_DIR}/epk.sock \
    --umask 000 \
    --access-logfile ${SCRIPT_DIR}/logs/gunicorn-access.log \
    --error-logfile ${SCRIPT_DIR}/logs/gunicorn-error.log \
    core.wsgi:application
