from .models import Profile


def current_profile(request):
    """Add `profile` to template context for authenticated users.
    Returns {'profile': Profile instance or None}.
    """
    if request.user.is_authenticated:
        try:
            profile, _ = Profile.objects.get_or_create(user=request.user)
            return {'profile': profile}
        except Exception:
            return {'profile': None}
    return {'profile': None}
