import calendar
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone

from users.models import BonusAccount, BonusConsumption, BonusTransaction


class BonusService:
    # Единый источник истины для всех правил бонусной программы.
    PURCHASE_BONUS_PERCENT = Decimal('1')
    PURCHASE_BONUS_VALIDITY_MONTHS = 12
    BIRTHDAY_BONUS = 1000
    BIRTHDAY_WINDOW_DAYS = 7
    MAX_PRODUCT_REDEMPTION_PERCENT = Decimal('50')
    BONUS_VALUE_UAH = Decimal('1')

    @classmethod
    def get_rules(cls):
        """Возвращает публичные правила бонусной программы для UI."""
        return {
            'purchase_percent': cls.PURCHASE_BONUS_PERCENT,
            'purchase_validity_months': cls.PURCHASE_BONUS_VALIDITY_MONTHS,
            'birthday_bonus': cls.BIRTHDAY_BONUS,
            'birthday_window_days': cls.BIRTHDAY_WINDOW_DAYS,
            'max_product_payment_percent': cls.MAX_PRODUCT_REDEMPTION_PERCENT,
            'bonus_value_uah': cls.BONUS_VALUE_UAH,
        }

    @classmethod
    def _today(cls):
        return timezone.localdate()

    @staticmethod
    def _add_months(value, months):
        year = value.year + (value.month - 1 + months) // 12
        month = (value.month - 1 + months) % 12 + 1
        day = min(value.day, calendar.monthrange(year, month)[1])
        return value.replace(year=year, month=month, day=day)

    @classmethod
    def purchase_expiry(cls, created_at):
        local = timezone.localtime(created_at) if timezone.is_aware(created_at) else created_at
        target_date = cls._add_months(local.date(), cls.PURCHASE_BONUS_VALIDITY_MONTHS)
        return local.replace(year=target_date.year, month=target_date.month, day=target_date.day)

    @classmethod
    def birthday_window(cls, birth_date, year):
        """Return [start_date, end_date] inclusive for the birthday year."""
        try:
            birthday = birth_date.replace(year=year)
        except ValueError:
            # For 29 February we keep the benefit usable every year by
            # treating the birthday as 28 February in non-leap years.
            birthday = birth_date.replace(year=year, day=28)
        return birthday - timedelta(days=cls.BIRTHDAY_WINDOW_DAYS), birthday + timedelta(days=cls.BIRTHDAY_WINDOW_DAYS)

    @classmethod
    def birthday_expiry(cls, birth_date, year):
        _, end_date = cls.birthday_window(birth_date, year)
        expiry = datetime.combine(end_date + timedelta(days=1), time.min)
        return timezone.make_aware(expiry) if timezone.is_naive(expiry) else expiry

    @classmethod
    def get_active_birthday_year(cls, birth_date, on_date=None):
        if not birth_date:
            return None
        on_date = on_date or cls._today()
        for year in (on_date.year - 1, on_date.year, on_date.year + 1):
            start, end = cls.birthday_window(birth_date, year)
            if start <= on_date <= end:
                return year
        return None

    @classmethod
    def birthday_is_active(cls, birth_date, on_date=None):
        return cls.get_active_birthday_year(birth_date, on_date=on_date) is not None

    @classmethod
    def calculate_purchase_bonus(cls, eligible_purchase_value):
        value = Decimal(eligible_purchase_value or 0)
        if value <= 0:
            return 0
        percent = cls.PURCHASE_BONUS_PERCENT / Decimal('100')
        return int((value * percent).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

    @classmethod
    def get_or_create_account(cls, user):
        account, _ = BonusAccount.objects.get_or_create(user=user)
        return account

    @classmethod
    def _positive_sources(cls, account, at=None):
        at = at or timezone.now()
        qs = account.transactions.filter(amount__gt=0).order_by(F('expires_at').asc(nulls_last=True), 'created_at', 'id')
        result = []
        for transaction in qs:
            if transaction.expires_at is not None and transaction.expires_at <= at:
                continue
            consumed = sum(item.amount for item in transaction.consumed_amounts.all())
            remaining = transaction.amount - consumed
            if remaining > 0:
                result.append((transaction, remaining))
        return result

    @classmethod
    def get_available_balance(cls, account, at=None):
        at = at or timezone.now()
        total = 0
        qs = account.transactions.filter(amount__gt=0).order_by(F('expires_at').asc(nulls_last=True), 'created_at', 'id')
        for transaction in qs:
            if transaction.expires_at is not None and transaction.expires_at <= at:
                continue
            consumed = sum(item.amount for item in transaction.consumed_amounts.all())
            total += max(0, transaction.amount - consumed)

        # SPEND transactions are represented by BonusConsumption. Other negative
        # ledger rows (refund/adjustment) are direct reversals and therefore
        # reduce the available balance without deleting historical operations.
        direct_reversals = account.transactions.filter(
            amount__lt=0,
        ).exclude(
            transaction_type=BonusTransaction.TransactionType.SPEND,
        ).aggregate(total=Sum('amount'))['total'] or 0
        return max(0, total + direct_reversals)

    @classmethod
    @transaction.atomic
    def grant_purchase_bonus(cls, order, *, created_at=None):
        if not order.user_id:
            return 0
        if getattr(order, 'purchase_bonus_granted', False):
            return 0

        account = cls.get_or_create_account(order.user)
        created_at = created_at or order.created
        eligible_value = Decimal('0.00')

        items = order.items.select_related('product').all()
        for item in items:
            eligible = getattr(item, 'bonus_eligible', None)
            if eligible is None:
                eligible = (
                    item.price == item.product.price
                    and item.product.effective_discount_percent == 0
                )
            if eligible:
                eligible_value += item.price * item.quantity

        amount = cls.calculate_purchase_bonus(eligible_value)
        if amount > 0:
            BonusTransaction.objects.create(
                account=account,
                amount=amount,
                transaction_type=BonusTransaction.TransactionType.PURCHASE,
                order=order,
                description=f'{cls.PURCHASE_BONUS_PERCENT}% бонусов за заказ №{order.pk}',
                created_at=created_at,
                expires_at=cls.purchase_expiry(created_at),
            )

        if hasattr(order, 'purchase_bonus_granted'):
            order.purchase_bonus_granted = True
            order.purchase_bonus_amount = amount
            order.save(update_fields=['purchase_bonus_granted', 'purchase_bonus_amount', 'updated'])
        return amount

    @classmethod
    @transaction.atomic
    def ensure_birthday_bonus(cls, user, on_date=None):
        if not user.is_authenticated:
            return None
        profile = getattr(user, 'profile', None)
        if not profile or not profile.birth_date:
            return None

        on_date = on_date or cls._today()
        birthday_year = cls.get_active_birthday_year(profile.birth_date, on_date)
        if birthday_year is None:
            return None
        _, end = cls.birthday_window(profile.birth_date, birthday_year)

        account = cls.get_or_create_account(user)
        exists = BonusTransaction.objects.filter(
            account=account,
            transaction_type=BonusTransaction.TransactionType.BIRTHDAY,
            reference_year=birthday_year,
        ).exists()
        if exists:
            return None

        expiry = cls.birthday_expiry(profile.birth_date, birthday_year)
        return BonusTransaction.objects.create(
            account=account,
            amount=cls.BIRTHDAY_BONUS,
            transaction_type=BonusTransaction.TransactionType.BIRTHDAY,
            reference_year=birthday_year,
            description='Подарок ко дню рождения',
            created_at=timezone.now(),
            expires_at=expiry,
        )

    @classmethod
    def is_product_full_price(cls, product):
        return product.effective_discount_percent == 0

    @classmethod
    def max_redemption_for_line(cls, price, quantity=1):
        # Лимит применяется отдельно к каждой единице товара.
        unit_price = Decimal(price or 0)
        units = int(quantity or 0)
        if unit_price <= 0 or units <= 0:
            return 0

        unit_limit = int(
            (unit_price * (cls.MAX_PRODUCT_REDEMPTION_PERCENT / Decimal('100'))).quantize(
                Decimal('1'),
                rounding=ROUND_DOWN,
            )
        )
        return unit_limit * units

    @classmethod
    def calculate_max_spend(cls, items):
        total = 0
        for item in items:
            product = item['product']
            if not cls.is_product_full_price(product):
                continue
            total += cls.max_redemption_for_line(item['price'], item['quantity'])
        return total

    @classmethod
    @transaction.atomic
    def spend(cls, user, amount, *, order=None, description='Оплата бонусами'):
        amount = int(amount or 0)
        if amount <= 0:
            return None

        account = cls.get_or_create_account(user)
        now = timezone.now()
        cls.ensure_birthday_bonus(user, on_date=timezone.localdate(now))
        sources = cls._locked_positive_sources(account, now)
        source_total = sum(remaining for _, remaining in sources)
        direct_reversals = account.transactions.filter(
            amount__lt=0,
        ).exclude(
            transaction_type=BonusTransaction.TransactionType.SPEND,
        ).aggregate(total=Sum('amount'))['total'] or 0
        available = max(0, source_total + direct_reversals)
        if amount > available:
            raise ValueError('Недостаточно доступных бонусов.')

        spend = BonusTransaction.objects.create(
            account=account,
            amount=-amount,
            transaction_type=BonusTransaction.TransactionType.SPEND,
            order=order,
            description=description,
            created_at=now,
        )

        left = amount
        for source, remaining in sources:
            take = min(left, remaining)
            BonusConsumption.objects.create(
                spend_transaction=spend,
                source_transaction=source,
                amount=take,
            )
            left -= take
            if left == 0:
                break
        return spend

    @classmethod
    def _locked_positive_sources(cls, account, at):
        qs = (
            account.transactions
            .select_for_update()
            .filter(amount__gt=0)
            .order_by(F('expires_at').asc(nulls_last=True), 'created_at', 'id')
            .prefetch_related('consumed_amounts')
        )
        result = []
        for transaction in qs:
            if transaction.expires_at is not None and transaction.expires_at <= at:
                continue
            consumed = sum(item.amount for item in transaction.consumed_amounts.all())
            remaining = transaction.amount - consumed
            if remaining > 0:
                result.append((transaction, remaining))
        return result

    @classmethod
    @transaction.atomic
    def reverse_purchase_bonus(cls, order, *, description=None):
        """Create an auditable reverse transaction for previously earned bonuses."""
        if not order.user_id or not getattr(order, 'purchase_bonus_amount', 0):
            return None
        account = cls.get_or_create_account(order.user)
        already_reversed = account.transactions.filter(
            order=order,
            transaction_type=BonusTransaction.TransactionType.REFUND,
        ).exists()
        if already_reversed:
            return None
        return BonusTransaction.objects.create(
            account=account,
            amount=-int(order.purchase_bonus_amount),
            transaction_type=BonusTransaction.TransactionType.REFUND,
            order=order,
            description=description or f'Сторно бонусов за возврат заказа №{order.pk}',
            created_at=timezone.now(),
        )

    @classmethod
    def available_balance_after_expiration(cls, user):
        account = cls.get_or_create_account(user)
        cls.ensure_birthday_bonus(user)
        return cls.get_available_balance(account)
