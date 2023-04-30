from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAllowOrAuthorOrAuthorized(BasePermission):

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or (request.user.is_authenticated
                                                  and request.user == obj.author)
