from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Violation, Notification
import re

User = get_user_model()

@receiver(post_save, sender=Violation)
def create_notification_on_violation(sender, instance, created, **kwargs):
    if created:

        full_plate = instance.car_plate

        pattern = r'^([АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2})(\d{2,3})$'
        match = re.match(pattern, full_plate)

        if not match:
            print(f"Не удалось распарсить номер: {full_plate}")
            return

        plate_series = match.group(1)
        plate_region = match.group(2)

        print(f"Ищем водителя: серия={plate_series}, регион={plate_region}")

        try:
            driver = User.objects.get(
                role='driver',
                full_license_plate__iexact=full_plate
            )
            print(f"Найден водитель: {driver.full_name}")

            instance.driver = driver
            instance.save(update_fields=['driver'])

        except User.DoesNotExist:
            print(f"Водитель с номером {full_plate} не найден")
            return

        notification_title = f"Новое нарушение #{instance.id}"
        notification_message = (
            f"Уважаемый(ая) {driver.full_name}!\n\n"
            f"За вашим транспортным средством ({full_plate}) зафиксировано нарушение: "
            f"{instance.article}.\n"
            f"Сумма штрафа: {instance.amount} руб.\n"
            f"Место: {instance.place}\n\n"
            f"Для оплаты перейдите в личный кабинет."
        )

        Notification.objects.create(
            user=driver,
            notification_type='new_violation',
            title=notification_title,
            message=notification_message,
            violation=instance
        )

        print(f"Уведомление для {driver.full_name} о нарушении #{instance.id} создано!")