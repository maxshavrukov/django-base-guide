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


    def test_brand_filter_uses_brand_name(self):
        other_brand = Brand.objects.create(name='Other Brand', slug='other-brand')
        other_product = Smartphone.objects.create(
            brand=other_brand,
            group=self.group,
            name='Другой смартфон',
            slug='other-smartphone',
            price=Decimal('600.00'),
            available=True,
            stock=3,
        )
        response = self.client.get(
            reverse('main:product_list_by_category', args=['smartphones']),
            {'brand': self.brand.name},
        )
        self.assertContains(response, self.product.name)
        self.assertNotContains(response, other_product.name)

    def test_catalog_menu_and_sort_markup(self):
        response = self.client.get(reverse('main:product_list_by_category', args=['smartphones']))
        self.assertContains(response, 'catalog-menu--mega')
        self.assertContains(response, 'catalog-menu__panels')
        self.assertContains(response, 'data-catalog-switch="smartphones"')
        self.assertContains(response, 'id="sortMenu"')

    def test_product_detail_does_not_reference_removed_gallery_script(self):
        url = reverse('main:product_detail', args=[self.product.id, self.product.slug])
        response = self.client.get(url)
        self.assertNotContains(response, 'imageGallery.js')
        self.assertContains(response, 'imageModal.js')

    def test_mini_cart_is_click_controlled(self):
        response = self.client.get(reverse('main:product_list'))
        self.assertContains(response, 'id="cartBtn"')
        self.assertContains(response, 'id="miniCart"')
        self.assertNotContains(response, 'header-cart.has-items:hover .mini-cart-dropdown')

    def test_product_detail_page(self):
        url = reverse('main:product_detail', args=[self.product.id, self.product.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
        self.assertEqual(response.context['product'].id, self.product.id)
        self.assertIn('storage_variants', response.context)
        self.assertIn('color_variants', response.context)
