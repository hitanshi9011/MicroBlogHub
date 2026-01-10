from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Like, Comment, Follow, Notification

# ======================
# LIKE NOTIFICATION
# ======================
@receiver(post_save, sender=Like)
def create_like_notification(sender, instance, created, **kwargs):
    if not created:
        return

    post = instance.post
    recipient = post.user

    if instance.user != recipient:
        Notification.objects.create(
            recipient=recipient,
            sender=instance.user,
            notification_type='like',
            post=post
        )


# ======================
# COMMENT NOTIFICATION
# ======================
@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if not created:
        return

    post = instance.post
    recipient = post.user

    if instance.user != recipient:
        Notification.objects.create(
            recipient=recipient,
            sender=instance.user,
            notification_type='comment',
            post=post
        )


# ======================
# FOLLOW NOTIFICATION
# ======================
@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.follower == instance.following:
        return

    Notification.objects.create(
        sender=instance.follower,
        recipient=instance.following,
        notification_type='follow'
    )
