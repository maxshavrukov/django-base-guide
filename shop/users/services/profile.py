from django.db.models import QuerySet
from orders.models import Order


def get_user_orders(user) -> QuerySet:
    """Возвращает список заказов пользователя с оптимизированными предзагрузками позиций."""
    return (
        Order.objects.filter(user=user)
        .prefetch_related('items__product')
        .order_by('-created_at')
    )