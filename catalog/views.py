from django.db.models import Q
from django.shortcuts import render
from .models import Category, ServiceType


def catalog(request):
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("categoria", "").strip()
    services = ServiceType.objects.filter(active=True, category__active=True).select_related("category")
    if query:
        services = services.filter(Q(name__icontains=query) | Q(description__icontains=query) | Q(category__name__icontains=query))
    if category_id.isdigit():
        services = services.filter(category_id=int(category_id))
    categories = Category.objects.filter(active=True).prefetch_related("services")
    active_categories = Category.objects.filter(active=True).order_by("name")
    return render(request, "catalog/catalog.html", {
        "categories": categories, "services": services, "active_categories": active_categories,
        "query": query, "selected_category": category_id,
    })
