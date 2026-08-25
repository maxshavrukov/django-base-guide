from django.urls import path
from . import views

# Задаем базовое пространство имен для путей приложения
app_name = 'wishlist'

urlpatterns = [
    # Главная страница избранного (url: /wishlist/)
    path('', views.wishlist_detail, name='wishlist_detail'),
    
    # Добавление товара в избранное (url: /wishlist/add/ID/)
    path('add/<int:product_id>/', views.wishlist_add, name='wishlist_add'),
    
    # Удаление товара из избранного (url: /wishlist/remove/ID/)
    path('remove/<int:product_id>/', views.wishlist_remove, name='wishlist_remove'),
]