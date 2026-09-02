from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from main.models import Smartphone
from orders.models import Order

class OrderCreateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = Smartphone.objects.create(
            name='Мяч',
            slug='ball',
            price=Decimal('600.00'),
            available=True
        )

    def test_order_creation_success(self):
        """Проверяем успешное оформление заказа с товарами из корзины"""
        # 1. Помещаем товар в корзину
        basket_add_url = reverse('basket:basket_add', args=[self.product.id])
        self.client.post(basket_add_url, {'quantity': 3, 'override': False})

        # 2. Отправляем POST-запрос на создание заказа с данными формы
        order_create_url = reverse('orders:order_create')
        form_data = {
            'first_name': 'Дмитрий',
            'email': 'dmitriy@example.com',
            'phone': '+380671112233',
            'address': 'ул. Космическая, 5',
            'comment': 'Срочная доставка'
        }
        response = self.client.post(order_create_url, data=form_data)

        # 3. Проверяем, что страница успешного оформления вернула статус 200 и нужный шаблон
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders/created.html')

        # 4. Проверяем, что заказ реально сохранился в базе данных со всеми связями
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.first_name, 'Дмитрий')
        self.assertEqual(order.items.count(), 1)
        
        item = order.items.first()
        self.assertEqual(item.product_id, self.product.id)
        self.assertEqual(item.quantity, 3)