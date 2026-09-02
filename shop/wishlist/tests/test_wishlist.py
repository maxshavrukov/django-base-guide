from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, RequestFactory
from django.contrib.sessions.backends.db import SessionStore

from main.models import Product, Smartphone
from wishlist.services.wishlist import Wishlist

User = get_user_model()


class WishlistClassTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.product = Smartphone.objects.create(
            name='Телефон',
            slug='phone',
            price=Decimal('10000.00'),
            available=True,
        )

    def test_guest_wishlist_methods(self):
        request = self.factory.get('/')
        request.session = SessionStore()
        request.user = AnonymousUser()
        wishlist = Wishlist(request)

        self.assertEqual(len(wishlist), 0)
        wishlist.add(self.product.id)
        self.assertEqual(len(wishlist), 1)
        self.assertIn(self.product, list(wishlist))
        wishlist.remove(self.product.id)
        self.assertEqual(len(wishlist), 0)


    def test_base_product_without_concrete_child_is_supported(self):
        base_product = Product.objects.create(
            name='Базовый товар',
            slug='base-product',
            price=Decimal('500.00'),
            available=True,
        )
        request = self.factory.get('/')
        request.session = SessionStore()
        request.user = AnonymousUser()
        wishlist = Wishlist(request)
        wishlist.add(base_product.id)
        products = list(wishlist)
        self.assertEqual(products[0].id, base_product.id)
        self.assertIs(type(products[0]), Product)

    def test_authenticated_wishlist_methods(self):
        request = self.factory.get('/')
        request.session = SessionStore()
        request.user = self.user
        wishlist = Wishlist(request)

        wishlist.add(self.product.id)
        self.assertEqual(len(wishlist), 1)
        wishlist.clear()
        self.assertEqual(len(wishlist), 0)
