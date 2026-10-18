
from django.db.models import Q
from django.shortcuts import render

from .models import Category, ServiceType
from technicians.models import TechnicianProfile
from accounts.models import User


def catalog(request):
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("categoria", "").strip()

    categories = Category.objects.filter(active=True).order_by("name")

    services = ServiceType.objects.filter(
        active=True,
        category__active=True,
    ).select_related("category")

    technicians = TechnicianProfile.objects.filter(
        status=TechnicianProfile.Status.APROBADO,
        category__active=True,
        user__is_active=True,
        user__role=User.Role.TECNICO,
    ).select_related("user", "category").distinct()

    if query:
        services = services.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
        )

        technicians = technicians.filter(
            Q(professional_title__icontains=query)
            | Q(description__icontains=query)
            | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(category__name__icontains=query)
        )

    if category_id.isdigit():
        services = services.filter(category_id=int(category_id))
        technicians = technicians.filter(category_id=int(category_id))

    return render(request, "catalog/catalog.html", {
        "categories": categories,
        "active_categories": categories,
        "services": services,
        "technicians": technicians,
        "query": query,
        "selected_category": category_id,
    })
