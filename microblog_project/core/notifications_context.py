from .models import Notification

def unread_notifications(request):
    """
    Context processor: inject unread notifications and count into templates.
    Keeps the original model field name 'recepient' to match your models.
    """
    if request.user.is_authenticated:
        unread = Notification.objects.filter(
            recepient=request.user,
            is_read=False
        )
        return {
            'unread_notifications': unread,
            'unread_notifications_count': unread.count(),
        }

    return {
        'unread_notifications': [],
        'unread_notifications_count': 0,
    }
