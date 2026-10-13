#!/bin/bash
# ==============================================================================
# Production Deployment Script for School Management System
# Deploys to https://codingclubskenya.com/learningpack
#
# Run on the production server (213.199.41.219):
#   chmod +x deploy/deploy_learningpack.sh
#   ./deploy/deploy_learningpack.sh
#
# Prerequisites on the server:
#   - Ubuntu 22.04
#   - Nginx (sudo apt-get install nginx)
#   - Redis (sudo apt-get install redis-server)
#   - PostgreSQL 16 (sudo apt-get install postgresql-16)
#   - Node.js 20+
#   - Python 3.12+ with venv
#   - The domain codingclubskenya.com must point to this server's IP
# ==============================================================================
set -e

# ---- 0. Install system packages (nginx, redis, postgresql) ----
echo "[0/8] Installing system packages..."
if ! command -v nginx &> /dev/null; then
    sudo apt-get install -y nginx
fi
if ! command -v redis-server &> /dev/null; then
    sudo apt-get install -y redis-server
    sudo systemctl enable redis-server
    sudo systemctl start redis-server
fi
if ! command -v psql &> /dev/null; then
    sudo apt-get install -y postgresql postgresql-contrib
    sudo systemctl enable postgresql
    sudo systemctl start postgresql
    # Create database and user
    sudo -u postgres psql -c "CREATE USER school_user WITH PASSWORD 'GENERATED_ON_SERVER';" 2>/dev/null || true
    sudo -u postgres psql -c "CREATE DATABASE school_mgmt OWNER school_user;" 2>/dev/null || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE school_mgmt TO school_user;" 2>/dev/null || true
fi

DOMAIN="codingclubskenya.com"
PROJECT_DIR="/var/www/school_backend"
FRONTEND_DIR="/var/www/school_frontend"
DISTRIBUTOR_DIR="/var/www/school_distributor"

echo "========================================"
echo "School Management System - Production"
echo "Learningpack Deployment"
echo "========================================"

# ---- 1. Ensure directories exist ----
echo "[1/8] Creating directories..."
mkdir -p "${PROJECT_DIR}/logs"
mkdir -p "${PROJECT_DIR}/media"
mkdir -p "${FRONTEND_DIR}"
mkdir -p "${DISTRIBUTOR_DIR}"
mkdir -p /var/www/certbot
chown -R www-data:www-data "${PROJECT_DIR}/media" "${FRONTEND_DIR}" 2>/dev/null || true

# ---- 2. Update code ----
echo "[2/8] Pulling latest code..."
cd "${PROJECT_DIR}/backend"
git pull origin development 2>/dev/null || echo "Git pull skipped (no changes)"

# ---- 3. Install Python dependencies ----
echo "[3/8] Installing Python dependencies..."
if [ ! -d "${PROJECT_DIR}/venv" ]; then
    python3 -m venv "${PROJECT_DIR}/venv"
fi
source "${PROJECT_DIR}/venv/bin/activate"
pip install --upgrade pip
pip install -r "${PROJECT_DIR}/backend/requirements.txt"

# ---- 4. Environment configuration ----
echo "[4/8] Configuring environment..."
if [ ! -f "${PROJECT_DIR}/.env" ]; then
    cp "${PROJECT_DIR}/backend/.env.production.example" "${PROJECT_DIR}/.env"
    echo "Created .env from template. EDIT ${PROJECT_DIR}/.env with your credentials!"
fi

# ---- 5. Run migrations & collectstatic ----
echo "[5/8] Running migrations and collecting static files..."
source "${PROJECT_DIR}/.env"
DJANGO_SETTINGS_MODULE=core.settings_production python manage.py migrate
DJANGO_SETTINGS_MODULE=core.settings_production python manage.py collectstatic --noinput

# ---- 6. Build frontend ----
echo "[6/8] Building React frontend..."
cd "${PROJECT_DIR}/frontend/codingclubskenya"
npm ci 2>/dev/null || npm install
npm run build
cp -r dist/* "${FRONTEND_DIR}/"

# ---- 7. Build distributor (Next.js) ----
echo "[7/8] Building distributor app..."
cd "${PROJECT_DIR}/distributor"
# The distributor is a git submodule at the repo root
# If building from a fresh deploy, ensure submodule is initialized:
#   git submodule update --init --recursive
npm ci 2>/dev/null || npm install
npm run build

# ---- 8. Restart services ----
echo "[8/8] Restarting services..."
# Install systemd service files
cp "${PROJECT_DIR}/backend/deploy/gunicorn.service" /etc/systemd/system/gunicorn.service
cp "${PROJECT_DIR}/backend/deploy/celery.service" /etc/systemd/system/celery.service
cp "${PROJECT_DIR}/backend/deploy/celery-beat.service" /etc/systemd/system/celery-beat.service
cp "${PROJECT_DIR}/backend/deploy/distributor.service" /etc/systemd/system/distributor.service

systemctl daemon-reload
systemctl restart gunicorn
systemctl restart celery
systemctl restart celery-beat
systemctl restart distributor

# Configure nginx
cp "${PROJECT_DIR}/backend/deploy/nginx/learningpack" /etc/nginx/sites-available/learningpack
ln -sf /etc/nginx/sites-available/learningpack /etc/nginx/sites-enabled/learningpack
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Obtain/renew SSL certificate
certbot --nginx -d "${DOMAIN}" --email admin@${DOMAIN} --agree-tos --redirect --non-interactive 2>/dev/null || {
    echo "WARNING: Certbot SSL setup failed. Check domain DNS and certbot."
}

# ---- Summary ----
echo ""
echo "========================================"
echo "Deployment complete!"
echo "========================================"
echo ""
echo "Site:        https://${DOMAIN}/learningpack/"
echo "Admin:       https://${DOMAIN}/learningpack/admin/"
echo "API docs:    https://${DOMAIN}/learningpack/api/docs/"
echo "Distributor: https://${DOMAIN}/distributor/"
echo ""
echo "Services:"
echo "  gunicorn:   systemctl status gunicorn"
echo "  celery:     systemctl status celery"
echo "  celery-beat: systemctl status celery-beat"
echo "  distributor: systemctl status distributor"
echo "  nginx:      systemctl status nginx"
echo ""
echo "Logs:"
echo "  gunicorn-access: tail -f ${PROJECT_DIR}/logs/gunicorn-access.log"
echo "  gunicorn-error:   tail -f ${PROJECT_DIR}/logs/gunicorn-error.log"
echo "  nginx-error:      tail -f /var/log/nginx/error.log"
