from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Post, Profile
from .utils import analyze_post_quality, calculate_engagement_score, assign_level


@receiver(post_save, sender=Post)
def update_reputation(sender, instance, created, **kwargs):
    # ✅ Only update on NEW post creation
    if not created:
        return

    try:
        profile = instance.user.profile

        # ---------- AI SCORE ----------
        recent_posts = (
            Post.objects
            .filter(user=instance.user)
            .order_by('-created_at')[:5]
        )

        if recent_posts.exists():
            ai_scores = [analyze_post_quality(p.content) for p in recent_posts]
            profile.ai_score = sum(ai_scores) / len(ai_scores)
        else:
            profile.ai_score = 0

        # ---------- ENGAGEMENT SCORE ----------
        profile.engagement_score = calculate_engagement_score(instance.user)

        # ---------- HYBRID REPUTATION ----------
        profile.reputation_score = (
            0.6 * profile.ai_score +
            0.4 * profile.engagement_score
        )

        # ---------- LEVEL (STRING) ----------
        profile.level = assign_level(profile.reputation_score)

        profile.save()

    except Exception as e:
        # ✅ NEVER break post/draft creation
        print("Reputation update skipped:", e)
