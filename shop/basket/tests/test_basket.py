from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from main.models import Category, Product

class BasketViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Книги', slug='books')
        self.product = Product.objects.create(
            category=self.category,
            name='Python для начинающих',
            slug='python-book',
            price=Decimal('1500.00'),
            available=True
        )

    def test_add_to_basket(self):
        """Проверяем добавление товара в корзину и редирект"""
        url = reverse('basket:basket_add', args=[self.product.id])
        response = self.client.post(url, {'quantity': 1, 'override': False})
        self.assertEqual(response.status_code, 302)

    def test_basket_session_content(self):
        """Проверяем, что товар реально записывается в сессию корзины"""
        url = reverse('basket:basket_add', args=[self.product.id])
        
        # Добавляем 2 штуки товара через POST-запрос
        self.client.post(url, {'quantity': 2, 'override': False})
        
        # Достаем сессию из тестового клиента
        session = self.client.session
        
        # В зависимости от настроек проекта ключ сессии корзины может называться 'basket' или 'cart'.
        # Проверим, какой из них присутствует в сессии:
        basket_key = 'basket' if 'basket' in session else 'cart'
        
        # Проверяем, что сессия содержит корзину
        self.assertIn(basket_key, session)
        basket_data = session[basket_key]
        
        # Проверяем, что наш товар (по его ID) появился в корзине и количество равно 2
        product_id_str = str(self.product.id)
        self.assertIn(product_id_str, basket_data)
        self.assertEqual(basket_data[product_id_str]['quantity'], 2)