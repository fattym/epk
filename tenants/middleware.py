from django.utils.deprecation import MiddlewareMixin
from .models import School

_thread_locals = {}

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        host = request.get_host()
        subdomain = host.split('.')[0] if '.' in host else host
        try:
            school = School.objects.using('default').get(code=subdomain, is_active=True)
            _thread_locals['school'] = school
            request.school = school
        except School.DoesNotExist:
            _thread_locals['school'] = None
            request.school = None


def get_current_school():
    return _thread_locals.get('school')
