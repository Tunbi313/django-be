# api/permissions.py

from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdmin(BasePermission):
    """
    Cho phép chỉ admin (is_admin=True) mới có quyền truy cập
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff

class IsAdminOrReadOnly(BasePermission):
    """
    Cho phép admin thực hiện tất cả các thao tác
    Cho phép user thường chỉ đọc (GET)
    """
    def has_permission(self, request, view):
        # Cho phép tất cả các request GET
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Cho các method khác (POST, PUT, DELETE), chỉ admin mới được phép
        return request.user.is_authenticated and request.user.is_staff
