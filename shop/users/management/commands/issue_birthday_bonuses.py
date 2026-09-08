from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from users.services.bonuses import BonusService


class Command(BaseCommand):
    help = 'Выдаёт бонус ко дню рождения пользователям, у которых началось 14-дневное окно.'

    def handle(self, *args, **options):
        today = timezone.localdate()
        granted = 0
        skipped = 0
        User = get_user_model()

        qs = User.objects.filter(is_active=True, profile__birth_date__isnull=False).select_related('profile')
        for user in qs.iterator():
            transaction = BonusService.ensure_birthday_bonus(user, on_date=today)
            if transaction:
                granted += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Готово: выдано {granted}, пропущено {skipped}. Дата: {today:%Y-%m-%d}.'
            )
        )
