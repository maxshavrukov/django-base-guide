from django.conf import settings
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь',
    )
    first_name = models.CharField('Имя', max_length=100, blank=True)
    last_name = models.CharField('Фамилия', max_length=100, blank=True)
    phone = models.CharField('Телефон', max_length=32, blank=True)
    birth_date = models.DateField('Дата рождения', null=True, blank=True)
    city = models.CharField('Город', max_length=120, blank=True)
    address = models.CharField('Адрес', max_length=255, blank=True)
    postal_code = models.CharField('Почтовый индекс', max_length=20, blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f'Профиль: {self.user.username}'

    @property
    def display_name(self):
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name or self.user.get_username()


class BonusAccount(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bonus_account',
        verbose_name='Пользователь',
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Бонусный счёт'
        verbose_name_plural = 'Бонусные счета'

    def __str__(self):
        return f'Бонусный счёт: {self.user.username}'

    def get_available_balance(self, at=None):
        # Логика расчёта находится в BonusService, чтобы единообразно
        # учитывать срок действия и уже использованные начисления.
        from users.services.bonuses import BonusService
        return BonusService.get_available_balance(self, at=at)


class BonusTransaction(models.Model):
    class TransactionType(models.TextChoices):
        PURCHASE = 'purchase', 'Начисление за покупку'
        BIRTHDAY = 'birthday', 'Подарок ко дню рождения'
        SPEND = 'spend', 'Списание бонусов'
        REFUND = 'refund', 'Возврат бонусов'
        ADJUSTMENT = 'adjustment', 'Корректировка'

    account = models.ForeignKey(
        BonusAccount,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='Бонусный счёт',
    )
    amount = models.IntegerField(
        'Количество бонусов',
        help_text='Положительное число — начисление, отрицательное — списание.',
    )
    transaction_type = models.CharField(
        'Тип операции',
        max_length=20,
        choices=TransactionType.choices,
    )
    order = models.ForeignKey(
        'orders.Order',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='bonus_transactions',
        verbose_name='Заказ',
    )
    description = models.CharField('Описание', max_length=255, blank=True)
    reference_year = models.PositiveIntegerField(
        'Расчётный год',
        null=True,
        blank=True,
        help_text='Используется для защиты от повторной выдачи подарка ко дню рождения.',
    )
    created_at = models.DateTimeField('Создано', default=timezone.now, db_index=True)
    expires_at = models.DateTimeField('Действует до', null=True, blank=True, db_index=True)

    class Meta:
        ordering = ('-created_at', '-id')
        verbose_name = 'Бонусная операция'
        verbose_name_plural = 'Бонусные операции'
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(amount=0),
                name='bonus_transaction_amount_nonzero',
            ),
            models.UniqueConstraint(
                fields=('account', 'transaction_type', 'reference_year'),
                condition=models.Q(transaction_type='birthday') & models.Q(reference_year__isnull=False),
                name='unique_birthday_bonus_per_year',
            ),
        ]

    def __str__(self):
        sign = '+' if self.amount > 0 else ''
        return f'{sign}{self.amount} бонусов · {self.get_transaction_type_display()}'


class BonusConsumption(models.Model):
    spend_transaction = models.ForeignKey(
        BonusTransaction,
        on_delete=models.CASCADE,
        related_name='consumptions',
        verbose_name='Списание',
        limit_choices_to={'amount__lt': 0},
    )
    source_transaction = models.ForeignKey(
        BonusTransaction,
        on_delete=models.PROTECT,
        related_name='consumed_amounts',
        verbose_name='Начисление-источник',
        limit_choices_to={'amount__gt': 0},
    )
    amount = models.PositiveIntegerField('Использовано бонусов')

    class Meta:
        verbose_name = 'Расход бонусов'
        verbose_name_plural = 'Расходы бонусов'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name='bonus_consumption_amount_positive',
            ),
        ]
        indexes = [
            models.Index(fields=('source_transaction',)),
            models.Index(fields=('spend_transaction',)),
        ]

    def __str__(self):
        return f'{self.amount} бонусов'


class RecentlyViewedProduct(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recently_viewed_products',
        verbose_name='Пользователь',
    )
    product = models.ForeignKey(
        'main.Product',
        on_delete=models.CASCADE,
        related_name='recently_viewed_by',
        verbose_name='Товар',
    )
    viewed_at = models.DateTimeField('Просмотрено', auto_now=True, db_index=True)

    class Meta:
        ordering = ('-viewed_at', '-id')
        verbose_name = 'Просмотренный товар'
        verbose_name_plural = 'Просмотренные товары'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'product'),
                name='unique_recently_viewed_user_product',
            ),
        ]

    def __str__(self):
        return f'{self.user} · {self.product}'
