from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import BonusAccount
from users.services.bonuses import BonusService


class Command(BaseCommand):
    help = 'Показывает количество действующих бонусов и не удаляет истёкшие транзакции.'

    def handle(self, *args, **options):
        now = timezone.now()
        total = 0
        for account in BonusAccount.objects.all().iterator():
            total += BonusService.get_available_balance(account, at=now)
        self.stdout.write(self.style.SUCCESS(f'Доступный баланс по системе: {total} бонусов.'))
