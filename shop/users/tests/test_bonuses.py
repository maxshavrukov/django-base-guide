from datetime import date, datetime, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from orders.models import Order, OrderItem
from main.models import Brand, ProductGroup, Smartphone
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

    def test_bonus_rules_are_single_source_of_truth(self):
        rules = BonusService.get_rules()
        self.assertEqual(rules['purchase_percent'], Decimal('1'))
        self.assertEqual(rules['purchase_validity_months'], 12)
        self.assertEqual(rules['birthday_bonus'], 1000)
        self.assertEqual(rules['birthday_window_days'], 7)
        self.assertEqual(rules['max_product_payment_percent'], Decimal('50'))
        self.assertEqual(rules['bonus_value_uah'], Decimal('1'))

    def test_purchase_expiry_uses_configured_twelve_month_term(self):
        created = timezone.make_aware(datetime(2026, 12, 27, 12, 0))
        self.assertEqual(
            BonusService.purchase_expiry(created),
            timezone.make_aware(datetime(2027, 12, 27, 12, 0)),
        )

    def test_birthday_window_is_seven_days_before_and_after(self):
        self.profile.birth_date = date(2000, 8, 20)
        self.profile.save(update_fields=['birth_date', 'updated_at'])
        self.assertEqual(BonusService.birthday_window(self.profile.birth_date, 2026), (date(2026, 8, 13), date(2026, 8, 27)))
        self.assertTrue(BonusService.birthday_is_active(self.profile.birth_date, date(2026, 8, 13)))
        self.assertTrue(BonusService.birthday_is_active(self.profile.birth_date, date(2026, 8, 27)))
        self.assertFalse(BonusService.birthday_is_active(self.profile.birth_date, date(2026, 8, 28)))

    def test_birthday_bonus_expires_at_start_of_the_next_day_after_window(self):
        birth_date = date(2000, 8, 20)
        expiry = BonusService.birthday_expiry(birth_date, 2026)
        self.assertEqual(expiry, timezone.make_aware(datetime(2026, 8, 28, 0, 0)))

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

    def test_expired_bonus_is_not_available_or_spent(self):
        account = BonusService.get_or_create_account(self.user)
        now = timezone.now()
        expired = BonusTransaction.objects.create(
            account=account, amount=100, transaction_type='purchase',
            created_at=now - timedelta(days=30), expires_at=now - timedelta(seconds=1),
        )
        active = BonusTransaction.objects.create(
            account=account, amount=80, transaction_type='purchase',
            created_at=now, expires_at=now + timedelta(days=30),
        )

        self.assertEqual(BonusService.get_available_balance(account, at=now), 80)
        spend = BonusService.spend(self.user, 80)
        self.assertEqual(spend.amount, -80)
        self.assertEqual(
            BonusConsumption.objects.get(source_transaction_id=active.id).amount,
            80,
        )
        self.assertFalse(BonusConsumption.objects.filter(source_transaction=expired).exists())

    def test_max_redemption_is_fifty_percent_per_unit(self):
        self.assertEqual(BonusService.max_redemption_for_line(Decimal('100.00'), 3), 150)


    def test_max_redemption_rounds_each_unit_down_before_multiplying(self):
        self.assertEqual(BonusService.max_redemption_for_line(Decimal('99.99'), 3), 147)

    def test_purchase_bonus_accrues_one_percent_only_for_full_price_items(self):
        brand = Brand.objects.create(name='Bonus Brand', slug='bonus-brand')
        group = ProductGroup.objects.create(name='Bonus Series', slug='bonus-series')
        full_price = Smartphone.objects.create(
            brand=brand, group=group, name='Full Price Phone', slug='full-price-phone',
            price=Decimal('10000.00'), available=True, stock=2,
            display_size='6.1', ram=8, storage=256, main_camera_mp=50, battery_capacity=5000,
        )
        discounted = Smartphone.objects.create(
            brand=brand, group=group, name='Discounted Phone', slug='discounted-phone',
            price=Decimal('5000.00'), discount=10, available=True, stock=2,
            display_size='6.1', ram=8, storage=256, main_camera_mp=50, battery_capacity=5000,
        )
        order = Order.objects.create(
            user=self.user, first_name='Test', email='test@example.com', phone='000', address='Test'
        )
        OrderItem.objects.create(order=order, product=full_price, price=full_price.price, quantity=1, bonus_eligible=True)
        OrderItem.objects.create(order=order, product=discounted, price=discounted.get_discounted_price(), quantity=1, bonus_eligible=False)

        order.paid = True
        order.save(update_fields=['paid', 'updated'])
        order.refresh_from_db()

        self.assertEqual(order.purchase_bonus_amount, 100)
        transaction = BonusTransaction.objects.get(
            order=order, transaction_type=BonusTransaction.TransactionType.PURCHASE
        )
        self.assertEqual(transaction.amount, 100)
        self.assertEqual(transaction.expires_at, BonusService.purchase_expiry(order.created))
        order.refresh_from_db()
        self.assertTrue(order.purchase_bonus_granted)
        self.assertEqual(order.purchase_bonus_amount, 100)

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
