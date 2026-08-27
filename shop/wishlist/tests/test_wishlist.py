from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.db import SessionStore
from main.models import Category, Product
from wishlist.wishlist import Wishlist

User = get_user_model()

class WishlistClassTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.category = Category.objects.create(name='Электроника', slug='electronics')
        self.product = Product.objects.create(
            category=self.category,
            name='Телефон',
            slug='phone',
            price=Decimal('10000.00'),
            available=True
        )

    def test_guest_wishlist_methods(self):
        """Проверяем методы сессионного избранного для гостей (add, remove, len, iter)[cite: 9]"""
        request = self.factory.get('/')
        request.session = SessionStore()  # Инициализируем полноценную сессию
        request.user = AnonymousUser()    # Указываем, что это гость
        
        wishlist = Wishlist(request)
        
        # Изначально список пуст[cite: 9]
        self.assertEqual(len(wishlist), 0)
        
        # Добавляем товар по ID[cite: 9]
        wishlist.add(self.product.id)
        self.assertEqual(len(wishlist), 1)
        
        # Проверяем итератор[cite: 9]
        products = list(wishlist)
        self.assertIn(self.product, products)
        
        # Удаляем товар[cite: 9]
        wishlist.remove(self.product.id)
        self.assertEqual(len(wishlist), 0)

    def test_authenticated_wishlist_methods(self):
        """Проверяем методы избранного для авторизованного пользователя через базу данных[cite: 7, 9]"""
        request = self.factory.get('/')
        request.session = SessionStore()  # Инициализируем сессию
        request.user = self.user          # Передаем авторизованного пользователя
        
        wishlist = Wishlist(request)
        
        # Добавляем товар[cite: 9]
        wishlist.add(self.product.id)
        self.assertEqual(len(wishlist), 1)
        
        # Проверяем полную очистку[cite: 9]
        wishlist.clear()
        self.assertEqual(len(wishlist), 0)