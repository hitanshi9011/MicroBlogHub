from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

# =========================
# FOLLOW
# =========================
class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='following',
        on_delete=models.CASCADE
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='followers',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'following'],
                name='unique_follow'
            )
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


# =========================
# POST
# =========================
class Post(models.Model):
    STATUS_CHOICES = (
        ("published", "Published"),
        ("draft", "Draft"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="published"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.status}"


# =========================
# LIKE
# =========================
class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user.username} likes post {self.post.id}"


# =========================
# COMMENT
# =========================
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    text = models.TextField()
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='replies',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} commented on post {self.post.id}"


class CommentLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(
        Comment,
        related_name="likes",
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('user', 'comment')

    def __str__(self):
        return f"{self.user.username} liked comment {self.comment.id}"


# =========================
# MESSAGE
# =========================
class Message(models.Model):
    sender = models.ForeignKey(
        User,
        related_name='sent_messages',
        on_delete=models.CASCADE
    )
    recipient = models.ForeignKey(
        User,
        related_name='received_messages',
        on_delete=models.CASCADE
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"From {self.sender.username} to {self.recipient.username}"


# =========================
# PROFILE
# =========================
# core/models.py

from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    LEVEL_CHOICES = (
        (0, "Beginner"),
        (1, "Intermediate"),
        (2, "Expert"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    photo = models.ImageField(
        upload_to="profile_photos/",
        default="profile_photos/default.png",
        blank=True,
        null=True
    )

    bio = models.TextField(max_length=160, blank=True, default="")

    ai_score = models.FloatField(default=0.0)
    engagement_score = models.IntegerField(default=0)
    reputation_score = models.FloatField(default=0.0)

    action_points = models.IntegerField(default=0)
    badge = models.CharField(max_length=50, default="")

    level = models.SmallIntegerField(
        choices=LEVEL_CHOICES,
        default=0
    )

    def __str__(self):
        return self.user.username

# =========================
# NOTIFICATION
# =========================
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('follow', 'Follow'),
        ('like', 'Like'),
        ('comment', 'Comment'),
    )

    sender = models.ForeignKey(
        User,
        related_name='sent_notifications',
        on_delete=models.CASCADE
    )
    recipient = models.ForeignKey(
        User,
        related_name='received_notifications',
        on_delete=models.CASCADE
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES
    )
    post = models.ForeignKey(
        Post,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username} → {self.recipient.username} ({self.notification_type})"

    def get_redirect_url(self):
        if self.notification_type in ['like', 'comment'] and self.post:
            return f"/posts/{self.post.id}/"
        if self.notification_type == 'follow':
            return f"/profile/{self.sender.username}/"
        return "#"


# =========================
# COMMUNITY
# =========================
class Community(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name='communities_created'
    )
    members = models.ManyToManyField(
        User,
        related_name='joined_communities',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CommunityPost(models.Model):
    community = models.ForeignKey(
        Community,
        related_name="posts",
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.community.name} - {self.user.username}"


class CommunityComment(models.Model):
    post = models.ForeignKey(
        CommunityPost,
        related_name="comments",
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} in {self.post.community.name}"


class CommunityPostLike(models.Model):
    post = models.ForeignKey(
        CommunityPost,
        related_name="likes",
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('post', 'user')
