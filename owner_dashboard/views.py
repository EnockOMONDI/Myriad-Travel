from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone

from .services import build_dashboard_context


@staff_member_required
def dashboard(request):
    context = build_dashboard_context(request.user)
    context["last_updated"] = timezone.now()
    return render(request, "owner_dashboard/dashboard.html", context)
