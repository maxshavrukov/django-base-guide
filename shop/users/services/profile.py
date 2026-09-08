from django.db import transaction

from orders.models import Order
from users.models import BonusAccount, RecentlyViewedProduct, UserProfile


def get_user_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    BonusAccount.objects.get_or_create(user=user)
    return profile


def get_user_orders(user):
    return (
        Order.objects
        .filter(user=user)
        .prefetch_related('items__product')
        .order_by('-created', '-id')
    )


@transaction.atomic
def record_recently_viewed(user, product):
    item, _ = RecentlyViewedProduct.objects.get_or_create(user=user, product=product)
    item.save(update_fields=['viewed_at'])
    # Keep the DB history compact. The cabinet is intentionally showing the
    # latest 20 items rather than an unbounded list.
    stale_ids = list(
        RecentlyViewedProduct.objects
        .filter(user=user)
        .order_by('-viewed_at', '-id')
        .values_list('id', flat=True)[20:]
    )
    if stale_ids:
        RecentlyViewedProduct.objects.filter(id__in=stale_ids).delete()


def get_recently_viewed(user, limit=20):
    return (
        RecentlyViewedProduct.objects
        .filter(user=user)
        .select_related('product', 'product__brand')
        .order_by('-viewed_at', '-id')[:limit]
    )