#!/bin/bash
set -e
PROJECT_DIR="/home/personal/personalweb/epk"
FRONTEND_SRC_DIR="${PROJECT_DIR}/frontend/codingclubskenya"
FRONTEND_OUT_DIR="/home/personal/personalweb/frontend-apk-web"
DOMAIN=${1:-codingclubskenya.com}
if [ "$EUID" -ne 0 ]; then
  SUDO="sudo"
else
  SUDO=""
fi

cd "${PROJECT_DIR}/backend"
source "${PROJECT_DIR}/venv/bin/activate"
git pull origin master
pip install -r requirements.txt
python manage.py migrate --settings=core.settings_production
python manage.py collectstatic --noinput --settings=core.settings_production
cd "${FRONTEND_SRC_DIR}"
npm ci 2>/dev/null || npm install
cat > .env.production << ENV
VITE_API_URL=https://${DOMAIN}
ENV
npm run build
mkdir -p "${FRONTEND_OUT_DIR}"
$SUDO cp -r dist/* "${FRONTEND_OUT_DIR}/"
$SUDO chown -R devops:devops "${FRONTEND_OUT_DIR}"
$SUDO systemctl restart gunicorn
$SUDO systemctl restart celery
$SUDO systemctl restart celery-beat
$SUDO systemctl reload nginx
echo "Update complete!"
