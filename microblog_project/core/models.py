from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

AUTH_USER = settings.AUTH_USER_MODEL
User = get_user_model()


class Follow(models.Model):
    follower = models.ForeignKey(AUTH_USER, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(AUTH_USER, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['follower', 'following'], name='unique_follow')
        ]

    def __str__(self):
        return f"{self.follower} -> {self.following}"


class Post(models.Model):
    STATUS_CHOICES = (("published", "Published"), ("draft", "Draft"))

    user = models.ForeignKey(AUTH_USER, on_delete=models.CASCADE)
    content = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="published")
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.status}"


class Like(models.Model):
    user = models.ForeignKey(AUTH_USER, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user.username} likes post {self.post.id}"


class Comment(models.Model):
    user = models.ForeignKey(AUTH_USER, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} commented on post {self.post.id}"


class CommentLike(models.Model):
    user = models.ForeignKey(AUTH_USER, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, related_name='likes', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'comment')

    def __str__(self):
        return f"{self.user.username} liked comment {self.comment.id}"


class Message(models.Model):
    sender = models.ForeignKey(AUTH_USER, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(AUTH_USER, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"From {self.sender.username} to {self.recipient.username}"


class Profile(models.Model):
    user = models.OneToOneField(AUTH_USER, related_name='profile', on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='profile_photos/', default='profile_photos/default.png', blank=True, null=True)
    bio = models.TextField(max_length=160, blank=True, default='')

    action_points = models.IntegerField(default=0)

    ai_score = models.FloatField(default=0.0)
    engagement_score = models.FloatField(default=0.0)
    reputation_score = models.FloatField(default=0.0)
    score = models.PositiveSmallIntegerField(default=0)
    level = models.PositiveSmallIntegerField(default=1)
    badge = models.CharField(max_length=32, default='Novice')
    last_recalc = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username

    def _badge_from_level(self, lvl: int) -> str:
        if lvl >= 9:
            return 'Elite'
        if lvl >= 7:
            return 'Star'
        if lvl >= 5:
            return 'Influencer'
        if lvl >= 3:
            return 'Contributor'
        return 'Novice'

    def recalc_hybrid_reputation(self, ai_score=None, engagement_score=None, save=True):
        if ai_score is not None:
            self.ai_score = float(ai_score)
        if engagement_score is not None:
            self.engagement_score = float(engagement_score)

        # weights: engagement 70% / ai 30%
        self.reputation_score = float((self.engagement_score * 0.7) + (self.ai_score * 0.3))
        self.score = int(round(self.reputation_score * 100))
        self.level = max(1, min(10, 1 + int(self.reputation_score * 9)))
        self.badge = self._badge_from_level(self.level)

        if save:
            self.last_recalc = timezone.now()
            try:
                self.save(update_fields=[
                    'ai_score', 'engagement_score', 'reputation_score',
                    'score', 'level', 'badge', 'last_recalc', 'action_points'
                ])
            except Exception:
                self.save()

    @property
    def photo_url(self):
        try:
            return self.photo.url if self.photo else '/static/images/default.png'
        except Exception:
            return '/static/images/default.png'

    # --- Badge / Level helpers (computed properties; do NOT modify DB) ---
    def _compute_badge_and_icon(self):
        """
        Compute badge name and emoji icon based on reputation_score.
        Keep logic in Python (no DB writes) to avoid migrations and to keep values derived.
        """
        r = float(self.reputation_score or 0)
        if r >= 250:
            return "Legend", "🏆"
        if r >= 100:
            return "Elite Creator", "💎"
        if r >= 50:
            return "Rising Star", "🌟"
        if r >= 20:
            return "Contributor", "✨"
        return "Novice", "🏅"

    @property
    def badge_name(self):
        """Human-readable badge label derived from reputation_score."""
        return self._compute_badge_and_icon()[0]

    @property
    def badge_icon(self):
        """Emoji/SVG icon for the badge derived from reputation_score."""
        return self._compute_badge_and_icon()[1]

    @property
    def level_label(self):
        """
        Map numeric level to readable label.
        Keep numeric level in DB, but render friendly labels here.
        """
        lvl = int(self.level or 1)
        if lvl >= 8:
            return "Expert"
        if lvl >= 5:
            return "Advanced"
        if lvl >= 3:
            return "Intermediate"
        return "Beginner"


class Notification(models.Model):
    NOTIFICATION_TYPES = (('follow', 'Follow'), ('like', 'Like'), ('comment', 'Comment'))

    sender = models.ForeignKey(AUTH_USER, related_name='sent_notifications', on_delete=models.CASCADE)
    recipient = models.ForeignKey(AUTH_USER, related_name='received_notifications', on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    post = models.ForeignKey(Post, null=True, blank=True, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.sender} → {self.recipient} ({self.notification_type})"

    def get_redirect_url(self):
        if self.notification_type in ["like", "comment"] and self.post:
            return f"/posts/{self.post.id}/"
        if self.notification_type == "follow":
            return f"/profile/{self.sender.username}/"
        return "#"


class Community(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(AUTH_USER, related_name='communities_created', null=True, on_delete=models.SET_NULL)
    members = models.ManyToManyField(AUTH_USER, related_name='communities', blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class CommunityPost(models.Model):
    community = models.ForeignKey(Community, related_name='posts', on_delete=models.CASCADE)
    user = models.ForeignKey(AUTH_USER, on_delete=models.CASCADE)
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.community.name}: {self.user.username} - {self.content[:30]}"


class CommunityComment(models.Model):
    post = models.ForeignKey(CommunityPost, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(AUTH_USER, on_delete=models.CASCADE)
    text = models.TextField(max_length=500)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} on {self.post.id} in {self.post.community.name}"


class CommunityPostLike(models.Model):
    user = models.ForeignKey(AUTH_USER, on_delete=models.CASCADE)
    post = models.ForeignKey(CommunityPost, related_name='likes', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user.username} likes community post {self.post.id}"


@receiver(post_save, sender=User)
def create_profile_for_user(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_profile_for_user(sender, instance, **kwargs):
    try:
        if hasattr(instance, 'profile'):
            instance.profile.save()
    except Exception:
        # don't raise during migrations/startup
        pass


