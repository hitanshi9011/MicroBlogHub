from django.contrib import admin
from .models import Post, Follow, Like, Comment, CommunityPost, CommunityComment
from .models import Community


admin.site.register(Post)
admin.site.register(Follow)
admin.site.register(Like)
admin.site.register(Comment)

# Community admin
@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
	list_display = ('name', 'created_by', 'created_at')
	search_fields = ('name',)


@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
	list_display = ('community', 'user', 'created_at')
	search_fields = ('community__name', 'user__username', 'content')


@admin.register(CommunityComment)
class CommunityCommentAdmin(admin.ModelAdmin):
	list_display = ('post', 'user', 'created_at')
	search_fields = ('post__content', 'user__username', 'text')