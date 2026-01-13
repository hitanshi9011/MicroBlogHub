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
    return {
        'top_creators': Profile.objects.select_related('user')
            .only('user__username', 'photo', 'reputation_score', 'level')
            .order_by('-reputation_score')[:5]
    }
