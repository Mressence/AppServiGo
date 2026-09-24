from django.shortcuts import render
from .models import Category

def catalog(request):
    categories = Category.objects.filter(active=True).prefetch_related("services")
    return render(request, "catalog/catalog.html", {"categories": categories})
