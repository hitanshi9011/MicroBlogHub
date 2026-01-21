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
from .models import Notification

def notifications(request):
    if request.user.is_authenticated:
        return {
            'notifications': Notification.objects.filter(
                recipient=request.user
            ).order_by('-created_at')[:10],
            'unread_notifications_count': Notification.objects.filter(
                recipient=request.user,
                is_read=False
            ).count()
        }
    return {}
def notification_count(request):
    if request.user.is_authenticated:
        return {
            "unread_notifications_count": Notification.objects.filter(
                recipient=request.user,
                is_read=False
            ).count()
        }
    return {}


def top_creators(request):
    # select_related to avoid N+1 when accessing .user, limit to top 5
    data = {
        'top_creators': Profile.objects.select_related('user')
            .only('user__username', 'photo', 'reputation_score', 'level')
            .order_by('-reputation_score')[:5]
    }

    # Provide a quick lookup of which users the current user follows so templates
    # can render Follow/Unfollow without extra queries per-row.
    if request.user.is_authenticated:
        from .models import Follow
        try:
            data['following_ids'] = list(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
        except Exception:
            data['following_ids'] = []

    return data
