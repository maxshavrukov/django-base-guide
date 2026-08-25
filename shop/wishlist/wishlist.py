class Wishlist:
    def __init__(self, request):
        """
        Инициализация избранного. 
        Привязываем корзину/избранное к сессии пользователя, чтобы оно 
        сохранялось, даже когда он переходит по страницам или перезаходит на сайт.
        """
        self.session = request.session
        wishlist = self.session.get('wishlist')
        
        # Если у пользователя еще нет списка избранного в сессии, создаем пустой список
        if not wishlist:
            wishlist = self.session['wishlist'] = []
        self.wishlist = wishlist

    def add(self, product_id):
        """Добавление товара в избранное по его ID"""
        product_id = str(product_id) # Превращаем ID в строку для надежности хранения в сессии
        
        # Если товара еще нет в списке — добавляем его
        if product_id not in self.wishlist:
            self.wishlist.append(product_id)
            self.save()

    def remove(self, product_id):
        """Удаление товара из избранного"""
        product_id = str(product_id)
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
        from main.models import Product  # <-- Тоже проверяем, чтобы было из main, а не products
        product_ids = self.wishlist
        products = Product.objects.filter(id__in=product_ids)
        for product in products:
            yield product

    def __len__(self):
        """Возвращает общее количество товаров в избранном (для счетчика в шапке)"""
        return len(self.wishlist)
    
    def clear(self):
        """Полная очистка избранного"""
        del self.session['wishlist']
        self.save()