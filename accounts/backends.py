from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(BaseBackend):
    """
    Custom authentication backend that allows users to log in using their email address.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to find user by email
            user = User.objects.get(email=username)
            if user.check_password(password) and user.is_active:
                return user
        except User.DoesNotExist:
            # Try to find user by username as fallback
            try:
                user = User.objects.get(username=username)
                if user.check_password(password) and user.is_active:
                    return user
            except User.DoesNotExist:
                pass
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None