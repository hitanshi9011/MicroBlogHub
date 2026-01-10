from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.db import IntegrityError, transaction
from django.contrib.auth import get_user_model
from .models import Notification
from django.template.loader import render_to_string
from .models import CommentLike

from .models import (
    Post,
    Follow,
    Like,
    Comment,
    Message,
    Notification,
)

User = get_user_model()

# =========================
# AUTH
# =========================

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('register')

        User.objects.create_user(username=username, password=password)
        messages.success(request, 'Account created successfully')
        return redirect('login')

    return render(request, 'register.html')


def login_view(request):
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user:
            login(request, user)
            return redirect('home')

        messages.error(request, 'Invalid credentials')
        return redirect('login')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# =========================
# HOME
# =========================
from core.models import Notification, Post

from core.models import Notification, Post


def home(request):
    posts = Post.objects.all().order_by('-created_at')

    unread_notifications = []
    unread_notifications_count = 0
    users = []
    following_ids = []
    liked_posts = []

    if request.user.is_authenticated:
        # Notifications
        unread_notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).order_by('-created_at')
        unread_notifications_count = unread_notifications.count()

        # People section
        following_ids = list(
            Follow.objects.filter(
                follower=request.user
            ).values_list('following_id', flat=True)
        )

        users = User.objects.exclude(id=request.user.id)[:20]

        # Likes
        liked_posts = list(
            Like.objects.filter(
                user=request.user
            ).values_list('post_id', flat=True)
        )
        liked_comments = []

        if request.user.is_authenticated:liked_comments = list(
        CommentLike.objects.filter(user=request.user)
        .values_list('comment_id', flat=True)
    )


    return render(request, 'home.html', {
    'posts': posts,
    'users': users,
    'following_ids': following_ids,
    'liked_posts': liked_posts,
    'liked_comments': liked_comments,   # ✅ ADD THIS
    'unread_notifications': unread_notifications,
    'unread_notifications_count': unread_notifications_count,
})




@login_required
def create_post(request):
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            Post.objects.create(
                user=request.user,
                content=content,
                status="published"
            )
    return redirect('home')


# =========================
# PROFILE
# =========================

@login_required
def profile(request, username):
    profile_user = get_object_or_404(User, username=username)

    posts = Post.objects.filter(user=profile_user).order_by('-created_at')

    followers_count = Follow.objects.filter(following=profile_user).count()
    following_count = Follow.objects.filter(follower=profile_user).count()

    is_following = Follow.objects.filter(
        follower=request.user,
        following=profile_user
    ).exists()

    return render(request, 'core/profile.html', {
        'profile_user': profile_user,
        'posts': posts,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_following': is_following,
    })


# =========================
# FOLLOW / UNFOLLOW
# =========================

@login_required
def follow_user(request, user_id):
    target = get_object_or_404(User, id=user_id)

    if request.user == target:
        messages.error(request, "You cannot follow yourself.")
        return redirect('profile', username=target.username)

    try:
        with transaction.atomic():
            follow_obj, created = Follow.objects.get_or_create(
                follower=request.user,
                following=target
            )
    except IntegrityError:
        follow_obj = Follow.objects.filter(
            follower=request.user,
            following=target
        ).first()
        created = bool(follow_obj)

    if created:
        Notification.objects.create(
            sender=request.user,
            recipient=target,
            notification_type='follow'
        )
        messages.success(request, f"You are now following @{target.username}.")
    else:
        messages.info(request, f"You are already following @{target.username}.")

    return redirect('profile', username=target.username)

@login_required
def unfollow_user(request, user_id):
    target = get_object_or_404(User, id=user_id)
    if request.user == target:
        messages.error(request, "Invalid operation.")
        return redirect('profile', username=target.username)

    deleted, _ = Follow.objects.filter(follower=request.user, following=target).delete()
    if deleted:
        messages.success(request, f"You unfollowed @{target.username}.")
    else:
        messages.info(request, f"You were not following @{target.username}.")
    return redirect('profile', username=target.username)


# =========================
# LIKE / UNLIKE
# =========================

@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    Like.objects.get_or_create(
        user=request.user,
        post=post
    )

    if post.user != request.user:
       Notification.objects.create(
    sender=request.user,
    recipient=post.user,
    notification_type='like',
    post=post
)


    return redirect('home')


@login_required
def unlike_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    Like.objects.filter(recipient=request.user, post=post).delete()
    return redirect('home')


# =========================
# COMMENTS
# =========================

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        text = request.POST.get('comment')

        if text and text.strip():
            Comment.objects.create(
                user=request.user,
                post=post,
                text=text
            )

            if post.user != request.user:
                Notification.objects.create(
    sender=request.user,
    recipient=post.user,
    notification_type='comment',
    post=post
)


    return redirect('home')


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.user == request.user:
        comment.delete()
        messages.success(request, 'Comment deleted')
    else:
        messages.error(request, 'Not allowed')

    return redirect('home')


from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if request.user != comment.user:
        return redirect('home')

    if request.method == "POST":
        new_text = request.POST.get("text")
        if new_text:
            comment.text = new_text
            comment.save()

    return redirect('home')

@login_required
def reply_comment(request, comment_id):
    parent_comment = get_object_or_404(Comment, id=comment_id)

    if request.method == "POST":
        text = request.POST.get("text")
        if text:
            Comment.objects.create(
                user=request.user,
                post=parent_comment.post,
                text=text,
                parent=parent_comment
            )

    return redirect('home')

@login_required
def toggle_comment_like(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    like, created = CommentLike.objects.get_or_create(
        user=request.user,
        comment=comment
    )

    if not created:
        like.delete()

    return redirect(request.META.get("HTTP_REFERER", "/"))





# =========================
# NOTIFICATIONS
# =========================

@login_required

def notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/notifications.html', {
        'notifications': notifications
    })



@login_required
def mark_notifications_read(request):
    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)

    return JsonResponse({"status": "ok"})

# =========================
# MESSAGES
# =========================

@login_required
def messages_list(request):
    sent_to = Message.objects.filter(sender=request.user).values_list('recipient', flat=True)
    received_from = Message.objects.filter(recipient=request.user).values_list('sender', flat=True)

    users = User.objects.filter(
        Q(id__in=sent_to) | Q(id__in=received_from)
    ).exclude(id=request.user.id)

    conversations = []
    for user in users:
        last_message = Message.objects.filter(
            Q(sender=request.user, recipient=user) |
            Q(sender=user, recipient=request.user)
        ).order_by('-created_at').first()

        unread_count = Message.objects.filter(
            sender=user,
            recipient=request.user,
            is_read=False
        ).count()

        conversations.append({
            'user': user,
            'last_message': last_message,
            'unread_count': unread_count
        })

    conversations.sort(
        key=lambda x: x['last_message'].created_at if x['last_message'] else x['user'].date_joined,
        reverse=True
    )

    return render(request, 'core/messages.html', {
        'conversations': conversations
    })


@login_required
def conversation(request, username):
    other_user = get_object_or_404(User, username=username)

    Message.objects.filter(
        sender=other_user,
        recipient=request.user,
        is_read=False
    ).update(is_read=True)

    messages_list = Message.objects.filter(
        Q(sender=request.user, recipient=other_user) |
        Q(sender=other_user, recipient=request.user)
    ).order_by('created_at')

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                sender=request.user,
                recipient=other_user,
                content=content
            )
            return redirect('conversation', username=username)

    return render(request, 'core/conversation.html', {
        'other_user': other_user,
        'messages': messages_list
    })


from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.http import JsonResponse
from core.models import Notification

@login_required
def notification_dropdown(request):
    all_notifications = Notification.objects.filter(
        recipient=request.user
    )

    unread_count = all_notifications.filter(is_read=False).count()

    notifications = all_notifications.order_by('-created_at')[:5]

    html = render_to_string(
        "notifications/dropdown.html",
        {"notifications": notifications},
        request=request
    )

    return JsonResponse({
        "html": html,
        "count": unread_count
    })
from django.shortcuts import get_object_or_404, redirect

@login_required
def notification_redirect(request, id):
    notification = get_object_or_404(
        Notification,
        id=id,
        recipient=request.user
    )

    notification.is_read = True
    notification.save()

    return redirect(notification.get_redirect_url())







