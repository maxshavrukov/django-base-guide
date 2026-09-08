from django.conf import settings
from django.db import models
from django.db.models import F, Sum


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        blank=True,
        null=True,
        verbose_name='Пользователь',
    )
    first_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    address = models.CharField(max_length=250)
    comment = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    purchase_bonus_granted = models.BooleanField(default=False, verbose_name='Бонусы за покупку начислены')
    purchase_bonus_amount = models.PositiveIntegerField(default=0, verbose_name='Начислено бонусов за заказ')
    basket_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Скидка корзины',
    )
    bonus_spent_amount = models.PositiveIntegerField(
        default=0,
        verbose_name='Оплачено бонусами',
    )

    class Meta:
        ordering = ['-created']
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'Order {self.id}'

    def get_items_total(self):
        return self.items.aggregate(
            total=Sum(F('price') * F('quantity'))
        )['total'] or 0

    def get_total_cost(self):
        total = self.get_items_total() - self.basket_discount_amount - self.bonus_spent_amount
        return max(total, 0)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        'main.Product',
        related_name='order_items',
        on_delete=models.CASCADE,
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    bonus_eligible = models.BooleanField(
        null=True,
        default=None,
        verbose_name='Учитывать в начислении бонусов',
    )

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity
