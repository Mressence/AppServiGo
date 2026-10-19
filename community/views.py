
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CommentForm, PostForm, ReportForm
from .models import Category, Comment, Post, Report, Vote


def is_moderator(user):
    return (
        user.is_authenticated
        and (
            user.is_staff
            or user.is_superuser
            or getattr(user, "role", "") == "ADMINISTRADOR"
        )
    )


def moderator_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not is_moderator(request.user):
            return HttpResponseForbidden(
                "No tienes permiso para acceder a la moderación."
            )
        return view_func(request, *args, **kwargs)
    return wrapper


def post_list(request):
    posts = Post.objects.filter(
        status=Post.Status.APPROVED
    ).select_related("author", "category").annotate(
        helpful_count=Count("votes", distinct=True),
        comments_count=Count(
            "comments",
            filter=Q(comments__status=Comment.Status.APPROVED),
            distinct=True,
        ),
    )

    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("categoria", "").strip()

    if query:
        posts = posts.filter(
            Q(title__icontains=query) | Q(body__icontains=query)
        )

    if category_slug:
        posts = posts.filter(category__slug=category_slug)

    categories = Category.objects.filter(is_active=True)

    page_obj = Paginator(posts, 10).get_page(request.GET.get("page"))

    return render(request, "community/post_list.html", {
        "page_obj": page_obj,
        "categories": categories,
        "query": query,
        "selected_category": category_slug,
        "is_moderator": is_moderator(request.user),
    })


@login_required
def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.status = Post.Status.PENDING
            post.save()
            messages.success(
                request,
                "Tu publicación fue enviada y está pendiente de revisión."
            )
            return redirect("community:list")
    else:
        form = PostForm()

    return render(request, "community/post_form.html", {"form": form})


def post_detail(request, pk):
    post = get_object_or_404(
        Post.objects.select_related("author", "category").annotate(
            helpful_count=Count("votes", distinct=True)
        ),
        pk=pk,
    )

    can_moderate = is_moderator(request.user)

    if post.status != Post.Status.APPROVED:
        if not can_moderate and (
            not request.user.is_authenticated
            or post.author_id != request.user.pk
        ):
            messages.error(request, "Esta publicación no está disponible.")
            return redirect("community:list")

    comments = post.comments.filter(
        status=Comment.Status.APPROVED
    ).select_related("author")

    comment_form = CommentForm()
    report_form = ReportForm()

    user_voted = (
        request.user.is_authenticated
        and Vote.objects.filter(post=post, user=request.user).exists()
    )

    already_reported = (
        request.user.is_authenticated
        and Report.objects.filter(post=post, reporter=request.user).exists()
    )

    return render(request, "community/post_detail.html", {
        "post": post,
        "comments": comments,
        "comment_form": comment_form,
        "report_form": report_form,
        "user_voted": user_voted,
        "already_reported": already_reported,
        "is_moderator": can_moderate,
    })


@login_required
@require_POST
def comment_create(request, pk):
    post = get_object_or_404(Post, pk=pk, status=Post.Status.APPROVED)
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.status = Comment.Status.PENDING
        comment.save()
        messages.success(
            request,
            "Tu respuesta fue enviada y está pendiente de revisión."
        )
    else:
        messages.error(request, "Revisa el contenido de tu respuesta.")

    return redirect("community:detail", pk=post.pk)


@login_required
@require_POST
def post_vote(request, pk):
    post = get_object_or_404(Post, pk=pk, status=Post.Status.APPROVED)
    vote, created = Vote.objects.get_or_create(post=post, user=request.user)

    if created:
        messages.success(request, "Marcaste esta publicación como útil.")
    else:
        vote.delete()
        messages.info(request, "Quitaste tu voto.")

    return redirect("community:detail", pk=post.pk)


@login_required
@require_POST
def post_report(request, pk):
    post = get_object_or_404(Post, pk=pk, status=Post.Status.APPROVED)

    if post.author_id == request.user.pk:
        messages.error(request, "No puedes reportar tu propia publicación.")
        return redirect("community:detail", pk=post.pk)

    if Report.objects.filter(post=post, reporter=request.user).exists():
        messages.info(request, "Ya has reportado esta publicación.")
        return redirect("community:detail", pk=post.pk)

    form = ReportForm(request.POST)

    if form.is_valid():
        report = form.save(commit=False)
        report.post = post
        report.reporter = request.user
        report.save()
        messages.success(
            request,
            "El reporte fue enviado al equipo de moderación."
        )
    else:
        messages.error(request, "No se pudo enviar el reporte.")

    return redirect("community:detail", pk=post.pk)


@moderator_required
def moderation(request):
    pending_posts = Post.objects.filter(
        status=Post.Status.PENDING
    ).select_related("author", "category")

    pending_comments = Comment.objects.filter(
        status=Comment.Status.PENDING
    ).select_related("author", "post")

    pending_reports = Report.objects.filter(
        status=Report.Status.PENDING
    ).select_related("reporter", "post")

    return render(request, "community/moderation.html", {
        "pending_posts": pending_posts,
        "pending_comments": pending_comments,
        "pending_reports": pending_reports,
    })


@moderator_required
@require_POST
def moderate_item(request, item_type, pk):
    action = request.POST.get("action")

    post_actions = {
        "approve": Post.Status.APPROVED,
        "reject": Post.Status.REJECTED,
        "hide": Post.Status.HIDDEN,
    }
    comment_actions = {
        "approve": Comment.Status.APPROVED,
        "reject": Comment.Status.REJECTED,
        "hide": Comment.Status.HIDDEN,
    }

    if item_type == "post":
        item = get_object_or_404(Post, pk=pk)
        status = post_actions.get(action)
    elif item_type == "comment":
        item = get_object_or_404(Comment, pk=pk)
        status = comment_actions.get(action)
    else:
        messages.error(request, "Tipo de contenido no válido.")
        return redirect("community:moderation")

    if status is None:
        messages.error(request, "Acción de moderación no válida.")
        return redirect("community:moderation")

    item.status = status
    item.save(update_fields=["status"])

    messages.success(request, "Se actualizó el estado del contenido.")
    return redirect("community:moderation")


@moderator_required
@require_POST
def moderate_report(request, pk):
    report = get_object_or_404(Report, pk=pk)
    action = request.POST.get("action")

    if action == "reviewed":
        report.status = Report.Status.REVIEWED
    elif action == "dismiss":
        report.status = Report.Status.DISMISSED
    elif action == "hide":
        report.post.status = Post.Status.HIDDEN
        report.post.save(update_fields=["status"])
        report.status = Report.Status.REVIEWED
    else:
        messages.error(request, "Acción de reporte no válida.")
        return redirect("community:moderation")

    report.save(update_fields=["status"])
    messages.success(request, "Se actualizó el reporte.")
    return redirect("community:moderation")
