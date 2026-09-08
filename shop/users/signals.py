from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import BonusAccount, UserProfile


@receiver(post_save, sender=User)
def ensure_user_accounts(sender, instance, created, **kwargs):
    UserProfile.objects.get_or_create(user=instance)
    BonusAccount.objects.get_or_create(user=instance)
