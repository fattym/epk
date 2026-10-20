import threading

_local = threading.local()


def get_current_request():
    """Return the active HTTP request (set by AuditMiddleware) or None."""
    return getattr(_local, 'request', None)


def set_current_request(request):
    _local.request = request


def clear_request():
    if hasattr(_local, 'request'):
        del _local.request


class AuditMiddleware:
    """Store the current request on a thread-local so signal handlers can
    attribute audit entries to the acting user and IP without threading
    the request through every call site."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_request(request)
        try:
            response = self.get_response(request)
        finally:
            clear_request()
        return response
