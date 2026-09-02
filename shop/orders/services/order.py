from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.db import transaction

from basket.services.basket import Basket
from orders.forms import OrderCreateForm
from orders.models import Order, OrderItem


@transaction.atomic
def create_order(user: AbstractBaseUser | AnonymousUser, form: OrderCreateForm, basket: Basket) -> Order:
    """
    Создает заказ, сохраняет позиции из корзины и очищает её.
    Выполняется в одной транзакции БД.
    """
    order = form.save(commit=False)
    if user and user.is_authenticated:
        order.user = user
    order.save()

    # Сохраняем позицию каждого товара из корзины в заказ
    for item in basket:
        OrderItem.objects.create(
            order=order,
            product=item['product'],
            price=item['price'],
            quantity=item['quantity']
        )

    # Очищаем корзину пользователя/сессии
    basket.clear()

    return order