from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Post
from django.contrib.auth.decorators import login_required
from .models import Post, Follow
from django.shortcuts import redirect, get_object_or_404
from .models import Like
from .models import Comment
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import Post, Follow

def home(request):
    if request.user.is_authenticated:
        # Users that the current user follows
        following_ids = Follow.objects.filter(
            follower=request.user
        ).values_list('following_id', flat=True)

        # Show posts from followed users + self
        posts = Post.objects.filter(
            user__in=list(following_ids) + [request.user.id]
        ).order_by('-created_at')

        users = User.objects.exclude(id=request.user.id)

    else:
        posts = Post.objects.all().order_by('-created_at')
        users = []
        following_ids = []

    context = {
        'posts': posts,
        'users': users,
        'following_ids': following_ids,
    }
    
    return render(request, 'home.html', context)
    liked_posts = []
    if request.user.is_authenticated:
      liked_posts = Like.objects.filter(
        user=request.user
      ).values_list('post_id', flat=True)


def profile(request, username):
    profile_user = get_object_or_404(User, username=username)

    posts = Post.objects.filter(user=profile_user).order_by('-created_at')

    followers_count = Follow.objects.filter(following=profile_user).count()
    following_count = Follow.objects.filter(follower=profile_user).count()

    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=profile_user
        ).exists()

    context = {
        'profile_user': profile_user,
        'posts': posts,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_following': is_following,
    }

    return render(request, 'core/profile.html', context)


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('register')

        user = User.objects.create_user(username=username, password=password)
        user.save()
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
    return redirect('home')

@login_required
def unlike_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    Like.objects.filter(user=request.user, post=post).delete()
    return redirect('home')

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

    return redirect('home')