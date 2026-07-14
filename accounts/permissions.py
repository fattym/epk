from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.role == 'ADMIN'


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
