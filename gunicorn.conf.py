import multiprocessing

BIND = "127.0.0.1:8000"
USER = "school"
WORKERS = multiprocessing.cpu_count() * 2 + 1
ACCESS_LOG = "/var/log/gunicorn/access.log"
ERROR_LOG = "/var/log/gunicorn/error.log"
LOG_LEVEL = "info"
DJANGO_SETTINGS_MODULE = "core.settings_production"
