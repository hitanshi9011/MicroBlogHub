from django.shortcuts import render, redirect
from django.http import JsonResponse
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


def home(request):
    # Toggle include_communities session flag when requested
    if request.GET.get('toggle_communities') is not None:
        current = request.session.get('include_communities', False)
        request.session['include_communities'] = not current
        return redirect('home')

    include_communities = request.session.get('include_communities', False)

    if request.user.is_authenticated:
        # Users that the current user follows
        following_ids = Follow.objects.filter(
            follower=request.user
        ).values_list('following_id', flat=True)

        # Show posts from followed users + self
        posts = Post.objects.filter(
<<<<<<< HEAD
            user__in=list(following_ids) + [request.user.id]
=======
            user__in=list(following_ids) + [request.user.id],
            status='published'
>>>>>>> sub-branch2
        ).select_related('user').annotate(
            like_count=Count('like', distinct=True),
            comment_count=Count('comment', distinct=True)
        ).order_by('-created_at')

        # Limit people list to a reasonable number to improve render performance
        users = User.objects.exclude(id=request.user.id)[:20]

    else:
<<<<<<< HEAD
        posts = Post.objects.all().select_related('user').annotate(
=======
        posts = Post.objects.filter(status='published').select_related('user').annotate(
>>>>>>> sub-branch2
            like_count=Count('like', distinct=True),
            comment_count=Count('comment', distinct=True)
        ).order_by('-created_at')
        users = []
        following_ids = []

<<<<<<< HEAD
    # Compute trending hashtags and top liked posts
=======
    # Compute trending hashtags and top liked posts (published posts only)
>>>>>>> sub-branch2
    import re
    from collections import Counter

    # Limit the scope for computing trending hashtags to recent posts (reduces scanning all historical posts)
<<<<<<< HEAD
    all_posts = Post.objects.order_by('-created_at')[:500]
=======
    all_posts = Post.objects.filter(status='published').order_by('-created_at')[:500]
>>>>>>> sub-branch2
    hashtag_counter = Counter()
    for p in all_posts:
        tags = re.findall(r"#(\w+)", p.content)
        for t in tags:
            hashtag_counter[t.lower()] += 1

    top_hashtags = [h for h,c in hashtag_counter.most_common(8)]
    # Top liked posts
<<<<<<< HEAD
    top_posts = Post.objects.annotate(like_count=Count('like')).select_related('user').order_by('-like_count', '-created_at')[:5]

    context = {
        'posts': posts,
        'users': users,
        'following_ids': following_ids,
        'trending_hashtags': top_hashtags,
        'trending_posts': top_posts,
    }
    
    return render(request, 'home.html', context)
=======
    top_posts = Post.objects.filter(status='published').annotate(like_count=Count('like')).select_related('user').order_by('-like_count', '-created_at')[:5]
    # attach liked posts list for template
>>>>>>> sub-branch2
    liked_posts = []
    if request.user.is_authenticated:
        liked_posts = Like.objects.filter(user=request.user).values_list('post_id', flat=True)

    # Build unified feed (optionally include community posts)
    posts_list = list(posts)
    if include_communities:
        from .models import CommunityPost
        community_posts = CommunityPost.objects.select_related('user', 'community').prefetch_related('comments').order_by('-created_at')[:50]
        # Normalize community posts to be compatible with template expectations
        for cp in community_posts:
            setattr(cp, 'is_community', True)
            setattr(cp, 'community_obj', cp.community)
            setattr(cp, 'like_count', 0)
            # Provide comment_set similar API used for regular posts
            setattr(cp, 'comment_set', cp.comments)

        # Mark regular posts as non-community
        for p in posts_list:
            setattr(p, 'is_community', False)

        posts_list.extend(list(community_posts))
    else:
        for p in posts_list:
            setattr(p, 'is_community', False)

    # Merge and sort by creation time
    posts_list.sort(key=lambda x: x.created_at, reverse=True)

    context = {
        'posts': posts_list,
        'users': users,
        'following_ids': following_ids,
        'trending_hashtags': top_hashtags,
        'trending_posts': top_posts,
        'liked_posts': liked_posts,
        'include_communities': include_communities,
    }

    return render(request, 'home.html', context)


def profile(request, username):
    profile_user = get_object_or_404(User, username=username)

<<<<<<< HEAD
    posts = Post.objects.filter(user=profile_user).select_related('user').annotate(
=======
    # Show drafts only to the profile owner
    if request.user.is_authenticated and request.user == profile_user:
        posts_qs = Post.objects.filter(user=profile_user)
    else:
        posts_qs = Post.objects.filter(user=profile_user, status='published')

    posts = posts_qs.select_related('user').annotate(
>>>>>>> sub-branch2
        like_count=Count('like', distinct=True),
        comment_count=Count('comment', distinct=True)
    ).order_by('-created_at')

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


def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.select_related('user').annotate(
        like_count=Count('like', distinct=True),
        comment_count=Count('comment', distinct=True)
    ), id=post_id)

<<<<<<< HEAD
=======
    # Prevent others from viewing drafts
    if post.status == 'draft' and (not request.user.is_authenticated or request.user != post.user):
        return redirect('home')

>>>>>>> sub-branch2
    liked = False
    if request.user.is_authenticated:
        liked = Like.objects.filter(user=request.user, post=post).exists()

    comments = Comment.objects.filter(post=post).select_related('user').order_by('created_at')

    # compute trending hashtags and top posts for sidebar
    import re
    from collections import Counter
<<<<<<< HEAD
    all_posts = Post.objects.order_by('-created_at')[:500]
=======
    all_posts = Post.objects.filter(status='published').order_by('-created_at')[:500]
>>>>>>> sub-branch2
    hashtag_counter = Counter()
    for p in all_posts:
        tags = re.findall(r"#(\w+)", p.content)
        for t in tags:
            hashtag_counter[t.lower()] += 1
    top_hashtags = [h for h,c in hashtag_counter.most_common(8)]
<<<<<<< HEAD
    top_posts = Post.objects.annotate(like_count=Count('like')).order_by('-like_count', '-created_at')[:5]
=======
    top_posts = Post.objects.filter(status='published').annotate(like_count=Count('like')).order_by('-like_count', '-created_at')[:5]
>>>>>>> sub-branch2

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
<<<<<<< HEAD
    posts = posts.select_related('user').annotate(
=======
    # Only show published posts in search results
    posts = posts.filter(status='published').select_related('user').annotate(
>>>>>>> sub-branch2
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
<<<<<<< HEAD
    all_posts = Post.objects.all()
=======
    all_posts = Post.objects.filter(status='published')
>>>>>>> sub-branch2
    hashtag_counter = Counter()
    for p in all_posts:
        tags = re.findall(r"#(\w+)", p.content)
        for t in tags:
            hashtag_counter[t.lower()] += 1
    top_hashtags = [h for h,c in hashtag_counter.most_common(8)]
<<<<<<< HEAD
    top_posts = Post.objects.annotate(like_count=Count('like')).order_by('-like_count', '-created_at')[:5]
=======
    top_posts = Post.objects.filter(status='published').annotate(like_count=Count('like')).order_by('-like_count', '-created_at')[:5]
>>>>>>> sub-branch2

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
        content = request.POST.get('content', '').strip()
        action = request.POST.get('action', 'publish')

        if content == '':
            # do not create empty posts
            messages.error(request, 'Post content cannot be empty')
            return redirect('home')

        status = 'draft' if action == 'draft' else 'published'
        Post.objects.create(
            user=request.user,
            content=content,
            status=status
        )

        if status == 'draft':
            messages.success(request, 'Saved draft')
            return redirect('drafts')
        else:
            return redirect('home')

@login_required
def follow_user(request, user_id):
    # Only allow POST for follow action
    if request.method != 'POST':
        messages.error(request, 'Invalid method')
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    user_to_follow = get_object_or_404(User, id=user_id)

    # Prevent user from following themselves
    if user_to_follow != request.user:
        Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )

    # Return to the page the user came from (profile page), fall back to home
    return redirect(request.META.get('HTTP_REFERER', 'home'))
@login_required
def unfollow_user(request, user_id):
    # Only allow POST for unfollow action
    if request.method != 'POST':
        messages.error(request, 'Invalid method')
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    user_to_unfollow = get_object_or_404(User, id=user_id)

    Follow.objects.filter(
        follower=request.user,
        following=user_to_unfollow
    ).delete()

    # Return to the referring page so unfollow keeps user on the profile
    return redirect(request.META.get('HTTP_REFERER', 'home'))

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
<<<<<<< HEAD
        messages.success(request, 'Post deleted')
        return redirect('home')

    return render(request, 'confirm_delete.html', {'post': post})
=======
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok', 'message': 'Post deleted', 'post_id': post_id})
        messages.success(request, 'Post deleted')
        return redirect('home')

    return render(request, 'confirm_delete.html', {'post': post})


@login_required
def drafts(request):
    drafts_qs = Post.objects.filter(user=request.user, status='draft').select_related('user').annotate(
        like_count=Count('like', distinct=True),
        comment_count=Count('comment', distinct=True)
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


# --- Community views ---
from .models import Community, CommunityPost, CommunityComment


def community_list(request):
    communities = Community.objects.order_by('-created_at')
    context = {'communities': communities}
    return render(request, 'community_list.html', context)


def community_detail(request, community_id):
    community = get_object_or_404(Community, id=community_id)
    posts = community.posts.select_related('user').prefetch_related('comments').order_by('-created_at')

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to post in a community')
            return redirect('login')

        # support posting a community post or adding a comment
        action = request.POST.get('action')
        if action == 'post':
            content = request.POST.get('content', '').strip()
            if content:
                CommunityPost.objects.create(
                    community=community,
                    user=request.user,
                    content=content
                )
                return redirect('community_detail', community_id=community.id)
            else:
                messages.error(request, 'Post content cannot be empty')
        elif action == 'comment':
            post_id = request.POST.get('post_id')
            text = request.POST.get('comment', '').strip()
            if post_id and text:
                post = get_object_or_404(CommunityPost, id=post_id, community=community)
                CommunityComment.objects.create(post=post, user=request.user, text=text)
                return redirect('community_detail', community_id=community.id)
            else:
                messages.error(request, 'Comment text cannot be empty')

    context = {
        'community': community,
        'posts': posts,
    }
    return render(request, 'community_detail.html', context)


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
>>>>>>> sub-branch2
