from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse

from main.models import Brand, ProductGroup, Smartphone


class MainViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        cls.brand = Brand.objects.create(name='Test Brand', slug='test-brand')
        cls.group = ProductGroup.objects.create(name='Test Series', slug='test-series')
        cls.product = Smartphone.objects.create(
            brand=cls.brand,
            group=cls.group,
            name='Тестовый смартфон',
            slug='test-smartphone',
            price=Decimal('500.00'),
            available=True,
            stock=3,
        )

    def test_product_list_page(self):
        response = self.client.get(reverse('main:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/product/list.html')
        self.assertContains(response, self.product.name)

    def test_category_page(self):
        response = self.client.get(
            reverse('main:product_list_by_category', args=['smartphones'])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)

    def test_group_page(self):
        response = self.client.get(
            reverse('main:product_list_by_group', args=[self.group.slug])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)

    def test_brand_page(self):
        response = self.client.get(
            reverse('main:product_list_by_brand', args=[self.brand.slug])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)

    def test_discounted_price_filter(self):
        self.product.discount = 20
        self.product.save(update_fields=['discount'])
        response = self.client.get(
            reverse('main:product_list_by_category', args=['smartphones']),
            {'price_max': '450'},
        )
        self.assertContains(response, self.product.name)

    def test_price_filter(self):
        response = self.client.get(
            reverse('main:product_list_by_category', args=['smartphones']),
            {'price_max': '400'},
        )
        self.assertNotContains(response, self.product.name)

    def test_product_detail_page(self):
        url = reverse('main:product_detail', args=[self.product.id, self.product.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
        self.assertEqual(response.context['variants'][0].id, self.product.id)
