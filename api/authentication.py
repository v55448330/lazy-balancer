from rest_framework import authentication
from rest_framework import exceptions
from settings.models import system_settings

from rest_framework import permissions

class APIKeyPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        access_key = request.GET.get("access_key", None)
        if not access_key:
            raise exceptions.PermissionDenied("Access key not provided.")
        try:
            system_settings.objects.get(access_key=access_key)
            return True
        except system_settings.DoesNotExist:
            raise exceptions.PermissionDenied("No found the access key or API is disabled")
        except ValueError:
            raise exceptions.PermissionDenied("Badly formed hexadecimal UUID string")

        return False

class IsAdminPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            if not request.user.is_authenticated:
                raise exceptions.AuthenticationFailed("AuthFailed")
            if not request.user.groups.filter(name='Admin').exists():
                raise exceptions.PermissionDenied("PermissionDeny")
            
            print('bcd')

            return True
        except:
            raise exceptions.PermissionDenied("PermissionDeny")

            


