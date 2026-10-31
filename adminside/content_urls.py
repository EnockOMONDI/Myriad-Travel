from django.urls import path

from . import content_views

app_name = 'admin_content'

urlpatterns = [
    path('', content_views.content_overview, name='content_overview'),
    path('homepage/hero/', content_views.homepage_hero, name='homepage_hero'),
    path('homepage/hero/slides/new/', content_views.hero_slide_editor, name='hero_slide_new'),
    path('homepage/hero/slides/<int:pk>/', content_views.hero_slide_editor, name='hero_slide_edit'),
]
