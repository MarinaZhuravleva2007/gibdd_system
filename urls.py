from django.urls import path
from . import views

urlpatterns = [
    # Главная
    path('', views.home_view, name='home'),

    # Страницы ПДД и штрафов
    path('pdd-rules/', views.pdd_rules_view, name='pdd_rules'),
    path('fines-info/', views.fines_info_view, name='fines_info'),
    path('payment-info/', views.payment_info_view, name='payment_info'),
    path('contacts/', views.contacts_view, name='contacts'),

    # Регистрация и профиль
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),

    # Нарушения
    path('violations/my/', views.my_violations_view, name='my_violations'),
    path('violation/<int:pk>/', views.fine_detail_view, name='fine_detail'),
    path('violation/create/', views.create_violation, name='create_violation'),
    path('violation/print/<int:pk>/', views.violation_print, name='violation_print'),
    path('inspector/top-districts/', views.top_districts_report, name='top_districts_report'),

    # Для водителя
    path('driver/notifications/', views.get_notifications, name='get_notifications'),
    path('driver/certificate/', views.generate_certificate, name='generate_certificate'),
    path('driver/debt-status/', views.check_debt_status, name='check_debt_status'),

    # Для инспектора
    path('inspector/dashboard/', views.inspector_dashboard, name='inspector_dashboard'),
    path('inspector/dismissed/', views.inspector_dismissed_page, name='inspector_dismissed_page'),


    path('manager/dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/inspectors/', views.inspector_list, name='manager_inspector_list'),
    path('manager/inspector/<int:inspector_id>/', views.inspector_detail_page, name='manager_inspector_detail'),
    path('manager/inspector/<int:inspector_id>/dismiss/', views.dismiss_inspector, name='manager_dismiss_inspector'),
    path('manager/inspector/<int:inspector_id>/reinstate/', views.reinstate_inspector,
         name='manager_reinstate_inspector'),
    path('manager/stats/', views.violations_stats, name='manager_violations_stats'),
    path('manager/inspectors-stats/', views.inspectors_stats, name='manager_inspectors_stats'),
    path('manager/top-violators/', views.top_violators_report, name='manager_top_violators'),
    path('manager/by-article/', views.violations_by_article_report, name='manager_violations_by_article'),
    path('manager/articles/', views.manage_articles, name='manage_articles'),
    path('manager/articles/delete/<int:article_id>/', views.delete_article, name='delete_article'),


    # AJAX-запросы
    path('api/get-driver-by-plate/', views.get_driver_by_plate, name='get_driver_by_plate'),
    path('api/get-driver-details/', views.get_driver_details, name='get_driver_details'),
    path('api/get-fine-articles/', views.get_fine_articles, name='get_fine_articles'),
    path('api/unread-notifications/', views.unread_notifications_count, name='unread_notifications'),

]