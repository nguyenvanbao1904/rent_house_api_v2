from rest_framework import permissions
from app.models import Role

class AdminPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == Role.ADMIN

class ChuNhaTroPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == Role.CHU_NHA_TRO

class NguoiThueTroPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == Role.NGUOI_THUE_TRO

    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and request.user.role == Role.NGUOI_THUE_TRO and obj.user_id == request.user