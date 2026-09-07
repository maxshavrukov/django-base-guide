from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse

from main.models import Banner, CartPromotion, Smartphone


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


class BasketPromotionIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = Smartphone.objects.create(
            name='Promo Phone',
            slug='promo-phone',
            price=Decimal('1000.00'),
            available=True,
            display_size='6.1',
            ram=8,
            storage=256,
            main_camera_mp=50,
            battery_capacity=5000,
            stock=10,
        )

    def test_no_cart_promotion_means_no_extra_discount(self):
        self.client.post(
            reverse('basket:basket_add', args=[self.product.id]),
            {'quantity': 3, 'override': False},
        )
        response = self.client.get(reverse('basket:basket_detail'))
        self.assertEqual(response.context['basket_details']['promo_discount_amount'], Decimal('0.00'))

    def test_active_banner_alone_does_not_create_discount(self):
        Banner.objects.create(title='Sony Week', is_active=True)
        self.client.post(
            reverse('basket:basket_add', args=[self.product.id]),
            {'quantity': 3, 'override': False},
        )
        response = self.client.get(reverse('basket:basket_detail'))
        self.assertEqual(response.context['basket_details']['promo_discount_amount'], Decimal('0.00'))

    def test_active_cart_promotion_is_used(self):
        CartPromotion.objects.create(
            name='Три товара — скидка',
            rule_type=CartPromotion.RuleType.CHEAPEST,
            discount_percent=10,
            min_quantity=3,
        )
        self.client.post(
            reverse('basket:basket_add', args=[self.product.id]),
            {'quantity': 3, 'override': False},
        )
        response = self.client.get(reverse('basket:basket_detail'))
        self.assertEqual(response.context['basket_details']['promo_discount_amount'], Decimal('100.00'))
