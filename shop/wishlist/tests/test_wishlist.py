from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, RequestFactory
from django.contrib.sessions.backends.db import SessionStore

from main.models import Smartphone
from wishlist.wishlist import Wishlist

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

    def test_authenticated_wishlist_methods(self):
        request = self.factory.get('/')
        request.session = SessionStore()
        request.user = self.user
        wishlist = Wishlist(request)

        wishlist.add(self.product.id)
        self.assertEqual(len(wishlist), 1)
        wishlist.clear()
        self.assertEqual(len(wishlist), 0)
