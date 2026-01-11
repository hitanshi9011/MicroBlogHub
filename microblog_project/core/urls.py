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

    # PROFILE
    path('profile/<str:username>/', views.profile, name='profile'),

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
