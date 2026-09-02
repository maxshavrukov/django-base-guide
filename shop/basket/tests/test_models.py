from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

from main.models import Smartphone
from basket.models import BasketItem

User = get_user_model()


class BasketItemModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.product = Smartphone.objects.create(
            name='Беспроводные наушники',
            slug='wireless-headphones',
            price=Decimal('3500.00'),
            available=True,
        )

    def test_basket_item_creation(self):
        basket_item = BasketItem.objects.create(
            user=self.user,
            product=self.product,
            quantity=3,
        )
        self.assertEqual(basket_item.user, self.user)
        self.assertEqual(basket_item.product, self.product)
        self.assertEqual(basket_item.quantity, 3)
        self.assertEqual(str(basket_item), 'testuser - Беспроводные наушники (3)')

    def test_basket_item_unique_together(self):
        BasketItem.objects.create(user=self.user, product=self.product, quantity=1)
        with self.assertRaises(IntegrityError):
            BasketItem.objects.create(user=self.user, product=self.product, quantity=2)
