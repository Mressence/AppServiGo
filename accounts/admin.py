from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name", "phone")
    fieldsets = DjangoUserAdmin.fieldsets + (("AppServiGo", {"fields": ("role", "phone", "address", "profile_photo")}),)
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (("AppServiGo", {"fields": ("role", "email", "first_name", "last_name")}),)
