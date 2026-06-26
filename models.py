from random import random
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import RegexValidator
plate_regex = RegexValidator(
     regex=r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}$',
     message="Номер должен быть в формате: А111АА (используются только буквы, совпадающие по начертанию с латиницей: А, В, Е, К, М, Н, О, Р, С, Т, У, Х)"
 )
class User(AbstractUser):
    ROLE_CHOICES = (
        ('driver', 'Водитель'),
        ('inspector', 'Инспектор ДПС'),
        ('manager', 'Руководитель'),
    )
    full_license_plate = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name='Госномер ТС'
    )
    driver_license_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Номер водительского удостоверения',
        db_index=True
    )
    driver_license_issued = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата выдачи ВУ'
    )
    driver_license_expires = models.DateField(
        null=True,
        blank=True,
        verbose_name='Срок действия ВУ'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='driver')
    full_name = models.CharField(max_length=255, verbose_name='ФИО')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    birth_date = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    car_brand = models.CharField(max_length=100, blank=True)
    car_model = models.CharField(max_length=100, blank=True)
    car_categories = models.CharField(max_length=50, blank=True)
    vin_number = models.CharField(max_length=17, blank=True)
    car_year = models.IntegerField(null=True, blank=True)
    country = models.CharField(max_length=10, default='RUS')
    license_plate = models.CharField(max_length=10, blank=True)
    car_region = models.CharField(max_length=5, blank=True)
    service_id = models.CharField(max_length=20, blank=True)
    is_dismissed = models.BooleanField(default=False)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    dismissed_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.full_name or self.username

class FineArticle(models.Model):
    number = models.CharField(max_length=20, verbose_name='Статья КоАП')
    description = models.TextField(verbose_name='Описание нарушения')
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма штрафа')

    def __str__(self):
        return f"{self.number} - {self.cost} руб."

class Violation(models.Model):
    STATUS_CHOICES = (
        ('registered', 'Зарегистрировано'),
        ('paid', 'Оплачено'),
        ('appealed', 'Обжаловано'),
    )
    car_plate = models.CharField(
        max_length=15,
        verbose_name='Госномер ТС',
        validators=[]
    )
    discount_until = models.DateField(
        null=True,
        blank=True,
        verbose_name='Срок действия скидки 50%'
    )
    notification_sent = models.BooleanField(
        default=False,
        verbose_name='Уведомление отправлено'
    )
    vehicle = models.ForeignKey(
        'Vehicle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='violations',
        verbose_name='Транспортное средство'
    )
    inspector_comment = models.TextField(
        blank=True,
        verbose_name='Комментарий инспектора'
    )
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='violations', null=True, blank=True)
    inspector = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registered_violations')
    car_brand_model = models.CharField(max_length=255, verbose_name='Марка/модель')
    vin = models.CharField(max_length=17, blank=True, verbose_name='VIN')
    article = models.CharField(max_length=50, verbose_name='Статья КоАП')
    place = models.CharField(max_length=255, verbose_name='Место')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма')
    evidence_img = models.ImageField(upload_to='evidence/', blank=True, null=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='registered')
    violation_datetime = models.DateTimeField(
        verbose_name='Дата и время нарушения',
        null=True,
        blank=True,
        help_text='Укажите дату и время совершения нарушения'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    fine_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=False,  # Убираем unique
        db_index=True,  # Добавляем индекс для быстрого поиска
        verbose_name='Номер постановления'
    )

    def save(self, *args, **kwargs):
        # Генерируем номер постановления если его нет
        if not self.fine_number:
            import random
            # Генерируем уникальный 6-значный номер
            while True:
                new_number = str(random.randint(100000, 999999))
                if not Violation.objects.filter(fine_number=new_number).exists():
                    self.fine_number = new_number
                    break
        super().save(*args, **kwargs)
    def __str__(self):
        return f"Нарушение #{self.id} - {self.car_plate} - {self.article}"


    @property
    def full_plate(self):
        """Возвращает полный номер (серия + регион)"""
        return f"{self.car_plate}"

    def clean(self):
        """Валидация полного госномера"""
        from django.core.exceptions import ValidationError
        import re

        # Если оба поля пустые - пропускаем
        if not self.car_plate:
            return

        # Если нет серии номера - ошибка
        if not self.car_plate:
            raise ValidationError({'car_plate': 'Введите серию госномера (например: А945ОА)'})

        full = self.full_plate
        pattern = r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$'

        if not re.match(pattern, full):
            raise ValidationError(
                f'Неверный формат госномера "{full}". '
                f'Примеры: А123ВС777, В543ОР99, М777АА178'
            )

        @property
        def plate_series(self):
            """Возвращает серию номера (без региона)"""
            import re
            pattern = r'^([АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2})'
            match = re.match(pattern, self.car_plate)
            return match.group(1) if match else self.car_plate

        @property
        def plate_region(self):
            """Возвращает регион (последние 2-3 цифры)"""
            import re
            pattern = r'(\d{2,3})$'
            match = re.search(pattern, self.car_plate)
            return match.group(1) if match else ''
    def save(self, *args, **kwargs):
        # Вызываем валидацию перед сохранением
        self.clean()
        super().save(*args, **kwargs)


class Notification(models.Model):
    """Модель уведомлений для водителей"""
    NOTIFICATION_TYPES = (
        ('new_violation', 'Новое нарушение'),
        ('discount_expiring', 'Истекает срок скидки'),
        ('payment_reminder', 'Напоминание об оплате'),
        ('status_changed', 'Изменение статуса'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Получатель'
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
        verbose_name='Тип уведомления'
    )
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    message = models.TextField(verbose_name='Текст уведомления')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    violation = models.ForeignKey(
        'Violation',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='Связанное нарушение'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.full_name}"


class ViolationReport(models.Model):
    """Модель для сформированных выписок/отчетов"""
    REPORT_TYPES = (
        ('certificate', 'Справка о нарушениях'),
        ('detailed', 'Детальный отчет'),
        ('statistics', 'Статистический отчет'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name='Пользователь'
    )
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPES,
        verbose_name='Тип отчета'
    )
    date_from = models.DateField(verbose_name='Период с')
    date_to = models.DateField(verbose_name='Период по')
    file = models.FileField(
        upload_to='reports/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='Файл отчета'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    data = models.JSONField(default=dict, verbose_name='Данные отчета')

    def __str__(self):
        return f"Отчет {self.user.full_name} от {self.created_at.strftime('%d.%m.%Y')}"


class ArticleCoAP(models.Model):
    """Справочник статей КоАП"""
    article_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Номер статьи'
    )
    description = models.TextField(verbose_name='Описание нарушения')
    fine_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма штрафа (₽)'
    )
    penalty_points = models.IntegerField(
        default=0,
        verbose_name='Штрафные баллы'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    class Meta:
        verbose_name = 'Статья КоАП'
        verbose_name_plural = 'Статьи КоАП'
        ordering = ['article_number']

    def __str__(self):
        return self.article_number


class ViolationPhoto(models.Model):
    """
    Модель фотоматериалов нарушения
    Доказательная база
    """

    violation = models.ForeignKey(
        'Violation',
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name='Нарушение'
    )
    photo = models.ImageField(
        upload_to='violations/%Y/%m/%d/',
        verbose_name='Фотография',
        help_text='Загрузите фото нарушения. Поддерживаются форматы: JPG, PNG, GIF, BMP'
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Описание фото'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата загрузки'
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_photos',
        verbose_name='Загрузил'
    )

    class Meta:
        verbose_name = 'Фотоматериал'
        verbose_name_plural = 'Фотоматериалы'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Фото к нарушению #{self.violation.id} от {self.uploaded_at.strftime('%d.%m.%Y %H:%M')}"

    @property
    def photo_url(self):
        if self.photo:
            return self.photo.url
        return None

    @property
    def photo_filename(self):
        if self.photo:
            return self.photo.name.split('/')[-1]
        return None


class Vehicle(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='vehicles',
        verbose_name='Владелец'
    )
    license_plate = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Государственный номер'
    )
    brand = models.CharField(
        max_length=100,
        verbose_name='Марка'
    )
    model = models.CharField(
        max_length=100,
        verbose_name='Модель'
    )
    vin = models.CharField(
        max_length=17,
        blank=True,
        verbose_name='VIN-номер'
    )
    year = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Год выпуска'
    )
    color = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Цвет'
    )
    category = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Категория ТС'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активно'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата регистрации'
    )

    class Meta:
        verbose_name = 'Транспортное средство'
        verbose_name_plural = 'Транспортные средства'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.license_plate} - {self.brand} {self.model}"
