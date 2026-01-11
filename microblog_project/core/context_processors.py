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
