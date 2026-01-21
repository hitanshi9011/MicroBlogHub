from django.urls import path
from . import views


urlpatterns = [
	# Home / Auth
	path('', views.home, name='home'),
	path('register/', views.register, name='register'),
	path('login/', views.login_view, name='login'),
	path('logout/', views.logout_view, name='logout'),

	# Profile
	path('profile/edit/', views.edit_profile, name='edit_profile'),

	# canonical profile routes (username-specific)
 	path('profile/<str:username>/', views.profile, name='profile'),
 	path('users/<str:username>/posts/', views.user_posts, name='user_posts'),
 	path('profile/<str:username>/followers/', views.followers_list, name='followers'),
 	path('profile/<str:username>/following/', views.following_list, name='following'),
	path('account/delete/', views.delete_account, name='delete_account'),

	# Posts
	path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
	path('posts/<int:post_id>/edit/', views.edit_post, name='edit_post'),
	path('posts/<int:post_id>/delete/', views.delete_post, name='delete_post'),
	path('create/', views.create_post, name='create_post'),

	# Follow / Like (names expected by templates)
    path('follow/<int:user_id>/', views.follow_user, name='follow'),
    path('unfollow/<int:user_id>/', views.unfollow_user, name='unfollow'),
    path('like/<int:post_id>/', views.like_post, name='like'),
    path('unlike/<int:post_id>/', views.unlike_post, name='unlike'),
	path('bookmark/<int:post_id>/', views.bookmark_post, name='bookmark'),
	path('unbookmark/<int:post_id>/', views.unbookmark_post, name='unbookmark'),
	path('bookmark/toggle/<int:post_id>/', views.toggle_bookmark, name='bookmark_toggle'),
	path('bookmarks/', views.bookmarks, name='bookmarks'),

	# Drafts
	path('drafts/', views.drafts, name='drafts'),
	path('drafts/edit/<int:post_id>/', views.edit_draft, name='edit_draft'),
	path('drafts/delete/<int:post_id>/', views.delete_draft, name='delete_draft'),
	path('drafts/publish/<int:post_id>/', views.publish_draft, name='publish_draft'),
	path('drafts/action/<int:post_id>/', views.draft_action, name='draft_action'),

	# Comments
	path('comments/add/<int:post_id>/', views.add_comment, name='add_comment'),
	path('comments/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
	path('comments/edit/<int:comment_id>/', views.edit_comment, name='edit_comment'),
	path('comments/reply/<int:comment_id>/', views.reply_comment, name='reply_comment'),
	path('comments/toggle-like/<int:comment_id>/', views.toggle_comment_like, name='toggle_comment_like'),

	# Notifications
	path('notifications/', views.notifications, name='notifications'),
	path('notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
	path('notifications/dropdown/', views.notification_dropdown, name='notification_dropdown'),
	path('notifications/<int:id>/redirect/', views.notification_redirect, name='notification_redirect'),

	# Community URLs (single canonical set)
	path('communities/', views.community_list, name='community_list'),
	path('communities/create/', views.create_community, name='create_community'),
	path('communities/<int:community_id>/', views.community_detail, name='community_detail'),
	path('communities/<int:community_id>/post/<int:post_id>/delete/', views.delete_community_post, name='delete_community_post'),
	path('communities/<int:community_id>/post/<int:post_id>/edit/', views.edit_community_post, name='edit_community_post'),
	path('communities/<int:community_id>/comment/<int:comment_id>/delete/', views.delete_community_comment, name='delete_community_comment'),
	path('communities/<int:community_id>/delete/', views.delete_community, name='delete_community'),
	path('communities/join/<int:community_id>/', views.join_community, name='join_community'),
	path('communities/leave/<int:community_id>/', views.leave_community, name='leave_community'),
	path('community/post/<int:post_id>/like/', views.toggle_community_like, name='toggle_community_like'),

	# Messages
	path('messages/', views.messages_list, name='messages'),
	path('messages/<str:username>/', views.conversation, name='conversation'),

	# Search
	path('search/', views.search, name='search'),

	# Debug / misc
	path('debug/profile-files/', views.list_profile_files, name='list_profile_files'),
]
