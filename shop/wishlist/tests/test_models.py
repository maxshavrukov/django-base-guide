from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from main.models import Category, Product
from wishlist.models import WishlistItem

User = get_user_model()

class WishlistItemModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='wishuser', password='password123')
        self.category = Category.objects.create(name='Книги', slug='books')
        self.product = Product.objects.create(
            category=self.category,
            name='Python книга',
            slug='python-book',
            price=Decimal('1200.00'),
            available=True
        )

    def test_wishlist_item_creation(self):
        """Проверяем создание элемента избранного и строковое представление, заданное в модели[cite: 7]"""
        item = WishlistItem.objects.create(user=self.user, product=self.product)
        self.assertEqual(item.user, self.user)
        self.assertEqual(item.product, self.product)
        self.assertEqual(str(item), 'wishuser - Python книга')

    def test_wishlist_item_unique_together(self):
        """Проверяем ограничение unique_together: нельзя добавить один товар дважды для одного пользователя[cite: 7]"""
        from django.db.utils import IntegrityError
        WishlistItem.objects.create(user=self.user, product=self.product)
        with self.assertRaises(IntegrityError):
            WishlistItem.objects.create(user=self.user, product=self.product)