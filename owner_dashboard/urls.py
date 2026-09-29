from django.urls import path

from . import views

app_name = "owner_dashboard"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
]
