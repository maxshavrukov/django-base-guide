from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from users.services.bonuses import BonusService


class Command(BaseCommand):
    help = 'Проверяет доступный баланс бонусов и не изменяет историю операций.'

    def handle(self, *args, **options):
        User = get_user_model()
        checked = 0
        for user in User.objects.filter(is_active=True):
            BonusService.available_balance_after_expiration(user)
            checked += 1
        self.stdout.write(self.style.SUCCESS(f'Проверено аккаунтов: {checked}.'))
