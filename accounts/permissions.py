from rest_framework import permissions


STAFF_ROLES = ('ADMIN', 'STAFF', 'TEACHER')


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.role == 'ADMIN'


class IsAdminOrStaffOrTeacher(permissions.BasePermission):
    """Read: any authenticated user (school scope still applies via the queryset).
    Write (create/update/delete): restricted to ADMIN, STAFF or TEACHER.

    Prevents learners/parents/drivers from creating or mutating school
    reference data such as streams and learning areas."""

    def has_permission(self, request, view):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
            return bool(user and user.is_authenticated)
        return bool(user and user.is_authenticated and user.role in STAFF_ROLES)



class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'TEACHER'


class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'STUDENT'


class IsParent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'PARENT'


class IsStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['STAFF', 'ADMIN']


class IsDriver(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'DRIVER'
