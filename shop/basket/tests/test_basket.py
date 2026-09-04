from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse

from main.models import Smartphone


class BasketViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = Smartphone.objects.create(
            name='Python для начинающих',
            slug='python-book',
            price=Decimal('1500.00'),
            available=True,
            display_size="6.1",
            ram=8,
            storage=256,
            main_camera_mp=50,
            battery_capacity=5000,
            stock=10,
        )

    def test_add_to_basket(self):
        response = self.client.post(
            reverse('basket:basket_add', args=[self.product.id]),
            {'quantity': 1, 'override': False},
        )
        self.assertEqual(response.status_code, 302)

    def test_basket_session_content(self):
        self.client.post(
            reverse('basket:basket_add', args=[self.product.id]),
            {'quantity': 2, 'override': False},
        )
        session = self.client.session
        self.assertIn('basket', session)
        self.assertEqual(session['basket'][str(self.product.id)]['quantity'], 2)
