from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from main.models import Category, Product

class BasketViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Электроника', slug='electronics')
        self.product = Product.objects.create(
            category=self.category,
            name='Смартфон',
            slug='smartphone',
            price=Decimal('25000.00'),
            available=True
        )

    def test_basket_detail_view(self):
        """Проверяем, что страница корзины открывается успешно"""
        url = reverse('basket:basket_detail')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'basket/basket_detail.html')

    def test_basket_add_view(self):
        """Проверяем стандартное добавление товара в корзину (с редиректом)"""
        url = reverse('basket:basket_add', args=[self.product.id])
        # Отправляем POST с количеством
        response = self.client.post(url, {'quantity': 2, 'override': False})
        # Ожидаем редирект (302)
        self.assertEqual(response.status_code, 302)

    def test_basket_add_ajax(self):
        """Проверяем добавление товара через AJAX-запрос (возвращает JSON)"""
        url = reverse('basket:basket_add', args=[self.product.id])
        # Имитируем AJAX-запрос с помощью заголовка HTTP_X_REQUESTED_WITH
        response = self.client.post(
            url, 
            {'quantity': 1, 'override': False}, 
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        
        # Проверяем структуру JSON-ответа
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['basket_len'], 1)
        self.assertEqual(data['total_price'], '25000.00')

    def test_basket_remove_view(self):
        """Проверяем удаление товара из корзины"""
        # Сначала добавляем товар
        add_url = reverse('basket:basket_add', args=[self.product.id])
        self.client.post(add_url, {'quantity': 1, 'override': False})

        # Затем удаляем его
        remove_url = reverse('basket:basket_remove', args=[self.product.id])
        response = self.client.post(remove_url)
        self.assertEqual(response.status_code, 302)

    def test_basket_update_plus_minus(self):
        """Проверяем изменение количества товара (кнопки плюс и минус)"""
        # Добавляем товар (количество: 1)
        add_url = reverse('basket:basket_add', args=[self.product.id])
        self.client.post(add_url, {'quantity': 1, 'override': False})

        # Увеличиваем количество ('plus')
        update_plus_url = reverse('basket:basket_update', args=[self.product.id, 'plus'])
        response = self.client.post(update_plus_url)
        self.assertEqual(response.status_code, 302)

        # Уменьшаем количество ('minus')
        update_minus_url = reverse('basket:basket_update', args=[self.product.id, 'minus'])
        response = self.client.post(update_minus_url)
        self.assertEqual(response.status_code, 302)