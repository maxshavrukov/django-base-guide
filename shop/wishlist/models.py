from django.db import models
from django.conf import settings
from main.models import Product

class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product') # Чтобы нельзя было добавить один товар дважды

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"