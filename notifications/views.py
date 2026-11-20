from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import Notification


@login_required
def notification_list(request):
    items = Notification.objects.filter(recipient=request.user)
    return render(request, "notifications/list.html", {"notifications": items})


@login_required
def notification_read(request, pk):
    item = get_object_or_404(Notification, pk=pk, recipient=request.user)
    if not item.is_read:
        item.is_read = True
        item.save(update_fields=["is_read"])
    if item.related_url:
        return redirect(item.related_url)
    return redirect("notifications:list")


@login_required
def notification_read_all(request):
    if request.method == "POST":
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return redirect("notifications:list")
