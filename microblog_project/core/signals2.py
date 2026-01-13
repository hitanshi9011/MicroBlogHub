# core/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Post, Profile
from .utils import analyze_post_quality, calculate_engagement_score


@receiver(post_save, sender=Post)
def update_reputation(sender, instance, created, **kwargs):
    # Only run when a NEW post is created
    if not created:
        return

    try:
        profile = Profile.objects.get(user=instance.user)

        # ---------- AI SCORE ----------
        recent_posts = (
            Post.objects
            .filter(user=instance.user)
            .order_by("-created_at")[:5]
        )

        if recent_posts:
            ai_scores = [analyze_post_quality(p.content) for p in recent_posts]
            profile.ai_score = sum(ai_scores) / len(ai_scores)
        else:
            profile.ai_score = 0.0

        # ---------- ENGAGEMENT SCORE ----------
        profile.engagement_score = calculate_engagement_score(instance.user)

        # ---------- REPUTATION ----------
        profile.reputation_score = (
            0.6 * profile.ai_score +
            0.4 * profile.engagement_score
        )

        # ---------- LEVEL (INTEGER ONLY) ----------
        if profile.reputation_score < 30:
            profile.level = 0   # Beginner
        elif profile.reputation_score < 70:
            profile.level = 1   # Intermediate
        else:
            profile.level = 2   # Expert

        profile.save()

    except Profile.DoesNotExist:
        # Safety fallback
        Profile.objects.create(
            user=instance.user,
            ai_score=0.0,
            engagement_score=0,
            reputation_score=0.0,
            level=0
        )

    except Exception as e:
        # Never break post creation
        print("Reputation update skipped:", e)
