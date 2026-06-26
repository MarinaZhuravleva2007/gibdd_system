import datetime
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import IntegrityError
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .forms import MyRegistrationForm, ViolationForm
from .models import FineArticle
from .models import User, Violation, Notification, ViolationReport


def unread_notifications_count(request):
    if request.user.is_authenticated and request.user.role == 'driver':
        count = Notification.objects.filter(user=request.user, is_read=False).count()
    else:
        count = 0
    return JsonResponse({'count': count})
def is_manager(user):
    return user.is_authenticated and user.role == 'manager'


def home_view(request):
    context = {}

    if request.user.is_authenticated:
        if request.user.role == 'inspector' and request.user.is_dismissed:
            return redirect('inspector_dismissed_page')

        if request.user.role == 'inspector':
            my_violations = Violation.objects.filter(inspector=request.user)

            context['total_violations'] = my_violations.count()
            context['today_violations'] = my_violations.filter(
                created_at__date=timezone.now().date()
            ).count()
            context['week_violations'] = my_violations.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count()
            context['total_fines'] = my_violations.aggregate(total=Sum('amount'))['total'] or 0

            recent_violations = my_violations.order_by('-created_at')[:10]

            # ===== ТОП РАЙОНОВ =====
            top_districts = my_violations.values('place').annotate(
                count=Count('id')
            ).order_by('-count')[:5]

            top_violators = my_violations.values('car_plate').annotate(
                count=Count('id'),
                total_amount=Sum('amount')
            ).order_by('-count')[:3]

            for violator in top_violators:
                driver = User.objects.filter(
                    role='driver',
                    license_plate__iexact=violator['car_plate']
                ).first()
                violator['full_name'] = driver.full_name if driver else 'Неизвестный'

            context.update({
                'recent_violations': recent_violations,
                'top_districts': top_districts,
                'top_violators': top_violators,
            })


        elif request.user.role == 'driver':

            driver_plate = request.user.full_license_plate  # Используем полный номер

            print(f"DEBUG: Госномер водителя: {driver_plate}")  # Отладка

            if driver_plate:
                my_violations = Violation.objects.filter(car_plate__iexact=driver_plate)

                print(f"DEBUG: Найдено нарушений: {my_violations.count()}")  # Отладка

                context['total_violations'] = my_violations.count()
                context['today_violations'] = my_violations.filter(created_at__date=timezone.now().date()).count()
                context['week_violations'] = my_violations.filter(
                    created_at__gte=timezone.now() - timedelta(days=7)).count()
                context['total_fines'] = my_violations.aggregate(total=Sum('amount'))['total'] or 0
                context['my_license_plate'] = driver_plate
                context['my_violations'] = my_violations.order_by('-created_at')[:10]
            else:
                context['no_plate'] = True

        elif request.user.role == 'manager':
            context['total_violations'] = Violation.objects.count()
            context['today_violations'] = Violation.objects.filter(created_at__date=timezone.now().date()).count()
            context['week_violations'] = Violation.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=7)).count()
            context['total_fines'] = Violation.objects.aggregate(total=Sum('amount'))['total'] or 0
            context['active_inspectors'] = User.objects.filter(role='inspector', is_dismissed=False).count()
            context['dismissed_inspectors'] = User.objects.filter(role='inspector', is_dismissed=True).count()

    return render(request, 'home.html', context)


def pdd_rules_view(request):
    return render(request, 'pdd_rules.html')

def get_fine_articles(request):
    articles = FineArticle.objects.all().values('id', 'number', 'description', 'cost')
    return JsonResponse(list(articles), safe=False)

def fines_info_view(request):
    return render(request, 'fines_info.html')


def payment_info_view(request):
    return render(request, 'payment_info.html')


def contacts_view(request):
    return render(request, 'contacts.html')


@login_required
def top_districts_report(request):
    if request.user.role != 'inspector':
        messages.error(request, 'Доступ запрещен.')
        return redirect('home')

    my_violations = Violation.objects.filter(inspector=request.user)

    districts = my_violations.values('place').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('-count')

    district_data = []
    for d in districts:
        place = d['place']
        violations = my_violations.filter(place=place).order_by('-created_at')[:20]
        district_data.append({
            'place': place,
            'count': d['count'],
            'total_amount': d['total_amount'] or 0,
            'violations': violations,
        })

    context = {
        'district_data': district_data,
        'total_violations': my_violations.count(),
    }

    return render(request, 'inspector/top_districts_report.html', context)


def register_view(request):
    if request.method == 'POST':
        form = MyRegistrationForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, '✅ Регистрация прошла успешно! Теперь вы можете войти.')
                return redirect('login')
            except IntegrityError:
                # Если логин уже существует
                form.add_error('username',
                               '❌ Пользователь с таким логином уже существует. Пожалуйста, выберите другой.')
                messages.error(request, '❌ Ошибка: логин уже занят.')
        # Если форма невалидна или ошибка IntegrityError — показываем форму с ошибками
    else:
        form = MyRegistrationForm()

    return render(request, 'register.html', {'form': form})


@login_required
def profile_view(request):
    return render(request, 'profile.html', {'user': request.user})


@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        user = request.user


        user.full_name = request.POST.get('full_name', '')
        user.phone = request.POST.get('phone', '')
        user.email = request.POST.get('email', '')
        user.address = request.POST.get('address', '')

        if request.POST.get('birth_date'):
            user.birth_date = request.POST.get('birth_date')

        if user.role == 'driver':
            full_plate = request.POST.get('full_license_plate', '').upper().strip()

            if full_plate:
                import re
                pattern = r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$'
                if re.match(pattern, full_plate):
                    user.full_license_plate = full_plate
                    messages.success(request, f'Госномер {full_plate} сохранен!')
                else:
                    messages.error(request, f'Неверный формат госномера: {full_plate}. Пример: А945ОА25')
            else:
                user.full_license_plate = ''

            user.car_brand = request.POST.get('car_brand', '')
            user.car_model = request.POST.get('car_model', '')
            user.car_year = request.POST.get('car_year', '') or None
            user.vin_number = request.POST.get('vin_number', '')

        user.save()
        messages.success(request, '✅ Профиль успешно обновлен!')
        return redirect('profile')

    return render(request, 'edit_profile.html')



@login_required
def fine_detail_view(request, pk):
    fine = get_object_or_404(Violation, pk=pk)

    if request.user.role == 'driver':
        driver_plate = request.user.full_license_plate

        print(f"DEBUG: Номер водителя: {driver_plate}")
        print(f"DEBUG: Номер в нарушении: {fine.car_plate}")

        if not driver_plate:
            messages.error(request, '❌ В вашем профиле не указан госномер')
            return redirect('my_violations')

        if fine.car_plate.upper() != driver_plate.upper():
            messages.error(request, '❌ У вас нет доступа к этому штрафу')
            return redirect('my_violations')

    return render(request, 'fine_detail.html', {'fine': fine})

@login_required
def get_driver_by_plate(request):
    car_plate = request.GET.get('car_plate', '').upper().strip()

    if not car_plate:
        return JsonResponse({'found': False, 'message': 'Введите госномер'})

    driver = User.objects.filter(
        role='driver',
        license_plate__iexact=car_plate
    ).first()

    if driver:
        data = {
            'found': True,
            'driver_id': driver.id,
            'driver_name': driver.full_name,
            'car_brand': driver.car_brand or '',
            'car_model': driver.car_model or '',
            'vin': driver.vin_number or '',
            'license_plate': driver.license_plate,
            'message': f'Найден водитель: {driver.full_name}'
        }
    else:
        data = {
            'found': False,
            'message': f'Водитель с номером {car_plate} не найден. Заполните данные вручную.'
        }

    return JsonResponse(data)


@login_required
def get_driver_details(request):
    driver_id = request.GET.get('driver_id')

    if not driver_id:
        return JsonResponse({'found': False, 'message': 'ID водителя не указан'})

    try:
        driver = User.objects.get(id=driver_id, role='driver')
        data = {
            'found': True,
            'car_brand': driver.car_brand or '',
            'car_model': driver.car_model or '',
            'vin': driver.vin_number or '',
            'license_plate': driver.license_plate or '',
            'full_name': driver.full_name,
        }
    except User.DoesNotExist:
        data = {'found': False, 'message': 'Водитель не найден'}

    return JsonResponse(data)


@login_required
def create_violation(request):

    if request.user.role not in ['inspector', 'manager']:
        messages.error(request, '❌ У вас нет прав на создание нарушений.')
        return redirect('home')

    if request.user.role == 'inspector' and request.user.is_dismissed:
        messages.error(request, '🔒 Вы уволены и не можете создавать нарушения.')
        return redirect('inspector_dismissed_page')

    if request.method == 'POST':
        form = ViolationForm(request.POST, request.FILES, inspector=request.user)

        if request.user.role == 'inspector' and request.user.is_dismissed:
            messages.error(request, '🔒 Вы уволены. Действие отменено.')
            return redirect('inspector_dismissed_page')

        if form.is_valid():
            violation = form.save(commit=False)
            violation.inspector = request.user

            violation_time = request.POST.get('violation_datetime')
            if violation_time:
                try:
                    naive_time = datetime.datetime.strptime(violation_time, '%Y-%m-%dT%H:%M')
                    violation.violation_datetime = timezone.make_aware(naive_time)  # ← СЮДА!
                except ValueError:
                    pass

            violation.save()

            messages.success(request, f'✅ Нарушение #{violation.id} успешно зарегистрировано!')

            if 'save_and_print' in request.POST:
                return redirect('violation_print', pk=violation.pk)
            elif 'create_another' in request.POST:
                messages.info(request, 'Заполните данные для следующего нарушения.')
                return redirect('create_violation')
            else:
                return redirect('home')
        else:
            messages.error(request, '❌ Исправьте ошибки в форме.')
            return render(request, 'create_violation.html', {
                'form': form,
                'current_time': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            })
    else:
        form = ViolationForm(inspector=request.user)
        current_time = timezone.now().strftime('%Y-%m-%dT%H:%M')
        return render(request, 'create_violation.html', {
            'form': form,
            'current_time': current_time,
        })

@login_required
def violation_print(request, pk):
    violation = get_object_or_404(Violation, pk=pk)

    if request.user.role not in ['inspector', 'manager']:
        messages.error(request, '❌ У вас нет прав на печать протоколов.')
        return redirect('home')

    context = {
        'violation': violation,
        'now': timezone.now(),
    }
    return render(request, 'inspector/violation_print.html', {'violation': violation})



@login_required
def inspector_dashboard(request):
    if request.user.role != 'inspector':
        messages.error(request, 'Доступ запрещен. Только для инспекторов.')
        return redirect('home')

    if request.user.is_dismissed:
        return render(request, 'inspector/dismissed_page.html', {
            'dismissed_by': request.user.dismissed_by,
            'dismissed_at': request.user.dismissed_at,
        })

    today_violations = Violation.objects.filter(
        inspector=request.user,
        created_at__date=timezone.now().date()
    ).count()

    week_violations = Violation.objects.filter(
        inspector=request.user,
        created_at__gte=timezone.now() - timedelta(days=7)
    ).count()

    total_fines = Violation.objects.filter(
        inspector=request.user
    ).aggregate(total=Sum('amount'))['total'] or 0

    recent_violations = Violation.objects.filter(
        inspector=request.user
    ).order_by('-created_at')[:10]

    hour_stats = Violation.objects.filter(
        inspector=request.user
    ).extra(
        {'hour': "strftime('%%H', created_at)"}
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('-count')

    max_hour = hour_stats.first() if hour_stats else None

    top_districts = Violation.objects.filter(
        inspector=request.user
    ).values('place').annotate(
        count=Count('id')
    ).order_by('-count')[:5]

    context = {
        'today_violations': today_violations,
        'week_violations': week_violations,
        'total_fines': total_fines,
        'recent_violations': recent_violations,
        'max_hour': max_hour,
        'top_districts': top_districts,
    }

    return render(request, 'inspector/dashboard.html', context)


@login_required
def inspector_dismissed_page(request):
    context = {
        'dismissed_by': request.user.dismissed_by,
        'dismissed_at': request.user.dismissed_at,
        'message': 'Вы уволены. Доступ к созданию нарушений закрыт.'
    }
    return render(request, 'inspector/dismissed_page.html', context)


# ПАНЕЛЬ РУКОВОДИТЕЛЯ

@login_required
@user_passes_test(is_manager)
def manager_dashboard(request):
    total_violations = Violation.objects.count()
    today_violations = Violation.objects.filter(created_at__date=timezone.now().date()).count()
    week_violations = Violation.objects.filter(created_at__gte=timezone.now() - timedelta(days=7)).count()
    total_fines = Violation.objects.aggregate(total=Sum('amount'))['total'] or 0
    active_inspectors = User.objects.filter(role='inspector', is_dismissed=False).count()
    dismissed_inspectors = User.objects.filter(role='inspector', is_dismissed=True).count()


    top_violations = Violation.objects.values('article').annotate(count=Count('id')).order_by('-count')[:5]

    context = {
        'total_violations': total_violations,
        'today_violations': today_violations,
        'week_violations': week_violations,
        'total_fines': total_fines,
        'active_inspectors': active_inspectors,
        'dismissed_inspectors': dismissed_inspectors,
        'top_violations': top_violations,
    }
    return render(request, 'manager/dashboard.html', context)


@login_required
@user_passes_test(is_manager)
def inspector_list(request):
    inspectors = User.objects.filter(role='inspector').annotate(
        violations_count=Count('registered_violations')
    ).order_by('-is_dismissed', '-date_joined')
    return render(request, 'manager/inspector_list.html', {'inspectors': inspectors})


@login_required
@user_passes_test(is_manager)
def inspector_detail(request, inspector_id):
    inspector = get_object_or_404(User, id=inspector_id, role='inspector')
    violations = Violation.objects.filter(inspector=inspector).order_by('-created_at')
    return render(request, 'manager/inspector_detail.html', {'inspector': inspector, 'violations': violations})


@login_required
@user_passes_test(is_manager)
def dismiss_inspector(request, inspector_id):
    inspector = get_object_or_404(User, id=inspector_id, role='inspector')

    if request.method == 'POST':
        if inspector.is_dismissed:
            messages.warning(request, f'⚠️ Инспектор {inspector.full_name} уже уволен')
        else:
            inspector.is_dismissed = True
            inspector.dismissed_at = timezone.now()
            inspector.dismissed_by = request.user
            inspector.save()
            messages.success(request, f'✅ Инспектор {inspector.full_name} уволен.')

        return redirect('manager_inspector_list')

    return render(request, 'manager/dismiss_inspector_confirm.html', {'inspector': inspector})


@login_required
@user_passes_test(is_manager)
def reinstate_inspector(request, inspector_id):
    inspector = get_object_or_404(User, id=inspector_id, role='inspector')

    if request.method == 'POST':
        if not inspector.is_dismissed:
            messages.warning(request, f'⚠️ Инспектор {inspector.full_name} не был уволен')
        else:
            inspector.is_dismissed = False
            inspector.dismissed_at = None
            inspector.dismissed_by = None
            inspector.save()
            messages.success(request, f'✅ Инспектор {inspector.full_name} восстановлен.')

        return redirect('manager_inspector_list')

    return render(request, 'manager/reinstate_inspector_confirm.html', {'inspector': inspector})


@login_required
@user_passes_test(is_manager)
def violations_stats(request):
    daily_stats = Violation.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).annotate(date=TruncDate('created_at')).values('date').annotate(
        count=Count('id'), total_amount=Sum('amount')
    ).order_by('date')

    article_stats = Violation.objects.values('article').annotate(
        count=Count('id'), total_amount=Sum('amount')
    ).order_by('-count')[:15]

    context = {
        'daily_stats': daily_stats,
        'article_stats': article_stats,
        'total_violations': Violation.objects.count(),
        'total_fines': Violation.objects.aggregate(total=Sum('amount'))['total'] or 0,
    }
    return render(request, 'manager/violations_stats.html', context)


@login_required
@user_passes_test(is_manager)
def inspectors_stats(request):
    inspectors = User.objects.filter(role='inspector').annotate(
        violations_count=Count('registered_violations'),
        fines_sum=Sum('registered_violations__amount'),
    ).order_by('-violations_count')
    return render(request, 'manager/inspectors_stats.html', {'inspectors': inspectors})


@login_required
@user_passes_test(is_manager)
def top_violators_report(request):
    period = request.GET.get('period', 'month')

    if period == 'week':
        date_from = timezone.now() - timedelta(days=7)
    elif period == 'month':
        date_from = timezone.now() - timedelta(days=30)
    elif period == 'year':
        date_from = timezone.now() - timedelta(days=365)
    else:
        date_from = timezone.now() - timedelta(days=30)

    top_violators = Violation.objects.filter(
        created_at__gte=date_from
    ).values('car_plate').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    ).filter(count__gte=1).order_by('-count')[:20]

    for violator in top_violators:

        user = User.objects.filter(
            role='driver',
            full_license_plate=violator['car_plate']
        ).first()

        if user:
            violator['full_name'] = user.full_name
            violator['phone'] = user.phone
        else:
            violator['full_name'] = 'Не зарегистрирован'
            violator['phone'] = '-'

    context = {
        'top_violators': top_violators,
        'period': period,
        'date_from': date_from,
    }
    return render(request, 'manager/top_violators.html', context)


@login_required
@user_passes_test(is_manager)
def violations_by_article_report(request):
    from .models import ArticleCoAP

    period = request.GET.get('period', 'month')

    if period == 'week':
        date_from = timezone.now() - timedelta(days=7)
    elif period == 'month':
        date_from = timezone.now() - timedelta(days=30)
    else:
        date_from = timezone.now() - timedelta(days=365)

    articles_stats = Violation.objects.filter(
        created_at__gte=date_from
    ).values('article').annotate(
        count=Count('id'),
        total_amount=Sum('amount'),
        paid_count=Count('id', filter=Q(status='paid'))
    ).order_by('-count')

    for stat in articles_stats:
        article = ArticleCoAP.objects.filter(article_number=stat['article']).first()
        if article:
            stat['description'] = article.description
            stat['fine_amount'] = article.fine_amount

    context = {
        'articles_stats': articles_stats,
        'period': period,
        'date_from': date_from,
        'total_count': sum(stat['count'] for stat in articles_stats),
        'total_amount': sum(stat.get('total_amount', 0) or 0 for stat in articles_stats),
    }
    return render(request, 'manager/violations_by_article.html', context)


@login_required
def my_violations_view(request):
    driver_plate = request.user.full_license_plate

    print("=" * 50)
    print(f"1. Номер водителя из профиля: '{driver_plate}'")
    print(f"2. Тип номера водителя: {type(driver_plate)}")

    if not driver_plate:
        messages.warning(request, '⚠️ В вашем профиле не указан госномер автомобиля.')
        return render(request, 'driver/my_violations.html', {'violations': [], 'no_plate': True})

    all_plates = Violation.objects.values_list('car_plate', flat=True).distinct()
    print(f"3. Все номера в таблице нарушений: {list(all_plates)}")

    violations = Violation.objects.filter(car_plate__icontains=driver_plate.strip())

    print(f"4. SQL запрос: {str(violations.query)}")
    print(f"5. Найдено нарушений: {violations.count()}")

    for v in violations:
        print(f"   - Штраф #{v.id}: car_plate='{v.car_plate}'")

    for v in violations:
        appeal_deadline = v.created_at.date() + timedelta(days=10)
        v.days_left_to_appeal = max(0, (appeal_deadline - date.today()).days)

        discount_deadline = v.created_at.date() + timedelta(days=20)
        v.days_left_for_discount = max(0, (discount_deadline - date.today()).days)

        if v.discount_until and v.discount_until >= date.today() and v.status == 'registered':
            v.has_discount = True
            v.discount_amount = v.amount * 0.5
        else:
            v.has_discount = False

    context = {
        'violations': violations,
        'total_amount': violations.aggregate(total=Sum('amount'))['total'] or 0,
        'unpaid_count': violations.filter(status='registered').count(),
        'paid_count': violations.filter(status='paid').count(),
        'my_license_plate': driver_plate,
    }

    print(f"6. Количество violations в контексте: {len(context['violations'])}")
    print("=" * 50)

    return render(request, 'driver/my_violations.html', context)
@login_required
def check_debt_status(request):
    driver_plate = request.user.license_plate

    if not driver_plate:
        return JsonResponse({'error': 'Госномер не указан'}, status=400)

    violations = Violation.objects.filter(car_plate__iexact=driver_plate)

    total_debt = violations.filter(status='registered').aggregate(total=Sum('amount'))['total'] or 0
    expiring_discount = violations.filter(
        status='registered',
        discount_until__isnull=False,
        discount_until__lte=date.today() + timedelta(days=7),
        discount_until__gte=date.today()
    ).count()

    return JsonResponse({
        'total_debt': float(total_debt),
        'unpaid_count': violations.filter(status='registered').count(),
        'expiring_discount_count': expiring_discount,
    })


@login_required
def get_notifications(request):
    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')

    notifications.update(is_read=True)
    all_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'driver/notifications.html', {'notifications': all_notifications})


@login_required
def generate_certificate(request):
    if request.method == 'POST':
        date_from = request.POST.get('date_from')
        date_to = request.POST.get('date_to')
        report_type = request.POST.get('report_type', 'certificate')

        today = date.today()

        if date_from:
            date_from_obj = datetime.datetime.strptime(date_from, '%Y-%m-%d').date()
            if date_from_obj > today:
                messages.error(request, 'Дата начала не может быть в будущем!')
                return render(request, 'driver/generate_certificate.html', {'today': today.isoformat()})

        if date_to:
            date_to_obj = datetime.datetime.strptime(date_to, '%Y-%m-%d').date()
            if date_to_obj > today:
                messages.error(request, 'Дата окончания не может быть в будущем!')
                return render(request, 'driver/generate_certificate.html', {'today': today.isoformat()})

        if date_from and date_to:
            if date_from_obj > date_to_obj:
                messages.error(request, 'Дата начала не может быть позже даты окончания!')
                return render(request, 'driver/generate_certificate.html', {'today': today.isoformat()})

        driver_plate = request.user.full_license_plate

        if not driver_plate:
            messages.error(request, '❌ В вашем профиле не указан госномер автомобиля.')
            return redirect('profile')

        violations = Violation.objects.filter(
            car_plate__iexact=driver_plate,
            created_at__date__gte=date_from,
            created_at__date__lte=date_to
        ).order_by('-created_at')

        if not violations.exists():
            messages.warning(request, f'⚠️ За период с {date_from} по {date_to} нарушений не найдено.')
            return render(request, 'driver/certificate_result.html', {
                'violations': [],
                'user': request.user,
                'date_from': date_from,
                'date_to': date_to,
                'total_amount': 0,
                'no_violations': True
            })

        total_amount = violations.aggregate(total=Sum('amount'))['total'] or 0

        violations_data = []
        for v in violations:
            violations_data.append({
                'id': v.id,
                'article': v.article,
                'amount': float(v.amount),
                'created_at': v.created_at.isoformat(),
                'status': v.status
            })

        ViolationReport.objects.create(
            user=request.user,
            report_type=report_type,
            date_from=date_from,
            date_to=date_to,
            data={
                'violations_count': violations.count(),
                'total_amount': float(total_amount),
                'violations': violations_data
            }
        )

        return render(request, 'driver/certificate_result.html', {
            'violations': violations,
            'user': request.user,
            'date_from': date_from,
            'date_to': date_to,
            'total_amount': total_amount,
            'report_type': report_type,
        })

    return render(request, 'driver/generate_certificate.html')


@login_required
@user_passes_test(is_manager)
def manage_articles(request):
    from .models import ArticleCoAP
    from django.db import IntegrityError

    articles = ArticleCoAP.objects.all()

    if request.method == 'POST':
        article_id = request.POST.get('article_id')
        article_number = request.POST.get('article_number', '').strip()
        description = request.POST.get('description', '').strip()
        fine_amount = request.POST.get('fine_amount', '').strip()

        # Проверка на пустые поля
        if not article_number:
            messages.error(request, '❌ Номер статьи не может быть пустым!')
            return redirect('manage_articles')

        if not fine_amount:
            messages.error(request, '❌ Сумма штрафа не может быть пустой!')
            return redirect('manage_articles')

        try:
            fine_amount = float(fine_amount)
        except ValueError:
            messages.error(request, '❌ Сумма штрафа должна быть числом!')
            return redirect('manage_articles')

        if article_id:
            # Редактирование существующей статьи
            article = get_object_or_404(ArticleCoAP, id=article_id)

            # Проверяем, не занят ли номер другой статьёй
            if ArticleCoAP.objects.filter(article_number=article_number).exclude(id=article_id).exists():
                messages.error(request, f'❌ Статья с номером "{article_number}" уже существует!')
                return redirect('manage_articles')

            article.article_number = article_number
            article.description = description
            article.fine_amount = fine_amount
            article.save()
            messages.success(request, f'✅ Статья {article_number} обновлена')
        else:
            # Добавление новой статьи
            try:
                ArticleCoAP.objects.create(
                    article_number=article_number,
                    description=description,
                    fine_amount=fine_amount
                )
                messages.success(request, f'✅ Статья {article_number} добавлена')
            except IntegrityError:
                messages.error(request, f'❌ Статья с номером "{article_number}" уже существует!')

        return redirect('manage_articles')

    return render(request, 'manager/manage_articles.html', {'articles': articles})


@login_required
@user_passes_test(is_manager)
def delete_article(request, article_id):
    from .models import ArticleCoAP

    article = get_object_or_404(ArticleCoAP, id=article_id)
    article.delete()
    messages.success(request, f'Статья {article.article_number} удалена')
    return redirect('manage_articles')


@login_required
@user_passes_test(is_manager)
def inspector_detail_page(request, inspector_id):
    inspector = get_object_or_404(User, id=inspector_id, role='inspector')

    # Все нарушения инспектора
    all_violations = Violation.objects.filter(inspector=inspector)

    # Статистика
    total = all_violations.count()
    today = all_violations.filter(created_at__date=timezone.now().date()).count()
    week = all_violations.filter(created_at__gte=timezone.now() - timedelta(days=7)).count()
    total_fines = all_violations.aggregate(Sum('amount'))['amount__sum'] or 0

    stats = {
        'total_violations': total,
        'today_violations': today,
        'week_violations': week,
        'total_fines': total_fines,
    }

    violations = all_violations.order_by('-created_at')

    context = {
        'inspector': inspector,
        'stats': stats,
        'violations': violations,
    }

    # ВОТ ТУТ БЫЛО НЕПРАВИЛЬНО! Было HttpResponse, а нужно render
    return render(request, 'manager/inspector_detail.html', context)