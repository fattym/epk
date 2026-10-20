from rest_framework import permissions


STAFF_ROLES = ('ADMIN', 'STAFF', 'TEACHER')


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ADMIN')


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


class IsAdminOrStaffOrReadOnly(permissions.BasePermission):
    """Read: any authenticated user.
    Write (create/update/delete): restricted to ADMIN or STAFF only.
    Excludes TEACHER from write access (for sensitive reference data)."""

    def has_permission(self, request, view):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
            return bool(user and user.is_authenticated)
        return bool(user and user.is_authenticated and user.role in ('ADMIN', 'STAFF'))


class IsAdminOrStaffOrReadOnlyOrOwner(permissions.BasePermission):
    """Read: any authenticated user (queryset filters by school/ownership).
    Write: restricted to ADMIN or STAFF.
    For object-level: allows access if user is admin/staff or owns the object."""

    def has_permission(self, request, view):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
            return bool(user and user.is_authenticated)
        return bool(user and user.is_authenticated and user.role in ('ADMIN', 'STAFF'))

    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
            if hasattr(obj, 'school'):
                return obj.school == user.school
            return True
        return bool(user and user.is_authenticated and user.role in ('ADMIN', 'STAFF'))



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


class IsParentOrAdminOrStaff(permissions.BasePermission):
    """Allows parents to create orders (shopping bag), admins/staff to manage."""

    def has_permission(self, request, view):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
            return bool(user and user.is_authenticated)
        return bool(user and user.is_authenticated and user.role in ('PARENT', 'ADMIN', 'STAFF'))
