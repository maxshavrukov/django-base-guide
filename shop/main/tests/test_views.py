from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse

from main.models import Brand, Category, Headphone, ProductGroup, Smartphone


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
            display_size="6.1",
            ram=8,
            storage=256,
            main_camera_mp=50,
            battery_capacity=5000,
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
            display_size="6.1",
            ram=8,
            storage=256,
            main_camera_mp=50,
            battery_capacity=5000,
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

    def test_secondary_category_can_include_product_group(self):
        root = Category.objects.get(slug='headphones')
        custom = Category.objects.create(
            name='Беспроводные тест',
            slug='wireless-test',
            parent=root,
        )
        headphone_group = ProductGroup.objects.create(name='Test Headphone Series', slug='test-headphone-series')
        headphone = Headphone.objects.create(
            brand=self.brand,
            group=headphone_group,
            name='Тестовые беспроводные наушники',
            slug='test-wireless-headphones',
            price=Decimal('120.00'),
            available=True,
            stock=5,
            headphone_type='over_ear',
            connection_type='wireless',
        )
        headphone_group.categories.add(custom)

        response = self.client.get(reverse('main:product_list_by_category', args=[custom.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, headphone.name)

    def test_product_group_can_belong_to_multiple_secondary_categories(self):
        root = Category.objects.get(slug='headphones')
        wireless = Category.objects.create(name='Беспроводные multi', slug='wireless-multi', parent=root)
        gaming = Category.objects.create(name='Игровые multi', slug='gaming-multi', parent=root)
        multi_group = ProductGroup.objects.create(name='Multi Headphone Series', slug='multi-headphone-series')
        headphone = Headphone.objects.create(
            brand=self.brand,
            group=multi_group,
            name='Мультикатегорийные наушники',
            slug='multi-category-headphones',
            price=Decimal('130.00'),
            available=True,
            stock=2,
            headphone_type='over_ear',
            connection_type='wireless',
        )
        multi_group.categories.add(wireless, gaming)

        wireless_response = self.client.get(reverse('main:product_list_by_category', args=[wireless.slug]))
        gaming_response = self.client.get(reverse('main:product_list_by_category', args=[gaming.slug]))
        self.assertContains(wireless_response, headphone.name)
        self.assertContains(gaming_response, headphone.name)

    def test_secondary_category_is_available_in_catalog_menu(self):
        root = Category.objects.get(slug='smartphones')
        child = Category.objects.create(name='Флагманские тест', slug='flagship-test', parent=root)
        response = self.client.get(reverse('main:product_list'))
        self.assertContains(response, child.name)

    def test_root_category_is_automatic_for_product_type(self):
        response = self.client.get(reverse('main:product_list_by_category', args=['smartphones']))
        self.assertContains(response, self.product.name)

