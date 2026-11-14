from django.urls import path

from . import content_views

app_name = 'admin_content'

urlpatterns = [
    path('', content_views.content_overview, name='content_overview'),
    path('homepage/hero/', content_views.homepage_hero, name='homepage_hero'),
    path('homepage/explore-kenya/', content_views.homepage_explore_kenya, name='homepage_explore_kenya'),
    path('homepage/explore-the-world/', content_views.homepage_explore_world, name='homepage_explore_world'),
    path('homepage/hero/slides/new/', content_views.hero_slide_editor, name='hero_slide_new'),
    path('homepage/hero/slides/<int:pk>/', content_views.hero_slide_editor, name='hero_slide_edit'),
]
