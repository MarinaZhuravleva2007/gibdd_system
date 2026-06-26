from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


def inspector_required(view_func):
    """Декоратор для проверки, что инспектор не уволен"""

    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if request.user.role != 'inspector':
            messages.error(request, 'Доступ запрещен. Только для инспекторов.')
            return redirect('home')

        if request.user.is_dismissed:
            messages.error(request, request.user.get_dismissal_message() or
                           'Вы уволены. Доступ к созданию нарушений закрыт.')
            return redirect('inspector_dismissed_page')

        return view_func(request, *args, **kwargs)

    return wrapper


def can_create_violation(view_func):
    """Декоратор для проверки права на создание нарушения"""

    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.can_create_violations():
            messages.error(request, request.user.get_dismissal_message() or
                           'У вас нет прав на создание нарушений.')
            return redirect('dashboard')

        return view_func(request, *args, **kwargs)

    return wrapper