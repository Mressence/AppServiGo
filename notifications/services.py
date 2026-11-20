from .models import Notification


def notify(user, title, message, kind=Notification.Kind.GENERAL, url=""):
    if not user:
        return None
    return Notification.objects.create(
        recipient=user,
        title=title,
        message=message,
        notification_type=kind,
        related_url=url,
    )
