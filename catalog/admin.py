from django.contrib import admin
from .models import Category, ServiceType

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "active", "created_at")
    list_filter = ("active",)
    search_fields = ("name",)

@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "active", "created_at")
    list_filter = ("active", "category")
    search_fields = ("name", "category__name")
