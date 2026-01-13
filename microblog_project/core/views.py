from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.conf import settings
from django.core.files.storage import default_storage
from django.template.loader import render_to_string

import os
import logging
import re
from collections import Counter
from django.db import transaction, IntegrityError

from .models import (
    Post, Follow, Like, Comment, CommentLike,
    Message, Notification, Community, CommunityPost,
    CommunityComment, CommunityPostLike, Profile
)
from .forms import EditUserForm, ProfilePhotoForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

User = get_user_model()
logger = logging.getLogger(__name__)

def home(request):
    # =========================
    # TOGGLE COMMUNITY POSTS
    # =========================
    if request.GET.get('toggle_communities') is not None:
        current = request.session.get('include_communities', False)
        request.session['include_communities'] = not current
        return redirect('home')

    include_communities = request.session.get('include_communities', False)

    # =========================
    # DEFAULT CONTEXT
    # =========================
    posts = []
    users = []
    following_ids = []
    liked_posts = []
    liked_comments = []
    unread_notifications = []
    unread_notifications_count = 0

    # =========================
    # AUTHENTICATED USER LOGIC
    # =========================
    if request.user.is_authenticated:
        # Notifications
        unread_notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).order_by('-created_at')
        unread_notifications_count = unread_notifications.count()

        # Following
        following_ids = list(
            Follow.objects.filter(
                follower=request.user
            ).values_list('following_id', flat=True)
        )

        # Feed: followed users + self
        posts = Post.objects.filter(
            user__in=following_ids + [request.user.id],
            status='published'
        ).select_related('user').annotate(
            like_count=Count('likes', distinct=True),
            comment_count=Count('comments', distinct=True)
        ).order_by('-created_at')

        # People section
        users = User.objects.exclude(id=request.user.id)[:20]

        # Likes
        liked_posts = list(
            Like.objects.filter(user=request.user)
            .values_list('post_id', flat=True)
        )

        # Comment likes
        liked_comments = list(
            CommentLike.objects.filter(user=request.user)
            .values_list('comment_id', flat=True)
        )

    # =========================
    # GUEST USER LOGIC
    # =========================
    else:
        posts = Post.objects.filter(
            status='published'
        ).select_related('user').annotate(
            like_count=Count('likes', distinct=True),
            comment_count=Count('comments', distinct=True)
        ).order_by('-created_at')

    # =========================
    # TRENDING HASHTAGS
    # =========================
    recent_posts = Post.objects.filter(
        status='published'
    ).order_by('-created_at')[:500]

    hashtag_counter = Counter()
    for p in recent_posts:
        tags = re.findall(r"#(\w+)", p.content)
        for t in tags:
            hashtag_counter[t.lower()] += 1

    top_hashtags = [h for h, c in hashtag_counter.most_common(8)]

    # =========================
    # TRENDING POSTS
    # =========================
    trending_posts = Post.objects.filter(
        status='published'
    ).annotate(
        like_count=Count('likes')
    ).select_related('user').order_by(
        '-like_count', '-created_at'
    )[:5]

    # =========================
    # COMMUNITY POSTS (OPTIONAL)
    # =========================
    posts_list = list(posts)

    if include_communities:
        from .models import CommunityPost

        community_posts = CommunityPost.objects.select_related(
            'user', 'community'
        ).prefetch_related(
            'comments'
        ).order_by('-created_at')[:50]

        for cp in community_posts:
            cp.is_community = True
            cp.community_obj = cp.community
            cp.like_count = 0
            cp.comment_set = cp.comments

        for p in posts_list:
            p.is_community = False

        posts_list.extend(list(community_posts))
    else:
        for p in posts_list:
            p.is_community = False

    posts_list.sort(key=lambda x: x.created_at, reverse=True)

    # =========================
    # FINAL RENDER
    # =========================
    return render(request, 'home.html', {
        'posts': posts_list,
        'users': users,
        'following_ids': following_ids,
        'liked_posts': liked_posts,
        'liked_comments': liked_comments,
        'unread_notifications': unread_notifications,
        'unread_notifications_count': unread_notifications_count,
        'trending_hashtags': top_hashtags,
        'trending_posts': trending_posts,
        'include_communities': include_communities,
    })


@login_required
def profile(request, username):
    profile_user = get_object_or_404(User, username=username)

    posts = (
        Post.objects
        .filter(user=profile_user)
        .select_related('user')
        .annotate(
            like_count=Count('likes', distinct=True),
            comment_count=Count('comments', distinct=True)
        )
        .order_by('-created_at')
    )
    # Show drafts only to the profile owner
    if request.user == profile_user:
        posts_qs = Post.objects.filter(user=profile_user)
    else:
        posts_qs = Post.objects.filter(user=profile_user, status='published')

    posts = posts_qs.select_related('user').annotate(
        like_count=Count('likes', distinct=True),
        comment_count=Count('comments', distinct=True)
    ).order_by('-created_at')

    posts_count = posts.count()
    followers_count = Follow.objects.filter(following=profile_user).count()
    following_count = Follow.objects.filter(follower=profile_user).count()

    is_following = False
    if request.user.is_authenticated and request.user != profile_user:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=profile_user
        ).exists()

    profile, _ = Profile.objects.get_or_create(user=profile_user)

    # likes/comments context for template (used to show liked state)
    liked_posts = []
    liked_comments = []
    if request.user.is_authenticated:
        liked_posts = list(Like.objects.filter(user=request.user).values_list('post_id', flat=True))
        liked_comments = list(CommentLike.objects.filter(user=request.user).values_list('comment_id', flat=True))

    photo_url = None
    try:
        if profile.photo and getattr(profile.photo, 'name', None):
            if default_storage.exists(str(profile.photo.name)):
                photo_url = profile.photo.url
    except Exception:
        pass

    context = {
        'profile_user': profile_user,
        'profile': profile,
        'photo_url': photo_url,
        'posts': posts,
        'posts_count': posts_count,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_following': is_following,
        'liked_posts': liked_posts,
        'liked_comments': liked_comments,
    }

    return render(request, 'core/profile.html', context)


# =========================
# AUTH
# =========================

def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.select_related('user').annotate(
        like_count=Count('likes', distinct=True),
        comment_count=Count('comments', distinct=True)
    ), id=post_id)

    # Prevent others from viewing drafts
    if post.status == 'draft' and (not request.user.is_authenticated or request.user != post.user):
        return redirect('home')

    liked = False
    if request.user.is_authenticated:
        liked = Like.objects.filter(user=request.user, post=post).exists()

    comments = Comment.objects.filter(post=post).select_related('user').order_by('created_at')

    # compute trending hashtags and top posts for sidebar
    import re
    from collections import Counter
    all_posts = Post.objects.filter(status='published').order_by('-created_at')[:500]
    hashtag_counter = Counter()
    for p in all_posts:
        tags = re.findall(r"#(\w+)", p.content)
        for t in tags:
            hashtag_counter[t.lower()] += 1
    top_hashtags = [h for h,c in hashtag_counter.most_common(8)]
    top_posts = Post.objects.filter(status='published').annotate(like_count=Count('likes')).order_by('-like_count', '-created_at')[:5]

    context = {
        'post': post,
        'liked': liked,
        'comments': comments,
        'trending_hashtags': top_hashtags,
        'trending_posts': top_posts,
    }

    return render(request, 'post_detail.html', context)


def search(request):
    q = request.GET.get('q', '') or ''
    q = q.strip()

    posts = Post.objects.none()
    users = User.objects.none()
    match_type = 'none'

    if q == '':
        # empty query -> show nothing
        match_type = 'empty'
    elif q.lower() == 'trending' or q.lower() == '#trending':
        match_type = 'trending'
        # annotate with like counts and order by popularity
        posts = Post.objects.annotate(like_count=Count('likes')).order_by('-like_count', '-created_at')[:50]
    elif q.startswith('@'):
        match_type = 'user'
        username = q[1:]
        users = User.objects.filter(username__icontains=username)
        posts = Post.objects.filter(user__in=users).order_by('-created_at')
    elif q.startswith('#'):
        match_type = 'hashtag'
        tag = q[1:]
        posts = Post.objects.filter(content__icontains=f"#{tag}").order_by('-created_at')
    else:
        match_type = 'keyword'
        # split into words and search content and usernames
        words = [w for w in q.split() if w]
        if words:
            q_filter = Q()
            for w in words:
                q_filter |= Q(content__icontains=w)
                q_filter |= Q(user__username__icontains=w)
            posts = Post.objects.filter(q_filter).distinct().order_by('-created_at')
        users = User.objects.filter(username__icontains=q)

    # annotate and select_related for better performance (avoid N+1 queries in templates)
    # Only show published posts in search results
    posts = posts.filter(status='published').select_related('user').annotate(
        like_count=Count('likes', distinct=True),
        comment_count=Count('comments', distinct=True)
    )

    liked_posts = []
    if request.user.is_authenticated:
        liked_posts = Like.objects.filter(user=request.user).values_list('post_id', flat=True)

    # Attach extracted tags per post for template convenience
    import re
    from collections import Counter

    post_list = list(posts)
    for p in post_list:
        p.tags = re.findall(r"#(\w+)", p.content)

    # compute trending hashtags and top posts for sidebar
    all_posts = Post.objects.all()
    all_posts = Post.objects.filter(status='published')
    hashtag_counter = Counter()
    for p in all_posts:
        tags = re.findall(r"#(\w+)", p.content)
        for t in tags:
            hashtag_counter[t.lower()] += 1
    top_hashtags = [h for h,c in hashtag_counter.most_common(8)]
    top_posts = Post.objects.filter(status='published').annotate(like_count=Count('likes')).order_by('-like_count', '-created_at')[:5]

    context = {
        'posts': posts,
        'users': users,
        'query': q,
        'match_type': match_type,
        'liked_posts': liked_posts,
        'trending_hashtags': top_hashtags,
        'trending_posts': top_posts,
    }

    return render(request, 'search_results.html', context)


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


@login_required
def create_post(request):
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        action = request.POST.get("action", "publish")  # 👈 KEY LINE

        if not content:
            messages.error(request, "Post content cannot be empty")
            return redirect('home')

        status = "draft" if action == "draft" else "published"

        Post.objects.create(
            user=request.user,
            content=content,
            status=status
        )

        if status == "draft":
            messages.success(request, "Draft saved")
            return redirect("drafts")
        else:
            messages.success(request, "Post published")
            return redirect("home")

    return redirect("home")



# =========================
# PROFILE
# ========================


# =========================
# FOLLOW / UNFOLLOW
# =========================

from django.db import transaction, IntegrityError

@login_required
def follow_user(request, user_id):
    # Only allow POST
    if request.method != 'POST':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
        messages.error(request, 'Invalid request method')
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    target = get_object_or_404(User, id=user_id)

    if request.user == target:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': "You cannot follow yourself."}, status=400)
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

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # return JSON so frontend JS doesn't choke on redirects
        return JsonResponse({
            'status': 'ok',
            'created': created,
            'is_following': True,
            'message': f"You are now following @{target.username}." if created else f"You are already following @{target.username}.",
            'followers_count': Follow.objects.filter(following=target).count(),
        })

    if created:
        messages.success(request, f"You are now following @{target.username}.")
    else:
        messages.info(request, f"You are already following @{target.username}.")

    return redirect('profile', username=target.username)


@login_required
def unfollow_user(request, user_id):
    # Only allow POST for unfollow action
    if request.method != 'POST':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
        messages.error(request, 'Invalid method')
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    target = get_object_or_404(User, id=user_id)

    if request.user == target:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': "Invalid operation."}, status=400)
        messages.error(request, "Invalid operation.")
        return redirect('profile', username=target.username)

    deleted = Follow.objects.filter(
        follower=request.user,
        following=target
    ).delete()[0]

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'ok',
            'deleted': bool(deleted),
            'message': f"You unfollowed @{target.username}." if deleted else f"You were not following @{target.username}.",
            'followers_count': Follow.objects.filter(following=target).count(),
        })

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

    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if created and post.user != request.user:
        Notification.objects.create(
            sender=request.user,
            recipient=post.user,
            notification_type='like',
            post=post
        )
    # Prefer returning to referring page, fallback to home
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def unlike_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    Like.objects.filter(user=request.user, post=post).delete()
    return redirect(request.META.get('HTTP_REFERER', 'home'))

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

    # Redirect back to the page that submitted the comment (profile, post detail, home, etc.)
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



@login_required
def join_community(request, community_id):
    community = get_object_or_404(Community, id=community_id)
    if not community.members.filter(id=request.user.id).exists():
        community.members.add(request.user)
    return redirect('community_detail', community_id=community.id)

@login_required
def leave_community(request, community_id):
    community = get_object_or_404(Community, id=community_id)

    # Prevent creator from leaving own community
    if request.user == community.created_by:
        messages.error(request, "Community creator cannot leave.")
        return redirect('community_detail', community_id=community.id)

    community.members.remove(request.user)
    messages.success(request, "You left the community.")
    return redirect('community_detail', community_id=community.id)




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
    # show notifications received by the user
    notifications_qs = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    return render(request, 'core/notifications.html', {
        'notifications': notifications_qs
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
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Only owner can edit
    if post.user != request.user:
        messages.error(request, "You don't have permission to edit this post")
        return redirect('home')

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if not content:
            messages.error(request, 'Post content cannot be empty')
        else:
            post.content = content
            post.save()
            messages.success(request, 'Post updated')
            return redirect('home')

    context = {'post': post}
    return render(request, 'edit_post.html', context)


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Permission check
    if post.user != request.user:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': "You don't have permission to delete this post"}, status=403)
        messages.error(request, "You don't have permission to delete this post")
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    # Only accept POST to perform delete
    if request.method != 'POST':
        return render(request, 'confirm_delete.html', {'post': post})

    # Perform deletion
    try:
        post.delete()
    except Exception as exc:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Error deleting post'}, status=500)
        messages.error(request, 'Error deleting post')
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'message': 'Post deleted', 'post_id': post_id})

    messages.success(request, 'Post deleted')
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        if 'save_profile' in request.POST:
            user_form = EditUserForm(request.POST, instance=request.user)
            profile_form = ProfilePhotoForm(
                request.POST,
                request.FILES,
                instance=profile
            )

            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                return redirect('edit_profile')

        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
                return redirect('profile', request.user.username)

    else:
        user_form = EditUserForm(instance=request.user)
        profile_form = ProfilePhotoForm(instance=profile)
        password_form = PasswordChangeForm(user=request.user)

    return render(request, 'core/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'password_form': password_form,
        'profile': profile,
    })
    
    
@login_required
def drafts(request):
    drafts_qs = Post.objects.filter(user=request.user, status='draft').select_related('user').annotate(
        like_count=Count('likes', distinct=True),
        comment_count=Count('comments', distinct=True)
    ).order_by('-created_at')

    context = {'drafts': drafts_qs}
    return render(request, 'drafts.html', context)

@login_required
def publish_draft(request, post_id):
    # Prefer POST for publishing; support POST from non-idempotent flows
    if request.method != 'POST':
        messages.error(request, 'Invalid method')
        return redirect('drafts')

    post = get_object_or_404(Post, id=post_id)
    if post.user != request.user:
        messages.error(request, "You don't have permission to publish this draft")
        return redirect('drafts')

    post.status = 'published'
    post.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'message': 'Draft published', 'post_id': post.id})
    messages.success(request, 'Draft published')
    return redirect('home')

@login_required
def draft_action(request, post_id):
    """Handle inline edit/save/publish actions for drafts via POST.

    Expected POST fields: 'content' and 'action' where action is 'save' or 'publish'.
    """
    if request.method != 'POST':
        messages.error(request, 'Invalid method')
        return redirect('drafts')

    post = get_object_or_404(Post, id=post_id)
    if post.user != request.user:
        messages.error(request, "You don't have permission to modify this draft")
        return redirect('drafts')

    content = request.POST.get('content', '').strip()
    action = request.POST.get('action', 'save')

    if content == '':
        messages.error(request, 'Post content cannot be empty')
        return redirect('drafts')

    post.content = content
    if action == 'publish':
        post.status = 'published'
    else:
        post.status = 'draft'

    post.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        resp = {
            'status': 'ok',
            'message': 'Draft published' if action == 'publish' else 'Draft saved',
            'post_id': post.id,
            'content': post.content,
            'action': action,
        }
        return JsonResponse(resp)

    if action == 'publish':
        messages.success(request, 'Draft published')
        return redirect('home')
    else:
        messages.success(request, 'Draft saved')
        return redirect('drafts')   

@login_required
def edit_draft(request, post_id):
    """
    Render a page to edit a draft (GET) or update/publish it (POST).
    Returns JSON if requested via X-Requested-With header.
    """
    post = get_object_or_404(Post, id=post_id, status='draft')

    if post.user != request.user:
        messages.error(request, "You don't have permission to edit this draft")
        return redirect('drafts')

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        action = request.POST.get('action', 'save')

        if content == '':
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Post content cannot be empty'}, status=400)
            messages.error(request, 'Post content cannot be empty')
            return redirect('drafts')

        post.content = content
        if action == 'publish':
            post.status = 'published'
        else:
            post.status = 'draft'
        post.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'ok',
                'message': 'Draft published' if action == 'publish' else 'Draft saved',
                'post_id': post.id,
                'content': post.content,
                'action': action,
            })

        messages.success(request, 'Draft published' if action == 'publish' else 'Draft saved')
        return redirect('home' if action == 'publish' else 'drafts')

    return render(request, 'edit_draft.html', {'post': post})


@login_required
def delete_draft(request, post_id):
    """
    Delete a draft via POST. Returns JSON for AJAX requests.
    """
    post = get_object_or_404(Post, id=post_id, status='draft')

    if post.user != request.user:
        messages.error(request, "You don't have permission to delete this draft")
        return redirect('drafts')

    if request.method != 'POST':
        messages.error(request, 'Invalid method')
        return redirect('drafts')

    post.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'message': 'Draft deleted', 'post_id': post_id})

    messages.success(request, 'Draft deleted')
    return redirect('drafts')


@login_required
def delete_account(request):
    if request.method == "POST":
        user = request.user
        logout(request)
        user.delete()
        return redirect('login') 


@login_required
def list_profile_files(request):
    """Staff-only debug view: list files in MEDIA_ROOT/profile_photos/ with URLs."""
    if not request.user.is_staff:
        return HttpResponseForbidden("Forbidden")

    photos_dir = os.path.join(settings.MEDIA_ROOT, 'profile_photos')
    files = []
    if os.path.isdir(photos_dir):
        for fname in sorted(os.listdir(photos_dir)):
            if fname.startswith('.'):
                continue
            url = f"{settings.MEDIA_URL}profile_photos/{fname}"
            files.append({'name': fname, 'url': url})

    return render(request, 'debug/profile_files.html', {'files': files})



def followers_list(request, username):
    profile_user = get_object_or_404(User, username=username)

    # Support both related_name and legacy lookups:
    try:
        followers = profile_user.followers.all()
    except Exception:
        followers = Follow.objects.filter(following=profile_user).select_related('follower')

    return render(request, 'core/followers.html', {
        'profile_user': profile_user,
        'followers': followers,
    })



def following_list(request, username):
    user = get_object_or_404(User, username=username)

    following = Follow.objects.filter(
        follower=user
    ).select_related('following')

    return render(request, 'core/following.html', {
        'profile_user': user,
        'following': following
    })





def user_posts(request, username):
    profile_user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(user=profile_user)

    return render(request, 'core/user_posts.html', {
        'profile_user': profile_user,
        'posts': posts
    })


# --- Community views ---#
from .models import Community, CommunityPost, CommunityComment


def community_list(request):
    communities = Community.objects.order_by('-created_at')
    context = {'communities': communities}
    return render(request, 'community_list.html', context)

@login_required
def community_list(request):
    communities = Community.objects.order_by('-created_at')
    context = {'communities': communities}
    return render(request, 'community_list.html', context)

@login_required
def community_detail(request, community_id):
    community = get_object_or_404(Community, id=community_id)

    is_creator = community.created_by == request.user
    is_member = community.members.filter(id=request.user.id).exists()
    can_post = is_creator or is_member

    has_posted = CommunityPost.objects.filter(
        community=community,
        user=request.user
    ).exists()

    # ================= HANDLE POST REQUEST =================
    if request.method == "POST":

        if not can_post:
            return HttpResponseForbidden("You must join this community.")

        action = request.POST.get("action")

        # -------- CREATE POST --------
        if action == "post":
            content = request.POST.get("content", "").strip()

            if content:
                CommunityPost.objects.create(
                    community=community,
                    user=request.user,
                    content=content
                )

            return redirect("community_detail", community_id=community.id)

        # -------- CREATE COMMENT --------
        elif action == "comment":
            post_id = request.POST.get("post_id")
            text = request.POST.get("comment", "").strip()

            if post_id and text:
                post = get_object_or_404(
                    CommunityPost,
                    id=post_id,
                    community=community
                )

                CommunityComment.objects.create(
                    post=post,
                    user=request.user,
                    text=text
                )

                return redirect(f"/communities/{community.id}/#comments-{post_id}")



    # ================= FETCH POSTS =================
    posts = (
        community.posts
        .select_related("user")
        .prefetch_related("comments__user", "likes")
        .order_by("-created_at")
        if can_post else []
    )

    return render(request, "community_detail.html", {
        "community": community,
        "posts": posts,
        "can_post": can_post,
        "is_member": is_member,
        "is_creator": is_creator,
        "has_posted": has_posted,
    })

    # ================= FETCH POSTS =================
    posts = (
        community.posts
        .select_related("user")
        .prefetch_related("comments__user", "likes")
        .order_by("-created_at")
        if can_post else []
    )

    return render(request, "community_detail.html", {
        "community": community,
        "posts": posts,
        "can_post": can_post,
        "is_member": is_member,
        "is_creator": is_creator,
        "has_posted": has_posted,
    })



@login_required
def delete_community_post(request, community_id, post_id):
    community = get_object_or_404(Community, id=community_id)
    post = get_object_or_404(CommunityPost, id=post_id, community=community)

    if request.method != 'POST':
        messages.error(request, 'Invalid method')
        return redirect('community_detail', community_id=community.id)

    # Allow deletion by post author or community owner
    if request.user != post.user and request.user != community.created_by:
        messages.error(request, "You don't have permission to delete this post")
        return redirect('community_detail', community_id=community.id)

    post.delete()
    messages.success(request, 'Community post deleted')
    return redirect('community_detail', community_id=community.id)


@login_required
def delete_community_comment(request, community_id, comment_id):
    community = get_object_or_404(Community, id=community_id)
    comment = get_object_or_404(CommunityComment, id=comment_id, post__community=community)

    if request.method != 'POST':
        messages.error(request, 'Invalid method')
        return redirect('community_detail', community_id=community.id)

    # Allow deletion by comment author or community owner
    if request.user != comment.user and request.user != community.created_by:
        messages.error(request, "You don't have permission to delete this comment")
        return redirect('community_detail', community_id=community.id)

    comment.delete()
    messages.success(request, 'Comment deleted')
    return redirect('community_detail', community_id=community.id)





@login_required
def edit_community_post(request, community_id, post_id):
    community = get_object_or_404(Community, id=community_id)
    post = get_object_or_404(CommunityPost, id=post_id, community=community)

    # Only the post author can edit
    if request.user != post.user:
        messages.error(request, "You don't have permission to edit this post")
        return redirect('community_detail', community_id=community.id)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if not content:
            messages.error(request, 'Post content cannot be empty')
        else:
            post.content = content
            post.save()
            messages.success(request, 'Community post updated')
            return redirect('community_detail', community_id=community.id)

    context = {'community': community, 'post': post}
    return render(request, 'community_edit_post.html', context)


@login_required
def create_community(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, 'Community name is required')
            return redirect('community_list')

        # Enforce unique name (case-insensitive)
        if Community.objects.filter(name__iexact=name).exists():
            messages.error(request, 'A community with that name already exists')
            return redirect('community_list')

        Community.objects.create(name=name, description=description, created_by=request.user)
        messages.success(request, f'Community "{name}" created')
        return redirect('community_list')

    return render(request, 'community_create.html')


@login_required
def delete_community(request, community_id):
    """Allow the community owner to delete a community.

    GET: render a confirmation page.
    POST: perform delete and redirect to community list.
    """
    community = get_object_or_404(Community, id=community_id)

    # Only community creator can delete the community
    if request.user != community.created_by:
        messages.error(request, "You don't have permission to delete this community")
        return redirect('community_detail', community_id=community.id)

    if request.method == 'POST':
        community.delete()
        messages.success(request, 'Community deleted')
        return redirect('community_list')

    return render(request, 'confirm_delete_community.html', {'community': community})



@login_required
def toggle_community_like(request, post_id):
    post = get_object_or_404(CommunityPost, id=post_id)

    like, created = CommunityPostLike.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()

    return redirect('community_detail', community_id=post.community.id)


