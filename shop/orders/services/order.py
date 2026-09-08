from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.db import transaction

from basket.services.basket import Basket
from orders.forms import OrderCreateForm
from orders.models import Order, OrderItem
from users.services.bonuses import BonusService


@transaction.atomic
def create_order(user: AbstractBaseUser | AnonymousUser, form: OrderCreateForm, basket: Basket) -> Order:
    """Создаёт заказ, фиксирует скидки/бонусы и только затем очищает корзину."""
    order = form.save(commit=False)
    if user and user.is_authenticated:
        order.user = user

    details = basket.get_basket_details()
    promo_discount_amount = details['promo_discount_amount']
    requested_bonus = basket.get_bonus_requested_amount()
    max_bonus = details['bonus_max_redemption']
    available_bonus = details['bonus_available_balance']
    actual_bonus = min(requested_bonus, max_bonus, available_bonus)

    order.basket_discount_amount = promo_discount_amount
    order.bonus_spent_amount = actual_bonus
    order.save()

    cart_promotion_applied = promo_discount_amount > 0
    for item in basket:
        bonus_eligible = (
            not cart_promotion_applied
            and item['product_discount_percent'] == 0
            and item['price'] == item['original_price']
        )
        OrderItem.objects.create(
            order=order,
            product=item['product'],
            price=item['price'],
            quantity=item['quantity'],
            bonus_eligible=bonus_eligible,
        )

    if actual_bonus > 0 and order.user_id:
        BonusService.spend(
            order.user,
            actual_bonus,
            order=order,
            description=f'Оплата бонусами заказа №{order.pk}',
        )

    basket.clear()
    return order
