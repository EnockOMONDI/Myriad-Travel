from django.contrib import admin
from django import forms
from django.db import models
from blog.models import Post, Comment, Category
from django_ckeditor_5.widgets import CKEditor5Widget
from django_ckeditor_5.fields import CKEditor5Field

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('get_title', 'slug', 'status', 'category', 'user', 'featured', 'trending', 'views', 'date')
    list_editable = ['status', 'category', 'featured', 'trending']
    list_filter = ('category', 'status', 'featured', 'trending', 'date', 'updated')
    search_fields = ['title', 'content', 'excerpt', 'slug']
    readonly_fields = ['views', 'date', 'updated', 'pid']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'date'
    ordering = ['-date']

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'excerpt', 'category', 'tags', 'image')
        }),
        ('Content', {
            'fields': ('content',),
            'classes': ('wide',)
        }),
        ('Publishing', {
            'fields': ('status', 'featured', 'trending', 'user'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('views', 'date', 'updated', 'pid'),
            'classes': ('collapse',)
        }),
    )

    # RichTextField widgets are automatically handled by the field configuration
    # No formfield_overrides needed for RichTextField

    class Media:
        css = {
            'all': ('assets/css/ckeditor5-admin.css',)
        }

    def get_title(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    get_title.short_description = 'Title'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'get_post_count', 'active', 'created')
    list_editable = ['active']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created']
    ordering = ['title']

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'active')
        }),
        ('System Information', {
            'fields': ('created',),
            'classes': ('collapse',)
        }),
    )

    def get_post_count(self, obj):
        count = obj.post_set.filter(status='published').count()
        return f"{count} posts"
    get_post_count.short_description = 'Published Posts'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('get_comment', 'post', 'full_name', 'email', 'active', 'date')
    list_editable = ['active']
    list_filter = ('active', 'date', 'post__category')
    search_fields = ['full_name', 'email', 'comment', 'post__title']
    readonly_fields = ['date']
    ordering = ['-date']

    fieldsets = (
        ('Comment Information', {
            'fields': ('post', 'full_name', 'email', 'comment')
        }),
        ('Moderation', {
            'fields': ('active', 'date'),
        }),
    )

    def get_comment(self, obj):
        return obj.comment[:50] + "..." if len(obj.comment) > 50 else obj.comment
    get_comment.short_description = 'Comment'