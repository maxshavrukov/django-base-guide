from datetime import date, datetime, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from orders.models import Order, OrderItem
from users.models import BonusConsumption, BonusTransaction, UserProfile
from users.services.bonuses import BonusService


class BonusServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('bonus-user', password='secret')
        self.profile = UserProfile.objects.get(user=self.user)

    def test_purchase_bonus_expires_after_twelve_months(self):
        created = timezone.make_aware(datetime(2026, 12, 27, 12, 0))
        expiry = BonusService.purchase_expiry(created)
        self.assertEqual(expiry, timezone.make_aware(datetime(2027, 12, 27, 12, 0)))

    def test_purchase_bonus_calculation_is_one_percent(self):
        self.assertEqual(BonusService.calculate_purchase_bonus(Decimal('12500.00')), 125)

    def test_birthday_window_is_seven_days_before_and_after(self):
        self.profile.birth_date = date(2000, 8, 20)
        self.profile.save(update_fields=['birth_date', 'updated_at'])
        self.assertEqual(BonusService.birthday_window(self.profile.birth_date, 2026), (date(2026, 8, 13), date(2026, 8, 27)))
        self.assertTrue(BonusService.birthday_is_active(self.profile.birth_date, date(2026, 8, 13)))
        self.assertTrue(BonusService.birthday_is_active(self.profile.birth_date, date(2026, 8, 27)))
        self.assertFalse(BonusService.birthday_is_active(self.profile.birth_date, date(2026, 8, 28)))

    def test_birthday_window_handles_new_year_boundary(self):
        self.profile.birth_date = date(2000, 1, 5)
        self.profile.save(update_fields=['birth_date', 'updated_at'])
        self.assertEqual(BonusService.get_active_birthday_year(self.profile.birth_date, date(2025, 12, 30)), 2026)

    def test_birthday_bonus_is_granted_once_per_year(self):
        self.profile.birth_date = date(2000, 8, 20)
        self.profile.save(update_fields=['birth_date', 'updated_at'])
        self.user.refresh_from_db()
        first = BonusService.ensure_birthday_bonus(self.user, on_date=date(2026, 8, 13))
        second = BonusService.ensure_birthday_bonus(self.user, on_date=date(2026, 8, 20))
        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertEqual(BonusTransaction.objects.filter(transaction_type='birthday', reference_year=2026).count(), 1)

    def test_spend_uses_earliest_expiry_first(self):
        account = BonusService.get_or_create_account(self.user)
        now = timezone.now()
        older = BonusTransaction.objects.create(
            account=account, amount=100, transaction_type='purchase',
            created_at=now, expires_at=now + timezone.timedelta(days=10),
        )
        newer = BonusTransaction.objects.create(
            account=account, amount=100, transaction_type='purchase',
            created_at=now, expires_at=now + timedelta(days=30),
        )
        spend = BonusService.spend(self.user, 120)
        self.assertEqual(spend.amount, -120)
        self.assertEqual(BonusConsumption.objects.get(source_transaction=older).amount, 100)
        self.assertEqual(BonusConsumption.objects.get(source_transaction=newer).amount, 20)
        self.assertEqual(BonusService.get_available_balance(account), 80)

    def test_max_redemption_is_fifty_percent_per_unit(self):
        self.assertEqual(BonusService.max_redemption_for_line(Decimal('100.00'), 3), 150)


    def test_reverse_purchase_bonus_is_a_negative_history_entry(self):
        account = BonusService.get_or_create_account(self.user)
        order = Order.objects.create(user=self.user, first_name='Test', email='test@example.com', phone='000', address='Test')
        order.purchase_bonus_amount = 100
        order.purchase_bonus_granted = True
        order.save(update_fields=['purchase_bonus_amount', 'purchase_bonus_granted', 'updated'])
        BonusTransaction.objects.create(account=account, amount=100, transaction_type='purchase', order=order, expires_at=timezone.now() + timedelta(days=30))
        refund = BonusService.reverse_purchase_bonus(order)
        self.assertEqual(refund.amount, -100)
        self.assertEqual(BonusService.get_available_balance(account), 0)
