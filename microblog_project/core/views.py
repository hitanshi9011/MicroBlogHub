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
from .models import Message
from django.db.models import Q
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import Post, Follow
from .models import Post, Follow, Like, Comment, Profile, Notification
from .models import Notification



def home(request):
    if request.user.is_authenticated:
        unread_notifications_count = Notification.objects.filter(
            receiver=request.user,
            is_read=False
        ).count()
    else:
        unread_notifications_count = 0

    return render(request, 'home.html', {
        'unread_notifications_count': unread_notifications_count,
    })



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
    if request.method == "POST":
        content = request.POST.get("content")

        if content and content.strip():
            Post.objects.create(
                user=request.user,
                content=content,
                status="published"   # IMPORTANT (fixes your earlier error)
            )

    return redirect("home")

@login_required
def follow_user(request, user_id):
    user_to_follow = get_object_or_404(User, id=user_id)

    if user_to_follow != request.user:
        Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )

        Notification.objects.create(
            sender=request.user,
            receiver=user_to_follow,
            notification_type='follow'
        )

    return redirect('profile', username=user_to_follow.username)

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

    Like.objects.get_or_create(
        user=request.user,
        post=post
    )

    if post.user != request.user:
        Notification.objects.create(
            sender=request.user,
            receiver=post.user,
            notification_type='like',
            post=post
        )

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

            if post.user != request.user:
                Notification.objects.create(
                    sender=request.user,
                    receiver=post.user,
                    notification_type='comment',
                    post=post
                )

    return redirect('home')


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Only allow the comment owner to delete their comment
    if comment.user == request.user:
        comment.delete()
        messages.success(request, 'Comment deleted successfully.')
    else:
        messages.error(request, 'You can only delete your own comments.')
    
    return redirect('home')

@login_required
def messages_list(request):
    # Get all unique users the current user has messaged with
    sent_to = Message.objects.filter(sender=request.user).values_list('recipient', flat=True).distinct()
    received_from = Message.objects.filter(recipient=request.user).values_list('sender', flat=True).distinct()
    all_users = User.objects.filter(Q(id__in=sent_to) | Q(id__in=received_from)).exclude(id=request.user.id)
    
    # Get last message for each conversation
    conversations = []
    for user in all_users:
        last_message = Message.objects.filter(
            Q(sender=request.user, recipient=user) | Q(sender=user, recipient=request.user)
        ).order_by('-created_at').first()
        
        unread_count = Message.objects.filter(
            sender=user, recipient=request.user, is_read=False
        ).count()
        
        conversations.append({
            'user': user,
            'last_message': last_message,
            'unread_count': unread_count
        })
    
    # Sort by last message time
    conversations.sort(key=lambda x: x['last_message'].created_at if x['last_message'] else x['user'].date_joined, reverse=True)
    
    context = {
        'conversations': conversations,
    }
    return render(request, 'core/messages.html', context)

@login_required
def conversation(request, username):
    other_user = get_object_or_404(User, username=username)
    
    # Mark messages as read
    Message.objects.filter(sender=other_user, recipient=request.user, is_read=False).update(is_read=True)
    
    # Get all messages between current user and other user
    messages_list = Message.objects.filter(
        Q(sender=request.user, recipient=other_user) | Q(sender=other_user, recipient=request.user)
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
    
    context = {
        'other_user': other_user,
        'messages': messages_list,
    }
    return render(request, 'core/conversation.html', context)

@login_required
def send_message(request, username):
    recipient = get_object_or_404(User, username=username)
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content
            )
            messages.success(request, 'Message sent successfully!')
            return redirect('conversation', username=username)
        else:
            messages.error(request, 'Message cannot be empty.')
    
    return redirect('conversation', username=username)

@login_required
def notifications(request):
    # 1️⃣ Get unread notifications (NOT sliced)
    unread_qs = Notification.objects.filter(
        receiver=request.user,
        is_read=False
    )

    # 2️⃣ Mark them as read
    unread_qs.update(is_read=True)

    # 3️⃣ Fetch latest notifications for display
    notifications = Notification.objects.filter(
        receiver=request.user
    ).order_by('-created_at')[:10]

    return render(request, 'core/notifications.html', {
        'notifications': notifications
    })
