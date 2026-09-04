from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from main.models import Banner, Brand, ProductGroup, Smartphone


class ProductModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.brand = Brand.objects.create(name='Test Brand', slug='test-brand')
        cls.group = ProductGroup.objects.create(name='Test Series', slug='test-series')
        cls.product = Smartphone.objects.create(
            brand=cls.brand,
            group=cls.group,
            name='Test Phone',
            slug='test-phone',
            price=Decimal('999.99'),
            discount=10,
            stock=5,
            available=True,
            display_size="6.1",
            ram=8,
            storage=256,
            main_camera_mp=50,
            battery_capacity=5000,
        )

    def test_product_creation_and_discount(self):
        self.assertEqual(str(self.product), 'Test Phone')
        self.assertEqual(self.product.price, Decimal('999.99'))
        self.assertEqual(self.product.discount_percent, 10)
        self.assertEqual(self.product.get_discounted_price(), Decimal('899.99'))
        self.assertTrue(self.product.available)

    def test_product_absolute_url(self):
        expected_url = reverse('main:product_detail', args=[self.product.id, self.product.slug])
        self.assertEqual(self.product.get_absolute_url(), expected_url)

    def test_group_absolute_url(self):
        self.assertEqual(
            self.group.get_absolute_url(),
            reverse('main:product_list_by_group', args=[self.group.slug]),
        )


class BannerModelTest(TestCase):
    def test_banner_creation(self):
        banner = Banner.objects.create(
            title='Летняя распродажа',
            subtitle='Скидки до 50%',
            link='/catalog/',
        )
        self.assertEqual(str(banner), 'Летняя распродажа')
        self.assertTrue(banner.is_active)
