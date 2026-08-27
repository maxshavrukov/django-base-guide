from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from orders.models import Order

class UserViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')

    def test_auth_view_redirect_authenticated(self):
        """Авторизованный пользователь при попытке зайти на страницу входа/регистрации перенаправляется на каталог"""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('users:auth'))
        self.assertRedirects(response, reverse('main:product_list'))

    def test_register_view_success(self):
        """Проверяем успешную регистрацию нового пользователя через представление"""
        response = self.client.post(reverse('users:register'), {
            'username': 'brandnewuser',
            'email': 'brandnew@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        # После успешной регистрации происходит редирект и автоматический логин[cite: 6]
        self.assertRedirects(response, reverse('main:product_list'))
        self.assertTrue(User.objects.filter(username='brandnewuser').exists())

    def test_user_login_success(self):
        """Проверяем успешный вход пользователя в систему"""
        response = self.client.post(reverse('users:login'), {
            'username': 'testuser',
            'password': 'password123'
        })
        self.assertRedirects(response, reverse('main:product_list'))

    def test_profile_view_access_control(self):
        """Профиль доступен только авторизованным пользователям"""
        # Гость перенаправляется (код 302)
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 302)

        # Авторизованный пользователь получает страницу профиля (код 200)[cite: 6]
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')

    def test_order_list_view(self):
        """Проверяем, что в личным кабинете отображаются заказы именно текущего пользователя"""
        # Создаем заказ для нашего тестового юзера
        Order.objects.create(
            user=self.user,
            first_name='Тест',
            email='test@example.com',
            phone='+380501112233',
            address='Тестовый адрес'
        )
        
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('users:order_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/order_list.html')
        # Проверяем, что заказ передан в контекст шаблона
        self.assertEqual(len(response.context['orders']), 1)