from django.db.models.signals import post_save
from django.dispatch import receiver

from orders.models import Order


@receiver(post_save, sender=Order)
def grant_purchase_bonus_after_payment(sender, instance, created, **kwargs):
    if instance.user_id and instance.paid and not instance.purchase_bonus_granted:
        from users.services.bonuses import BonusService
        BonusService.grant_purchase_bonus(instance)
