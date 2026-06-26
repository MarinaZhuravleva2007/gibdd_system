# accounts/context_processors.py
from .models import Notification

def notifications_count(request):
    if request.user.is_authenticated and request.user.role == 'driver':
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        return {'unread_notifications_count': unread_count}
    return {'unread_notifications_count': 0}