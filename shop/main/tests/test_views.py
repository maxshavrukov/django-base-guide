from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from main.models import Category, Product

class MainViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Создаем тестового клиента (он заменяет нам браузер)
        cls.client = Client()
        
        # Создаем категорию и товар, чтобы страница каталога не была пустой
        cls.category = Category.objects.create(name='Одежда', slug='clothes')
        cls.product = Product.objects.create(
            category=cls.category,
            name='Футболка',
            slug='t-shirt',
            price=Decimal('500.00'),
            available=True
        )

    def test_product_list_page(self, ):
        """Проверяем, что страница каталога/главная открывается успешно"""
        # Используем reverse для получения URL по имени из urls.py
        # Обрати внимание: если у тебя главная страница называется иначе (например, 'index' или 'home'), 
        # поменяй имя в кавычках на то, что прописано в твоих urls.py
        url = reverse('main:product_list') 
        response = self.client.get(url)
        
        # Проверяем, что страница ответила со статусом 200 (Всё ок)
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что используется правильный HTML-шаблон
        self.assertTemplateUsed(response, 'main/product/list.html')

    def test_product_detail_page(self):
        """Проверяем, что детальная страница конкретного товара открывается успешно"""
        # Передаем ID и slug товара в reverse
        url = reverse('main:product_detail', args=[self.product.id, self.product.slug])
        response = self.client.get(url)
        
        # Проверяем, что страница ответила со статусом 200
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что на странице отображается название товара
        self.assertContains(response, self.product.name)