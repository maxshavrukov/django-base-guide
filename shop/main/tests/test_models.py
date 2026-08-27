from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from main.models import Category, Product, Banner

class CategoryModelTest(TestCase):
    def test_category_creation(self):
        """Проверяем создание категории и её строковое представление"""
        category = Category.objects.create(name='Смартфоны', slug='smartphones')
        self.assertEqual(str(category), 'Смартфоны')
        self.assertEqual(category.slug, 'smartphones')

    def test_category_absolute_url(self):
        """Проверяем генерацию абсолютного URL для категории"""
        category = Category.objects.create(name='Ноутбуки', slug='laptops')
        expected_url = reverse('main:product_list_by_category', args=[category.slug])
        self.assertEqual(category.get_absolute_url(), expected_url)


class ProductModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Создаем категорию один раз для тестов этого класса (это быстрее, чем создавать перед каждым тестом)
        cls.category = Category.objects.create(name='Электроника', slug='electronics')
        cls.product = Product.objects.create(
            category=cls.category,
            name='Test Phone',
            slug='test-phone',
            price=Decimal('999.99'),
            available=True
        )

    def test_product_creation(self):
        """Проверяем поля продукта, связь с категорий и значения по умолчанию"""
        self.assertEqual(str(self.product), 'Test Phone')
        self.assertEqual(self.product.category, self.category)
        self.assertEqual(self.product.price, Decimal('999.99'))
        self.assertTrue(self.product.available)

    def test_product_absolute_url(self):
        """Проверяем генерацию абсолютного URL для детальной страницы продукта"""
        expected_url = reverse('main:product_detail', args=[self.product.id, self.product.slug])
        self.assertEqual(self.product.get_absolute_url(), expected_url)


class BannerModelTest(TestCase):
    def test_banner_creation(self):
        """Проверяем создание баннера и дефолтные значения"""
        banner = Banner.objects.create(
            title='Летняя распродажа',
            subtitle='Скидки до 50%',
            link='/catalog/'
        )
        self.assertEqual(str(banner), 'Летняя распродажа')
        self.assertTrue(banner.is_active)  # Проверяем дефолтное значение True
        self.assertEqual(banner.link, '/catalog/')