from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    message = "Змінювати каталог може лише адміністратор."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        return request.user.is_staff
