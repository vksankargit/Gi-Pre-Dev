from .models import User


def get_effective_user(request):
    """
    Get the effective user for the current request.
    If the user is impersonating another user, return the impersonated user.
    Otherwise, return the original user.
    """
    if 'impersonated_user_id' in request.session:
        try:
            impersonated_user_id = request.session['impersonated_user_id']
            return User.objects.get(id=impersonated_user_id)
        except User.DoesNotExist:
            # If impersonated user no longer exists, clear the session
            if 'impersonated_user_id' in request.session:
                del request.session['impersonated_user_id']
            if 'original_user_id' in request.session:
                del request.session['original_user_id']
            return request.user

    return request.user


def is_impersonating(request):
    """
    Check if the current request is impersonating another user.
    """
    return 'impersonated_user_id' in request.session


def get_original_user(request):
    """
    Get the original user (coordinator) when impersonating.
    Returns None if not impersonating.
    """
    if is_impersonating(request):
        try:
            original_user_id = request.session.get('original_user_id')
            if original_user_id:
                return User.objects.get(id=original_user_id)
        except User.DoesNotExist:
            pass
    return None