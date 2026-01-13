from django.urls import path
from . import views
from .views import home


urlpatterns = [

    # AUTH
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # HOME
    path('', views.home, name='home'),
    path('create-post/', views.create_post, name='create_post'),
    path('drafts/', views.drafts, name='drafts'),
    path('publish/<int:post_id>/', views.publish_draft, name='publish_draft'),
    path('draft/<int:post_id>/action/', views.draft_action, name='draft_action'),

    # Edit and delete posts
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),

    # PROFILE
    path('profile/<str:username>/', views.profile, name='profile'),
    path('search/', views.search, name='search'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('delete-account/', views.delete_account, name='delete_account'),
    # Debug: list uploaded profile photos (staff only)
    path('debug/profile-files/', views.list_profile_files, name='debug_profile_files'),
    path('profile/<str:username>/posts/', views.user_posts, name='user_posts'),
    path('profile/<str:username>/followers/', views.followers_list, name='followers'),
    path('profile/<str:username>/following/', views.following_list, name='following'),
    

    # Community URLs
    path('communities/', views.community_list, name='community_list'),
    path('communities/create/', views.create_community, name='create_community'),
    path('communities/<int:community_id>/', views.community_detail, name='community_detail'),
    path('communities/<int:community_id>/post/<int:post_id>/delete/', views.delete_community_post, name='delete_community_post'),
    path('communities/<int:community_id>/post/<int:post_id>/edit/', views.edit_community_post, name='edit_community_post'),
    path('communities/<int:community_id>/comment/<int:comment_id>/delete/', views.delete_community_comment, name='delete_community_comment'),
    path('communities/<int:community_id>/delete/', views.delete_community, name='delete_community'),
    path('communities/join/<int:community_id>/', views.join_community, name='join_community'),
    path('communities/leave/<int:community_id>/', views.leave_community, name='leave_community'),
    path(
    "community/post/<int:post_id>/like/",
    views.toggle_community_like,
    name="toggle_community_like"
),
    
    


    # FOLLOW
    path('follow/<int:user_id>/', views.follow_user, name='follow'),
    path('unfollow/<int:user_id>/', views.unfollow_user, name='unfollow'),

    # LIKE
    path('like/<int:post_id>/', views.like_post, name='like'),
    path('unlike/<int:post_id>/', views.unlike_post, name='unlike'),

    # COMMENTS
    # COMMENTS
    path('comment/<int:post_id>/', views.add_comment, name='add_comment'),
    path('comment/edit/<int:comment_id>/', views.edit_comment, name='edit_comment'),
    path('comment/reply/<int:comment_id>/', views.reply_comment, name='reply_comment'),
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path("comment/like/<int:comment_id>/", views.toggle_comment_like, name="toggle_comment_like"),


    # NOTIFICATIONS
    path('notifications/', views.notifications, name='notifications'),
    path("notifications/mark-read/", views.mark_notifications_read, name="mark_notifications_read"),
    path('notifications/dropdown/', views.notification_dropdown, name='notification_dropdown'),
    path('notifications/', views.notifications, name='notifications'),
    path(
    "notifications/redirect/<int:id>/",
    views.notification_redirect,
    name="notification_redirect"
    ),


    # MESSAGES
    path('messages/', views.messages_list, name='messages'),
    path('conversation/<str:username>/', views.conversation, name='conversation'),

]
