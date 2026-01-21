from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

from .models import Post, Like, Follow, Comment
from .utils import calculate_engagement_score, analyze_post_quality

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Post)
def update_reputation_on_post(sender, instance, created, **kwargs):
    if not created:
        return

    user = instance.user
    profile = getattr(user, 'profile', None)
    if not profile:
        return

    engagement = calculate_engagement_score(user)
    ai = analyze_post_quality(instance.content) / 100.0

    # credit action points for creating a post
    try:
        profile.action_points = (profile.action_points or 0) + 2
        profile.save(update_fields=['action_points'])
    except Exception:
        logger.exception('Failed to increment action_points for post creation')

    logger.debug('Post created by %s — recalcing reputation (eng=%s ai=%s)', user.username, engagement, ai)
    profile.recalc_hybrid_reputation(engagement_score=engagement, ai_score=ai)


@receiver(post_save, sender=Like)
def update_reputation_on_like(sender, instance, created, **kwargs):
    if not created:
        return

    # actor: the user who liked (give a small action boost)
    actor = instance.user
    actor_profile = getattr(actor, 'profile', None)
    if actor_profile:
        try:
            actor_profile.action_points = (actor_profile.action_points or 0) + 1
            actor_profile.save(update_fields=['action_points'])
            a_eng = calculate_engagement_score(actor)
            logger.debug('User %s liked a post — recalcing actor reputation (eng=%s)', actor.username, a_eng)
            actor_profile.recalc_hybrid_reputation(engagement_score=a_eng)
        except Exception:
            logger.exception('Failed to update actor reputation on like')

    # recipient: owner of the post
    try:
        recipient_profile = instance.post.user.profile
        r_eng = calculate_engagement_score(recipient_profile.user)
        logger.debug('Post %s liked — recalcing recipient %s reputation (eng=%s)', instance.post.id, recipient_profile.user.username, r_eng)
        recipient_profile.recalc_hybrid_reputation(engagement_score=r_eng)
    except Exception:
        logger.exception('Failed to update recipient reputation on like')


@receiver(post_save, sender=Comment)
def update_reputation_on_comment(sender, instance, created, **kwargs):
    if not created:
        return

    # actor: commenter
    actor = instance.user
    actor_profile = getattr(actor, 'profile', None)
    if actor_profile:
        try:
            actor_profile.action_points = (actor_profile.action_points or 0) + 1
            actor_profile.save(update_fields=['action_points'])
            a_eng = calculate_engagement_score(actor)
            logger.debug('User %s commented — recalcing actor reputation (eng=%s)', actor.username, a_eng)
            actor_profile.recalc_hybrid_reputation(engagement_score=a_eng)
        except Exception:
            logger.exception('Failed to update actor reputation on comment')

    # recipient: post owner
    try:
        recipient_profile = instance.post.user.profile
        r_eng = calculate_engagement_score(recipient_profile.user)
        logger.debug('Post %s commented — recalcing recipient %s reputation (eng=%s)', instance.post.id, recipient_profile.user.username, r_eng)
        recipient_profile.recalc_hybrid_reputation(engagement_score=r_eng)
    except Exception:
        logger.exception('Failed to update recipient reputation on comment')


@receiver(post_save, sender=Follow)
def update_reputation_on_follow(sender, instance, created, **kwargs):
    if not created:
        return

    # actor: follower
    follower = instance.follower
    f_profile = getattr(follower, 'profile', None)
    if f_profile:
        try:
            f_profile.action_points = (f_profile.action_points or 0) + 1
            f_profile.save(update_fields=['action_points'])
            f_eng = calculate_engagement_score(follower)
            logger.debug('User %s followed someone — recalcing follower reputation (eng=%s)', follower.username, f_eng)
            f_profile.recalc_hybrid_reputation(engagement_score=f_eng)
        except Exception:
            logger.exception('Failed to update follower reputation on follow')

    # recipient: followed user
    try:
        recipient_profile = instance.following.profile
        r_eng = calculate_engagement_score(recipient_profile.user)
        logger.debug('User %s was followed — recalcing recipient %s reputation (eng=%s)', recipient_profile.user.username, recipient_profile.user.username, r_eng)
        recipient_profile.recalc_hybrid_reputation(engagement_score=r_eng)
    except Exception:
        logger.exception('Failed to update recipient reputation on follow')
