from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from accounts import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # Основные страницы
    path('', views.home_view, name='home'),
    path('pdd-rules/', views.pdd_rules_view, name='pdd_rules'),
    path('fines-info/', views.fines_info_view, name='fines_info'),
    path('payment-info/', views.payment_info_view, name='payment_info'),
    path('contacts/', views.contacts_view, name='contacts'),

    # Профиль пользователя
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('fine/<int:pk>/', views.fine_detail_view, name='fine_detail'),

    # Нарушения
    path('violation/new/', views.create_violation, name='create_violation'),
    path('violation/print/<int:pk>/', views.violation_print, name='violation_print'),
    path('my-violations/', views.my_violations_view, name='my_violations'),
    path('inspector/top-districts/', views.top_districts_report, name='top_districts_report'),

    # Для руководителя
    path('manager/dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/inspectors/', views.inspector_list, name='manager_inspector_list'),

    path('manager/inspector/<int:inspector_id>/', views.inspector_detail_page, name='manager_inspector_detail'),

    path('manager/inspector/<int:inspector_id>/dismiss/', views.dismiss_inspector, name='manager_dismiss_inspector'),
    path('manager/inspector/<int:inspector_id>/reinstate/', views.reinstate_inspector,
         name='manager_reinstate_inspector'),
    path('manager/violations-stats/', views.violations_stats, name='manager_violations_stats'),
    path('manager/inspectors-stats/', views.inspectors_stats, name='manager_inspectors_stats'),
    path('manager/articles/', views.manage_articles, name='manage_articles'),
    path('manager/articles/delete/<int:article_id>/', views.delete_article, name='delete_article'),
    path('manager/top-violators/', views.top_violators_report, name='top_violators'),
    path('manager/by-article/', views.violations_by_article_report, name='violations_by_article'),

    # Для инспектора
    path('inspector/dashboard/', views.inspector_dashboard, name='inspector_dashboard'),
    path('inspector/dismissed/', views.inspector_dismissed_page, name='inspector_dismissed_page'),

    # Доп функции
    path('check-debt/', views.check_debt_status, name='check_debt_status'),
    path('notifications/', views.get_notifications, name='notifications'),
    path('generate-certificate/', views.generate_certificate, name='generate_certificate'),

    # Восстановление пароля
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)