from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from taggit.managers import TaggableManager
from html import unescape
from django.utils.html import strip_tags
from shortuuid.django_fields import ShortUUIDField
from pyuploadcare.dj.models import ImageField
from django_ckeditor_5.fields import CKEditor5Field


BLOG_PUBLISH_STATUS = (
	("draft", "draft"),
	("in_review", "In Review"),
	("published", "Published"),
)


class Category(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, help_text="SEO-friendly URL slug")
    description = models.TextField(blank=True, null=True, help_text="Category description for SEO")
    active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['active']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Return the canonical URL for this category"""
        return reverse('blog:category-detail', kwargs={'slug': self.slug})

    def get_published_posts(self):
        """Get published posts in this category"""
        return self.post_set.filter(status='published').order_by('-date')
        
    
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    image = ImageField(blank=True, null=True, manual_crop="4:4",)
    title = models.CharField(max_length=1000)
    slug = models.SlugField(max_length=1000, unique=True, blank=True, help_text="SEO-friendly URL slug (auto-generated from title)")
    excerpt = CKEditor5Field(config_name='default', blank=True, null=True, help_text="Brief description of the post")
    content = CKEditor5Field(config_name='default', help_text="Main blog content with rich text formatting")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    tags = TaggableManager()
    status = models.CharField(choices=BLOG_PUBLISH_STATUS, max_length=100, default="in_review")
    featured = models.BooleanField(default=False)
    trending = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    views = models.PositiveIntegerField(default=0)
    pid = ShortUUIDField(length=10, max_length=25, alphabet="abcdefghijklmnopqrstuvxyz")

    class Meta:
        verbose_name = "Posts"
        verbose_name_plural = "Posts"
        ordering = ['-date']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status', 'date']),
            models.Index(fields=['featured', 'status']),
            models.Index(fields=['trending', 'status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['views']),
        ]

    def __str__(self):
        return self.title[:50] + "..." if len(self.title) > 50 else self.title

    def save(self, *args, **kwargs):
        """Auto-generate slug from title if not provided"""
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1

            # Ensure unique slug
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Return the canonical URL for this post"""
        return reverse('blog:blog-detail', kwargs={'slug': self.slug})

    def get_read_time(self):
        string = self.content + unescape(strip_tags(self.content))
        total_words = len((string).split())

        return round(total_words / 200)

    def get_excerpt(self):
        """Return excerpt if available, otherwise generate from content"""
        if self.excerpt:
            # Check if excerpt has meaningful content (not just empty HTML)
            clean_excerpt = strip_tags(self.excerpt).strip()
            if clean_excerpt and clean_excerpt != '&nbsp;':
                return self.excerpt

        # Auto-generate excerpt from content (first 150 characters)
        clean_content = strip_tags(self.content)
        return clean_content[:150] + "..." if len(clean_content) > 150 else clean_content

    def get_meta_description(self):
        """Return SEO meta description (max 160 characters)"""
        excerpt = self.get_excerpt()
        clean_excerpt = strip_tags(excerpt)
        return clean_excerpt[:160] + "..." if len(clean_excerpt) > 160 else clean_excerpt

    def get_reading_time_display(self):
        """Return formatted reading time"""
        time = self.get_read_time()
        return f"{time} min read" if time > 0 else "Quick read"

    def get_related_posts(self, limit=6):
        """Get related posts from same category"""
        return Post.objects.filter(
            category=self.category,
            status='published'
        ).exclude(pk=self.pk).order_by('-views', '-date')[:limit]

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    full_name = models.CharField(max_length=1000)
    email = models.EmailField()
    comment = CKEditor5Field(config_name='default', help_text="Comment content with basic formatting")
    date = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return self.comment[0:20]