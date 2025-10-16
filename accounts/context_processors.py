"""
Context processors for the accounts app.
"""
from .utils import get_effective_user, is_impersonating
from .models import User


def impersonation_context(request):
    """
    Add impersonation context to all templates.
    """
    context = {
        'is_impersonating': False,
        'impersonated_user': None,
        'original_user': None,
    }

    if hasattr(request, 'user') and request.user.is_authenticated:
        if is_impersonating(request):
            context['is_impersonating'] = True
            context['impersonated_user'] = get_effective_user(request)

            # Get original user
            original_user_id = request.session.get('original_user_id')
            if original_user_id:
                try:
                    context['original_user'] = User.objects.get(id=original_user_id)
                except User.DoesNotExist:
                    pass

    return context