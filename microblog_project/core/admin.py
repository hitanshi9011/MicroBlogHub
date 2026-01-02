from django.contrib import admin
from .models import Post, Follow, Like, Comment
admin.site.register(Post)
admin.site.register(Follow)
admin.site.register(Like)
admin.site.register(Comment)