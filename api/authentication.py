from rest_framework import authentication
from rest_framework import exceptions
from settings.models import system_settings

from rest_framework import permissions

def any_of(*perms):
    """
    工厂函数：返回一个新的 Permission 类，
    满足任意一个给定权限类即可通过。
    """
    class AnyOfPermission(permissions.BasePermission):
        def has_permission(self, request, view):
            return any(
                perm().has_permission(request, view)
                for perm in perms
            )

        def has_object_permission(self, request, view, obj):
            return any(
                perm().has_permission(request, view) and
                perm().has_object_permission(request, view, obj)
                for perm in perms
            )
    AnyOfPermission.__name__ = f"AnyOf({','.join(p.__name__ for p in perms)})"
    return AnyOfPermission

class APIKeyPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        access_key = request.GET.get("access_key", None)
        if not access_key:
            #raise exceptions.PermissionDenied("Access key not provided.")
            return False
        try:
            system_settings.objects.get(access_key=access_key)
            return True
        except system_settings.DoesNotExist:
            return False
            #raise exceptions.PermissionDenied("No found the access key or API is disabled")
        except ValueError:
            return False
            raise exceptions.PermissionDenied("Badly formed hexadecimal UUID string")


class IsAdminPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            if not request.user.is_authenticated:
                #raise exceptions.AuthenticationFailed("AuthFailed")
                return False
            if not request.user.groups.filter(name='Admin').exists():
                #raise exceptions.PermissionDenied("PermissionDeny")
                return False
            
            return True
        except:
            #raise exceptions.PermissionDenied("PermissionDeny")
            return False

            


