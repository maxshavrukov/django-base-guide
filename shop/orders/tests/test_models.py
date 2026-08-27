from decimal import Decimal
from django.test import TestCase
from main.models import Category, Product
from orders.models import Order, OrderItem

class OrderModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Техника', slug='tech')
        self.product = Product.objects.create(
            category=self.category,
            name='Планшет',
            slug='tablet',
            price=Decimal('5000.00'),
            available=True
        )
        self.order = Order.objects.create(
            first_name='Ольга',
            email='olga@example.com',
            phone='+380509876543',
            address='пр. Шевченко, 15'
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            price=Decimal('5000.00'),
            quantity=2
        )

    def test_order_cost_calculation(self):
        """Проверяем расчет общей стоимости заказа и стоимости позиции"""
        self.assertEqual(str(self.order), f'Order {self.order.id}')
        self.assertEqual(self.order_item.get_cost(), Decimal('10000.00'))
        self.assertEqual(self.order.get_total_cost(), Decimal('10000.00'))