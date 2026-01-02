from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('create-post/', views.create_post, name='create_post'),

    # ✅ FOLLOW / UNFOLLOW URLS (THIS IS THE FIX)
    path('follow/<int:user_id>/', views.follow_user, name='follow'),
    path('unfollow/<int:user_id>/', views.unfollow_user, name='unfollow'),
    
    path('like/<int:post_id>/', views.like_post, name='like'),
    path('unlike/<int:post_id>/', views.unlike_post, name='unlike'),
    path('comment/<int:post_id>/', views.add_comment, name='add_comment'),
    path('profile/<str:username>/', views.profile, name='profile'),



]
