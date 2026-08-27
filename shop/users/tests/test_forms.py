from django.test import TestCase
from django.contrib.auth.models import User
from users.forms import UserRegistrationForm

class UserRegistrationFormTest(TestCase):
    def test_registration_form_unique_email(self):
        """Проверяем, что форма выдает ошибку при попытке зарегистрировать уже занятый Email"""
        # Создаем существующего пользователя
        User.objects.create_user(username='olduser', email='existing@example.com', password='password123')
        
        # Пытаемся передать тот же email в форму
        form_data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'password1': 'NewPassword123!',
            'password2': 'NewPassword123!',
        }
        form = UserRegistrationForm(data=form_data)
        
        # Форма не должна пройти валидацию
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)