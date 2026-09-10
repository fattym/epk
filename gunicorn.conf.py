import multiprocessing
import os

# Use 127.0.0.1:8000 for nginx to proxy to
BIND = "127.0.0.1:8000"

# Get user from environment or default to devops
USER = os.environ.get('GUNICORN_USER', 'devops')

WORKERS = multiprocessing.cpu_count() * 2 + 1
WORKER_CLASS = 'sync'
THREADS = 1
TIMEOUT = 120
KEEPALIVE = 5

# Log to project directory (no root needed)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(_BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

ACCESS_LOG = os.path.join(LOG_DIR, 'gunicorn_access.log')
ERROR_LOG = os.path.join(LOG_DIR, 'gunicorn_error.log')
LOG_LEVEL = 'info'

# Environment
RAW_ENV = ['DJANGO_SETTINGS_MODULE=core.settings_production']
