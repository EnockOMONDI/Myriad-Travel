from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse, Http404
from django.urls import reverse
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.contrib import messages
from django.db.models import Q, Count, Prefetch, F
from django.db import models
from django.core.paginator import Paginator
from django.utils import timezone
from blog.models import Post, Category, Comment


@cache_page(60 * 15)  # Cache for 15 minutes
def blog_list(request):
    """Optimized blog list view with caching and efficient queries"""

    # Get base queryset with optimized queries
    blog_queryset = Post.objects.select_related('category', 'user').prefetch_related('tags').filter(
        status="published"
    )

    # Get featured posts with optimized query
    featured_blog = blog_queryset.filter(featured=True).order_by("-date")[:6]

    # Get active categories with post counts (cached)
    categories_cache_key = 'blog_categories_with_counts'
    categories = cache.get(categories_cache_key)
    if categories is None:
        categories = Category.objects.filter(active=True).annotate(
            post_count=Count('post', filter=Q(post__status='published'))
        ).order_by('title')
        cache.set(categories_cache_key, categories, 60 * 30)  # Cache for 30 minutes

    # Apply filters
    blog = blog_queryset
    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category")
    sort_by = request.GET.get("sort", "latest")

    # Search functionality with better performance
    if query:
        blog = blog.filter(
            Q(title__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()

    # Category filtering
    if category_slug:
        try:
            category = Category.objects.get(slug=category_slug, active=True)
            blog = blog.filter(category=category)
        except Category.DoesNotExist:
            messages.error(request, "Category not found.")
            return redirect('blog:blog-list')

    # Sorting options
    if sort_by == "popular":
        blog = blog.order_by("-views", "-date")
    elif sort_by == "oldest":
        blog = blog.order_by("date")
    elif sort_by == "trending":
        blog = blog.filter(trending=True).order_by("-date")
    else:  # latest (default)
        blog = blog.order_by("-date")

    # Enhanced pagination
    paginator = Paginator(blog, 12)  # Show 12 posts per page
    page_number = request.GET.get('page')
    blog_page = paginator.get_page(page_number)

    # Get blog count for display
    blog_count = blog_queryset.count()

    context = {
        "query": query,
        "categories": categories,
        "blog_count": blog_count,
        "blog": blog_page,
        "featured_blog": featured_blog,
        "sort_by": sort_by,
        "category_slug": category_slug,
        "page_title": "Travel Blog - Mbugani Luxe Adventures",
        "meta_description": "Discover amazing travel stories, tips, and guides from Mbugani Luxe Adventures. Explore destinations, get travel advice, and plan your next adventure.",
    }
    return render(request, 'users/bloglist.html', context)

def blog_detail(request, slug=None, pid=None):
    """Optimized blog detail view with slug-based URLs"""

    # Get post by slug (preferred) or pid (fallback)
    if slug:
        post = get_object_or_404(
            Post.objects.select_related('category', 'user').prefetch_related('tags'),
            slug=slug,
            status="published"
        )
    elif pid:
        post = get_object_or_404(
            Post.objects.select_related('category', 'user').prefetch_related('tags'),
            pid=pid,
            status="published"
        )
    else:
        raise Http404("Post not found")

    # Get active comments with optimized query
    comments = Comment.objects.filter(post=post, active=True).order_by("-date")

    # Get related blogs from same category (optimized)
    related_blogs = post.get_related_posts(limit=6)

    # Get recent blogs (excluding current post) with optimized query
    recent_blogs = Post.objects.select_related('category').filter(
        status="published"
    ).exclude(pk=post.pk).order_by("-date")[:8]

    # Increment view count (only once per session)
    session_key = f'viewed_post_{post.slug}'
    if not request.session.get(session_key, False):
        Post.objects.filter(pk=post.pk).update(views=F('views') + 1)
        request.session[session_key] = True
        # Refresh post object to get updated view count
        post.refresh_from_db(fields=['views'])

    # Handle comment submission
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        comment_text = request.POST.get("comment", "").strip()
        email = request.POST.get("email", "").strip()

        if full_name and comment_text and email:
            Comment.objects.create(
                full_name=full_name,
                email=email,
                comment=comment_text,
                post=post
            )
            messages.success(request, f"Thank you {full_name}! Your comment has been submitted for review.")
            return redirect("blog:blog-detail", slug=post.slug)
        else:
            messages.error(request, "Please fill in all required fields.")

    # Get previous and next posts for navigation (optimized)
    previous_post = Post.objects.select_related('category').filter(
        status="published",
        date__lt=post.date
    ).order_by("-date").first()

    next_post = Post.objects.select_related('category').filter(
        status="published",
        date__gt=post.date
    ).order_by("date").first()

    # SEO and meta data
    page_title = f"{post.title} - Mbugani Luxe Adventures Blog"
    meta_description = post.get_meta_description()
    canonical_url = request.build_absolute_uri(post.get_absolute_url())

    context = {
        "post": post,
        "comments": comments,
        "recent_blogs": recent_blogs,
        "related_blogs": related_blogs,
        "previous_post": previous_post,
        "next_post": next_post,
        "page_title": page_title,
        "meta_description": meta_description,
        "canonical_url": canonical_url,
        "breadcrumbs": [
            {"name": "Home", "url": "/"},
            {"name": "Blog", "url": reverse("blog:blog-list")},
            {"name": post.category.title if post.category else "Uncategorized",
             "url": post.category.get_absolute_url() if post.category else "#"},
            {"name": post.title, "url": ""}
        ]
    }
    return render(request, 'users/blogdetail.html', context)


@cache_page(60 * 30)  # Cache for 30 minutes
def category_detail(request, slug):
    """Optimized category detail view"""
    category = get_object_or_404(Category, slug=slug, active=True)

    # Get posts in this category with optimized query
    blog_queryset = Post.objects.select_related('category', 'user').prefetch_related('tags').filter(
        category=category,
        status="published"
    )

    # Search within category
    query = request.GET.get("q", "").strip()
    if query:
        blog_queryset = blog_queryset.filter(
            Q(title__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()

    # Sorting
    sort_by = request.GET.get("sort", "latest")
    if sort_by == "popular":
        blog_queryset = blog_queryset.order_by("-views", "-date")
    elif sort_by == "oldest":
        blog_queryset = blog_queryset.order_by("date")
    else:
        blog_queryset = blog_queryset.order_by("-date")

    # Pagination
    paginator = Paginator(blog_queryset, 12)
    page_number = request.GET.get('page')
    blog_page = paginator.get_page(page_number)

    # Get all categories for sidebar
    categories = Category.objects.filter(active=True).annotate(
        post_count=Count('post', filter=Q(post__status='published'))
    ).order_by('title')

    # SEO data
    page_title = f"{category.title} - Travel Blog - Mbugani Luxe Adventures"
    meta_description = category.description or f"Explore {category.title} articles and travel guides from Mbugani Luxe Adventures."

    context = {
        "category": category,
        "blog": blog_page,
        "blog_count": blog_queryset.count(),
        "query": query,
        "sort_by": sort_by,
        "categories": categories,
        "page_title": page_title,
        "meta_description": meta_description,
        "breadcrumbs": [
            {"name": "Home", "url": "/"},
            {"name": "Blog", "url": reverse("blog:blog-list")},
            {"name": category.title, "url": ""}
        ]
    }
    return render(request, 'users/category-detail.html', context)


def blog_search(request):
    """Dedicated search view for better SEO"""
    query = request.GET.get("q", "").strip()

    if not query:
        messages.info(request, "Please enter a search term.")
        return redirect("blog:blog-list")

    # Search with optimized query
    blog_queryset = Post.objects.select_related('category', 'user').prefetch_related('tags').filter(
        Q(title__icontains=query) |
        Q(excerpt__icontains=query) |
        Q(content__icontains=query) |
        Q(tags__name__icontains=query),
        status="published"
    ).distinct()

    # Pagination
    paginator = Paginator(blog_queryset, 12)
    page_number = request.GET.get('page')
    blog_page = paginator.get_page(page_number)

    # Get categories for sidebar
    categories = Category.objects.filter(active=True).annotate(
        post_count=Count('post', filter=Q(post__status='published'))
    ).order_by('title')

    context = {
        "blog": blog_page,
        "blog_count": blog_queryset.count(),
        "query": query,
        "categories": categories,
        "page_title": f"Search Results for '{query}' - Mbugani Luxe Adventures Blog",
        "meta_description": f"Search results for '{query}' in Mbugani Luxe Adventures blog.",
        "breadcrumbs": [
            {"name": "Home", "url": "/"},
            {"name": "Blog", "url": reverse("blog:blog-list")},
            {"name": f"Search: {query}", "url": ""}
        ]
    }
    return render(request, 'users/blog-search.html', context)


def blog_detail_redirect(request, pid):
    """Redirect old PID-based URLs to new slug-based URLs"""
    try:
        post = Post.objects.get(pid=pid, status="published")
        return redirect("blog:blog-detail", slug=post.slug, permanent=True)
    except Post.DoesNotExist:
        messages.error(request, "The requested article was not found.")
        return redirect("blog:blog-list")


def blog_rss(request):
    """RSS feed for blog posts"""
    # This would implement RSS feed functionality
    # For now, return a simple response
    return HttpResponse("RSS feed coming soon", content_type="text/plain")


def blog_sitemap(request):
    """XML sitemap for blog posts"""
    # This would implement XML sitemap functionality
    # For now, return a simple response
    return HttpResponse("Sitemap coming soon", content_type="text/plain")
