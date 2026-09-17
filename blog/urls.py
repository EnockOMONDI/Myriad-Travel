from django.urls import path
from blog import views

app_name = 'blog'

urlpatterns = [
    # Blog list and search
    path('', views.blog_list, name="blog-list"),
    path('search/', views.blog_search, name="blog-search"),

    # Category URLs (slug-based)
    path('category/<slug:slug>/', views.category_detail, name="category-detail"),

    # Post URLs (slug-based with fallback for old PIDs)
    path('post/<slug:slug>/', views.blog_detail, name="blog-detail"),
    path('p/<str:pid>/', views.blog_detail_redirect, name="blog-detail-redirect"),  # Redirect old URLs

    # RSS and sitemap
    path('rss/', views.blog_rss, name="blog-rss"),
    path('sitemap/', views.blog_sitemap, name="blog-sitemap"),
]
