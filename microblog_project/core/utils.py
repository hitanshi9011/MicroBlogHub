def analyze_post_quality(text):
    score = 0

    if len(text) > 30:
        score += 20
    if len(text.split()) > 10:
        score += 20
    if "http" not in text.lower():
        score += 20
    if text.count("!") < 5:
        score += 20

    score += 20  # base score

    return min(score, 100)

import math
from .models import Follow, Post, Like, Comment, Profile


def calculate_engagement_score(user):
    followers_count = Follow.objects.filter(following=user).count()

    posts = Post.objects.filter(user=user)
    likes = Like.objects.filter(post__in=posts).count()
    comments = Comment.objects.filter(post__in=posts).count()

    return (
        math.log1p(followers_count) * 30 +
        math.log1p(likes) * 40 +
        math.log1p(comments) * 30
    )


def assign_level(score):
    if score >= 100:
        return "Elite Creator"
    elif score >= 60:
        return "Top Creator"
    elif score >= 30:
        return "Influencer"
    elif score >= 10:
        return "Rising Creator"
    else:
        return "Beginner"
