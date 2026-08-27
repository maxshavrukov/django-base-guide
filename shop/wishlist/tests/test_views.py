from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from main.models import Category, Product
from wishlist.models import WishlistItem

User = get_user_model()

class WishlistViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.category = Category.objects.create(name='Одежда', slug='clothes')
        self.product = Product.objects.create(
            category=self.category,
            name='Куртка',
            slug='jacket',
            price=Decimal('3000.00'),
            available=True
        )

    def test_wishlist_detail_view(self):
        """Проверяем успешное открытие страницы избранного[cite: 8]"""
        response = self.client.get(reverse('wishlist:wishlist_detail'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wishlist/wishlist_detail.html')

    def test_guest_wishlist_add_and_remove(self):
        """Проверяем добавление и удаление товара в избранное для неавторизованного гостя через сессию[cite: 8, 9]"""
        add_url = reverse('wishlist:wishlist_add', args=[self.product.id])
        response = self.client.get(add_url)
        # Представление возвращает редирект (302) на HTTP_REFERER[cite: 8]
        self.assertEqual(response.status_code, 302)

        # Проверяем, что товар появился в избранном (через контекст страницы детализации)
        detail_response = self.client.get(reverse('wishlist:wishlist_detail'))
        self.assertEqual(len(detail_response.context['wishlist']), 1)

        # Удаляем товар из избранного[cite: 8, 9]
        remove_url = reverse('wishlist:wishlist_remove', args=[self.product.id])
        self.client.get(remove_url)
        
        detail_response_after = self.client.get(reverse('wishlist:wishlist_detail'))
        self.assertEqual(len(detail_response_after.context['wishlist']), 0)

    def test_authenticated_wishlist_add_and_remove(self):
        """Проверяем добавление и удаление товара в избранное для авторизованного пользователя в БД[cite: 7, 8, 9]"""
        self.client.login(username='testuser', password='password123')
        
        add_url = reverse('wishlist:wishlist_add', args=[self.product.id])
        self.client.get(add_url)
        
        # Проверяем, что запись сохранилась в базе данных[cite: 7, 9]
        self.assertTrue(WishlistItem.objects.filter(user=self.user, product=self.product).exists())

        # Удаляем товар из базы данных[cite: 8, 9]
        remove_url = reverse('wishlist:wishlist_remove', args=[self.product.id])
        self.client.get(remove_url)
        
        self.assertFalse(WishlistItem.objects.filter(user=self.user, product=self.product).exists())