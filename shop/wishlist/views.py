from django.shortcuts import redirect, render
from .wishlist import Wishlist
from main.models import Product

# Отображение страницы со списком избранных товаров
def wishlist_detail(request):
    wishlist = Wishlist(request)
    return render(request, 'wishlist/wishlist_detail.html', {'wishlist': wishlist})

# Добавление товара в избранное по ID
def wishlist_add(request, product_id):
    wishlist = Wishlist(request)
    wishlist.add(product_id)
    # Возвращаем пользователя на ту же страницу, откуда он нажал кнопку
    return redirect(request.META.get('HTTP_REFERER', 'main:product_list'))

# Удаление товара из избранного
def wishlist_remove(request, product_id):
    wishlist = Wishlist(request)
    wishlist.remove(product_id)
    # Возвращаем пользователя на ту же страницу
    return redirect(request.META.get('HTTP_REFERER', 'main:product_list'))