from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from main.models import Category, Product
from basket.models import BasketItem

# Получаем модель пользователя, которая используется в проекте
User = get_user_model()

class BasketItemModelTest(TestCase):
    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(username='testuser', password='password123')
        
        # Создаем категорию и товар для корзины
        self.category = Category.objects.create(name='Гаджеты', slug='gadgets')
        self.product = Product.objects.create(
            category=self.category,
            name='Беспроводные наушники',
            slug='wireless-headphones',
            price=Decimal('3500.00'),
            available=True
        )

    def test_basket_item_creation(self):
        """Проверяем, что товар успешно добавляется в корзину пользователя и работает __str__"""
        basket_item = BasketItem.objects.create(
            user=self.user,
            product=self.product,
            quantity=3
        )
        
        # Проверяем поля
        self.assertEqual(basket_item.user, self.user)
        self.assertEqual(basket_item.product, self.product)
        self.assertEqual(basket_item.quantity, 3)
        
        # Проверяем строковое представление (__str__)
        expected_str = 'testuser - Беспроводные наушники (3)'
        self.assertEqual(str(basket_item), expected_str)

    def test_basket_item_unique_together(self):
        """Проверяем ограничение unique_together: нельзя создать дубликат той же позиции для одного юзера"""
        from django.db.utils import IntegrityError
        
        # Создаем первый элемент
        BasketItem.objects.create(user=self.user, product=self.product, quantity=1)
        
        # Пытаемся создать второй точно такой же элемент для того же юзера.
        # Ожидаем, что база данных выбросит ошибку целостности (IntegrityError) из-за unique_together.
        with self.assertRaises(IntegrityError):
            BasketItem.objects.create(user=self.user, product=self.product, quantity=2)