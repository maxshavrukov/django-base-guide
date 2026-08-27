from main.models import Product
from .models import WishlistItem # Модель в базе данных (создадим ниже, если её еще нет)

class Wishlist:
    def __init__(self, request):
        """
        Инициализация избранного. 
        Если пользователь авторизован — работаем с базой данных.
        Если гость — работаем с сессией.
        """
        self.session = request.session
        self.request = request
        self.user = request.user if request.user.is_authenticated else None
        
        if not self.user:
            wishlist = self.session.get('wishlist')
            if not wishlist:
                wishlist = self.session['wishlist'] = []
            self.wishlist = wishlist

    def add(self, product_id):
        """Добавление товара в избранное по его ID"""
        product_id = str(product_id)
        
        if self.user:
            # Сохраняем в базу данных для авторизованного
            product = Product.objects.get(id=product_id)
            WishlistItem.objects.get_or_create(user=self.user, product=product)
        else:
            # Сохраняем в сессию для гостя
            if product_id not in self.wishlist:
                self.wishlist.append(product_id)
                self.save()

    def remove(self, product_id):
        """Удаление товара из избранного"""
        product_id = str(product_id)
        
        if self.user:
            # Удаляем из базы данных
            WishlistItem.objects.filter(user=self.user, product_id=product_id).delete()
        else:
            # Удаляем из сессии
            if product_id in self.wishlist:
                self.wishlist.remove(product_id)
                self.save()

    def save(self):
        """Помечаем сессию как измененную, чтобы Django сохранил данные"""
        self.session.modified = True

    def __iter__(self):
        """
        Магический метод для перебора товаров в избранном
        """
        if self.user:
            # Берем товары из базы данных для авторизованного
            product_ids = WishlistItem.objects.filter(user=self.user).values_list('product_id', flat=True)
            products = Product.objects.filter(id__in=product_ids)
        else:
            # Берем товары из сессии для гостя
            products = Product.objects.filter(id__in=self.wishlist)
            
        for product in products:
            yield product

    def __len__(self):
        """Возвращает общее количество товаров в избранном (для счетчика в шапке)"""
        if self.user:
            return WishlistItem.objects.filter(user=self.user).count()
        return len(self.wishlist)
    
    def clear(self):
        """Полная очистка избранного"""
        if self.user:
            WishlistItem.objects.filter(user=self.user).delete()
        else:
            if 'wishlist' in self.session:
                del self.session['wishlist']
                self.save()