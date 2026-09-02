from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse

from main.models import Smartphone


class BasketViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = Smartphone.objects.create(
            name='Смартфон',
            slug='smartphone',
            price=Decimal('25000.00'),
            available=True,
            stock=10,
        )

    def test_basket_detail_view(self):
        response = self.client.get(reverse('basket:basket_detail'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'basket/basket_detail.html')

    def test_basket_add_ajax(self):
        response = self.client.post(
            reverse('basket:basket_add', args=[self.product.id]),
            {'quantity': 1, 'override': False},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['basket_len'], 1)
        self.assertEqual(data['total_price'], '25000.00')
        self.assertEqual(data['items'][0]['product_id'], self.product.id)


    def test_basket_add_ajax_returns_discount_breakdown(self):
        self.product.discount = 20
        self.product.save(update_fields=['discount'])
        response = self.client.post(
            reverse('basket:basket_add', args=[self.product.id]),
            {'quantity': 2, 'override': False},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['subtotal'], '50000.00')
        self.assertEqual(data['product_discount_amount'], '10000.00')
        self.assertEqual(data['items'][0]['original_price'], '25000.00')
        self.assertEqual(data['items'][0]['product_discount_percent'], 20)
        self.assertEqual(data['items'][0]['price'], '20000.00')

    def test_basket_update_plus_minus(self):
        self.client.post(
            reverse('basket:basket_add', args=[self.product.id]),
            {'quantity': 1, 'override': False},
        )
        self.client.post(
            reverse('basket:basket_update', args=[self.product.id, 'plus'])
        )
        self.client.post(
            reverse('basket:basket_update', args=[self.product.id, 'minus'])
        )
