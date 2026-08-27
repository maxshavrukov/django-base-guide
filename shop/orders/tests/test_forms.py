from django.test import TestCase
from orders.forms import OrderCreateForm

class OrderCreateFormTest(TestCase):
    def test_order_form_valid(self):
        """Проверяем форму с правильными и полными данными"""
        form_data = {
            'first_name': 'Алексей',
            'email': 'alexey@example.com',
            'phone': '+380501234567',
            'address': 'ул. Победы, 10',
            'comment': 'Домофон не работает'
        }
        form = OrderCreateForm(data=form_data)
        # Форма должна быть валидной
        self.assertTrue(form.is_valid())

    def test_order_form_missing_required_fields(self):
        """Проверяем, что форма выдает ошибки, если обязательные поля не заполнены или email некорректный"""
        form_data = {
            'first_name': '',  # Пустое обязательное поле
            'email': 'bad-email-format',  # Неверный формат email
            'phone': '',       # Пустое обязательное поле
            'address': '',     # Пустое обязательное поле
        }
        form = OrderCreateForm(data=form_data)
        # Форма НЕ должна быть валидной
        self.assertFalse(form.is_valid())
        
        # Проверяем, что ошибки прилетели именно для этих полей
        self.assertIn('first_name', form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('phone', form.errors)
        self.assertIn('address', form.errors)