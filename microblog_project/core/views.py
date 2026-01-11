from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Post
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from .models import Post, Follow
from django.shortcuts import redirect, get_object_or_404
from .models import Like
from .models import Comment
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import Post, Follow
from .forms import EditUserForm, ProfilePhotoForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .models import Profile
from django.conf import settings
import os
import logging
import time
from django.utils.text import get_valid_filename
from django.http import HttpResponseForbidden
from django.core.files.storage import default_storage
from django.templatetags.static import static

logger = logging.getLogger(__name__)



def home(request):
    if request.user.is_authenticated:
        # Users that the current user follows
        following_ids = Follow.objects.filter(
            follower=request.user
        ).values_list('following_id', flat=True)

        # Show posts from followed users + self
        posts = Post.objects.filter(
            user__in=list(following_ids) + [request.user.id]
        ).select_related('user').annotate(
            like_count=Count('like', distinct=True),
            comment_count=Count('comment', distinct=True)
        ).order_by('-created_at')

        # Limit people list to a reasonable number to improve render performance
        users = User.objects.exclude(id=request.user.id)[:20]

    else:
        posts = Post.objects.all().select_related('user').annotate(
            like_count=Count('like', distinct=True),
            comment_count=Count('comment', distinct=True)
        ).order_by('-created_at')
        users = []
        following_ids = []

    # Compute trending hashtags and top liked posts
    import re
    from collections import Counter

    # Limit the scope for computing trending hashtags to recent posts (reduces scanning all historical posts)
    all_posts = Post.objects.order_by('-created_at')[:500]
    hashtag_counter = Counter()
    for p in all_posts:
        tags = re.findall(r"#(\w+)", p.content)
        for t in tags:
            hashtag_counter[t.lower()] += 1

    top_hashtags = [h for h,c in hashtag_counter.most_common(8)]
    # Top liked posts
    top_posts = Post.objects.annotate(like_count=Count('like')).select_related('user').order_by('-like_count', '-created_at')[:5]

    context = {
        'posts': posts,
        'users': users,
        'following_ids': following_ids,
        'trending_hashtags': top_hashtags,
        'trending_posts': top_posts,
    }
    
    return render(request, 'home.html', context)
    liked_posts = []
    if request.user.is_authenticated:
      liked_posts = Like.objects.filter(
        user=request.user
      ).values_list('post_id', flat=True)


def profile(request, username):
    profile_user = get_object_or_404(User, username=username)

    posts = (
        Post.objects
        .filter(user=profile_user)
        .select_related('user')
        .annotate(
            like_count=Count('like', distinct=True),
            comment_count=Count('comment', distinct=True)
        )
        .order_by('-created_at')
    )

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
    }

    return render(request, 'core/profile.html', context)



def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.select_related('user').annotate(
        like_count=Count('like', distinct=True),
        comment_count=Count('comment', distinct=True)
    ), id=post_id)

    liked = False
    if request.user.is_authenticated:
        liked = Like.objects.filter(user=request.user, post=post).exists()

    comments = Comment.objects.filter(post=post).select_related('user').order_by('created_at')

    # compute trending hashtags and top posts for sidebar
    import re
    from collections import Counter
    all_posts = Post.objects.order_by('-created_at')[:500]
    hashtag_counter = Counter()
    for p in all_posts:
        tags = re.findall(r"#(\w+)", p.content)
        for t in tags:
            hashtag_counter[t.lower()] += 1
    top_hashtags = [h for h,c in hashtag_counter.most_common(8)]
    top_posts = Post.objects.annotate(like_count=Count('like')).order_by('-like_count', '-created_at')[:5]

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
        posts = Post.objects.annotate(like_count=Count('like')).order_by('-like_count', '-created_at')[:50]
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
    posts = posts.select_related('user').annotate(
        like_count=Count('like', distinct=True),
        comment_count=Count('comment', distinct=True)
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
    hashtag_counter = Counter()
    for p in all_posts:
        tags = re.findall(r"#(\w+)", p.content)
        for t in tags:
            hashtag_counter[t.lower()] += 1
    top_hashtags = [h for h,c in hashtag_counter.most_common(8)]
    top_posts = Post.objects.annotate(like_count=Count('like')).order_by('-like_count', '-created_at')[:5]

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

        user = User.objects.create_user(username=username, password=password)
        user.save()
        # Create profile for the new user
        Profile.objects.create(user=user)
        messages.success(request, 'Account created successfully')
        return redirect('login')

    return render(request, 'register.html')

   
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('login')

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def create_post(request):
    if request.method == 'POST':
        content = request.POST.get('content')

        if content.strip() != "":
            Post.objects.create(
                user=request.user,
                content=content
            )
        return redirect('home')

@login_required
def follow_user(request, user_id):
    user_to_follow = get_object_or_404(User, id=user_id)

    # Prevent user from following themselves
    if user_to_follow != request.user:
        Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )

    return redirect('home')
@login_required
def unfollow_user(request, user_id):
    user_to_unfollow = get_object_or_404(User, id=user_id)

    Follow.objects.filter(
        follower=request.user,
        following=user_to_unfollow
    ).delete()

    return redirect('home')

from .models import Like

@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    Like.objects.get_or_create(user=request.user, post=post)
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def unlike_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    Like.objects.filter(user=request.user, post=post).delete()
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        text = request.POST.get('comment')
        if text.strip():
            Comment.objects.create(
                user=request.user,
                post=post,
                text=text
            )

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

    # Only owner can delete
    if post.user != request.user:
        messages.error(request, "You don't have permission to delete this post")
        return redirect('home')

    # Delete only via POST to avoid accidental deletes
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted')
        return redirect('home')

    return render(request, 'confirm_delete.html', {'post': post})

@login_required
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        if 'save_profile' in request.POST:
            user_form = EditUserForm(request.POST, instance=request.user)
            profile_form = ProfilePhotoForm(
                request.POST, request.FILES, instance=profile
            )

            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                return redirect('profile', request.user.username)

        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
                return redirect('profile', request.user.username)
        else:
            password_form = PasswordChangeForm(user=request.user)
    else:
        user_form = EditUserForm(instance=request.user)
        profile_form = ProfilePhotoForm(instance=profile)
        password_form = PasswordChangeForm(user=request.user)

    return render(request, 'core/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'password_form': password_form,
    })

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
    user = get_object_or_404(User, username=username)

    followers = Follow.objects.filter(
        following=user
    ).select_related('follower')

    return render(request, 'core/followers.html', {
        'profile_user': user,
        'followers': followers
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


