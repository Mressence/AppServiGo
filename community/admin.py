
from django.contrib import admin
from .models import Category, Comment, Post, Report, Vote


@admin.action(description="Aprobar contenido seleccionado")
def approve_items(modeladmin, request, queryset):
    queryset.update(status="APPROVED")


@admin.action(description="Rechazar contenido seleccionado")
def reject_items(modeladmin, request, queryset):
    queryset.update(status="REJECTED")


@admin.action(description="Ocultar contenido seleccionado")
def hide_items(modeladmin, request, queryset):
    queryset.update(status="HIDDEN")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "title", "author", "category", "status",
        "is_seed", "created_at",
    )
    list_filter = ("status", "category", "is_seed", "created_at")
    search_fields = ("title", "body", "author__username", "author__email")
    list_editable = ("status",)
    readonly_fields = ("created_at", "updated_at")
    actions = (approve_items, reject_items, hide_items)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "author", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("body", "author__username", "post__title")
    list_editable = ("status",)
    actions = (approve_items, reject_items, hide_items)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("post", "reporter", "reason", "status", "created_at")
    list_filter = ("status", "reason", "created_at")
    search_fields = ("post__title", "reporter__username", "details")
    list_editable = ("status",)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "created_at")
    search_fields = ("post__title", "user__username")
