from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Violation, ViolationPhoto, Vehicle, ArticleCoAP, Notification, ViolationReport

class DriverFilter(admin.SimpleListFilter):
    title = 'Категория пользователя'
    parameter_name = 'user_category'

    def lookups(self, request, model_admin):
        return (
            ('all', 'Все пользователи'),
            ('drivers', 'Только водители'),
            ('inspectors', 'Только инспекторы'),
            ('managers', 'Только руководители'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'drivers':
            return queryset.filter(role='driver')
        if self.value() == 'inspectors':
            return queryset.filter(role='inspector')
        if self.value() == 'managers':
            return queryset.filter(role='manager')
        return queryset


class VehicleInline(admin.TabularInline):
    """Встроенное отображение ТС в профиле пользователя"""
    model = Vehicle
    extra = 0
    fields = ('license_plate', 'brand', 'model', 'vin', 'year', 'is_active')
    readonly_fields = ('created_at',)


class CustomUserAdmin(UserAdmin):
    """Кастомизация отображения пользователей в админке с разделением по ролям"""

    # Список отображаемых полей
    list_display = (
        'username', 'full_name', 'role_badge', 'phone', 'license_plate', 'violations_count', 'vehicles_count', 'is_active', 'is_dismissed'
    )
    list_filter = (DriverFilter, 'role', 'is_dismissed', 'is_active', 'date_joined')
    search_fields = ('username', 'full_name', 'phone', 'license_plate', 'service_id')
    list_per_page = 20
    inlines = [VehicleInline]

    # Действия
    actions = ['make_active', 'make_inactive', 'dismiss_selected']

    def role_badge(self, obj):
        """Цветная метка роли"""
        colors = {
            'driver': '#28a745',
            'inspector': '#007bff',
            'manager': '#6f42c1'
        }
        names = {
            'driver': '🚗 Водитель',
            'inspector': '👮 Инспектор',
            'manager': '👔 Руководитель'
        }
        color = colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 15px; font-size: 12px;">{}</span>',
            color, names.get(obj.role, obj.role)
        )

    role_badge.short_description = 'Роль'

    def violations_count(self, obj):
        """Количество нарушений (для водителя)"""
        count = obj.violations.count()
        if count > 0:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', count)
        return format_html('<span style="color: green;">0</span>')

    violations_count.short_description = 'Нарушений'

    def vehicles_count(self, obj):
        count = obj.vehicles.count()
        if count > 0:
            return format_html('<span style="color: #28a745;">{} ТС</span>', count)
        return '0 ТС'

    vehicles_count.short_description = 'Транспорт'

    def make_active(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, 'Выбранные пользователи активированы')

    make_active.short_description = 'Активировать выбранных пользователей'

    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, 'Выбранные пользователи деактивированы')

    make_inactive.short_description = 'Деактивировать выбранных пользователей'

    def dismiss_selected(self, request, queryset):
        from django.utils import timezone
        for user in queryset.filter(role='inspector'):
            user.is_dismissed = True
            user.dismissed_at = timezone.now()
            user.save()
        self.message_user(request, 'Выбранные инспекторы уволены')

    dismiss_selected.short_description = 'Уволить выбранных инспекторов'

    # Поля для отображения в форме редактирования
    fieldsets = UserAdmin.fieldsets + (
        ('Личная информация', {
            'fields': ('full_name', 'phone', 'birth_date', 'address'),
            'classes': ('wide',)
        }),
        ('Данные автомобиля', {
            'fields': ('car_brand', 'car_model', 'car_categories', 'vin_number', 'car_year'),
            'classes': ('collapse',)
        }),
        ('Госномер', {
            'fields': ('country', 'license_plate', 'car_region'),
            'classes': ('collapse',)
        }),
        ('Служебная информация', {
            'fields': ('role', 'service_id'),
            'classes': ('wide',)
        }),
        ('Управление статусом', {
            'fields': ('is_dismissed', 'dismissed_at', 'dismissed_by'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Личная информация', {
            'fields': ('full_name', 'phone', 'birth_date', 'address')
        }),
        ('Роль', {
            'fields': ('role',)
        }),
    )



class ViolationPhotoInline(admin.TabularInline):
    model = ViolationPhoto
    extra = 1
    fields = ('photo', 'description', 'uploaded_at', 'uploaded_by')
    readonly_fields = ('uploaded_at',)



@admin.register(Violation)
class ViolationAdmin(admin.ModelAdmin):
    list_display = ('id', 'car_plate', 'article', 'amount', 'status', 'inspector', 'driver_info', 'created_at')
    list_filter = ('status', 'article', 'created_at', 'inspector')
    search_fields = ('car_plate', 'article', 'fine_number', 'place', 'vin')
    readonly_fields = ('created_at',)  # Убрал updated_at, если его нет в модели
    inlines = [ViolationPhotoInline]
    list_per_page = 20

    def driver_info(self, obj):
        if obj.driver:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.driver.full_name or obj.driver.username,
                obj.driver.phone or 'нет телефона'
            )
        return '-'

    driver_info.short_description = 'Водитель'

    fieldsets = (
        ('Основная информация', {
            'fields': ('car_plate', 'car_brand_model', 'vin', 'article', 'place', 'amount', 'fine_number')
        }),
        ('Статус и описание', {
            'fields': ('status', 'description')
        }),
        ('Связи', {
            'fields': ('driver', 'inspector')
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )



@admin.register(ViolationPhoto)
class ViolationPhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'violation_info', 'photo_preview', 'uploaded_at', 'uploaded_by')
    list_filter = ('uploaded_at',)
    search_fields = ('violation__car_plate', 'description')
    readonly_fields = ('uploaded_at',)

    def violation_info(self, obj):
        return f"Нарушение #{obj.violation.id} - {obj.violation.car_plate}"

    violation_info.short_description = 'Нарушение'

    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />',
                               obj.photo.url)
        return '-'

    photo_preview.short_description = 'Превью'



@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    """Администрирование транспортных средств"""

    list_display = ('license_plate', 'brand', 'model', 'owner_info', 'year', 'vin_short', 'is_active')
    list_filter = ('brand', 'is_active', 'year')
    search_fields = ('license_plate', 'brand', 'model', 'vin', 'owner__full_name', 'owner__username')
    list_editable = ('is_active',)
    list_per_page = 20

    fieldsets = (
        ('Основная информация', {
            'fields': ('license_plate', 'brand', 'model', 'year', 'color')
        }),
        ('Технические данные', {
            'fields': ('vin', 'category')
        }),
        ('Владелец', {
            'fields': ('owner',)
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
    )

    def owner_info(self, obj):
        if obj.owner:
            return format_html(
                '<strong>{}</strong><br><small style="color: #6c757d;">тел: {}</small>',
                obj.owner.full_name or obj.owner.username,
                obj.owner.phone or '-'
            )
        return '-'

    owner_info.short_description = 'Владелец'

    def vin_short(self, obj):
        if obj.vin:
            return obj.vin[:10] + '...' if len(obj.vin) > 10 else obj.vin
        return '-'

    vin_short.short_description = 'VIN'



@admin.register(ArticleCoAP)
class ArticleCoAPAdmin(admin.ModelAdmin):
    list_display = ('article_number', 'description_short', 'fine_amount', 'penalty_points', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('article_number', 'description')
    list_editable = ('fine_amount', 'penalty_points', 'is_active')
    list_per_page = 20

    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description

    description_short.short_description = 'Описание'



@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user_info', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__full_name')
    readonly_fields = ('created_at',)

    def user_info(self, obj):
        return obj.user.full_name or obj.user.username

    user_info.short_description = 'Пользователь'


@admin.register(ViolationReport)
class ViolationReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'report_type', 'date_from', 'date_to', 'created_at')
    list_filter = ('report_type', 'created_at')
    search_fields = ('user__full_name',)
    readonly_fields = ('created_at',)


admin.site.register(User, CustomUserAdmin)