from decimal import Decimal
from django.conf import settings
from main.models import Product
from .models import BasketItem  # Модель в БД

class Basket:
    def __init__(self, request):
        self.session = request.session
        self.request = request  # Сохраняем request для проверки пользователя и скидок
        self.user = request.user if request.user.is_authenticated else None
        
        if not self.user:
            basket = self.session.get(settings.BASKET_SESSION_ID)
            if not basket:
                basket = self.session[settings.BASKET_SESSION_ID] = {}
            self.basket = basket
    
    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        
        if self.user:
            # Сохранение в базу данных для авторизованного
            basket_item, created = BasketItem.objects.get_or_create(
                user=self.user, 
                product=product,
                defaults={'quantity': 0} # Указываем 0, чтобы get_or_create не подставлял default=1 раньше времени
            )
            
            if created:
                # Если товара еще не было в БД, устанавливаем переданное количество
                basket_item.quantity = quantity
            else:
                # Если товар уже был в базе
                if override_quantity:
                    basket_item.quantity = quantity
                else:
                    basket_item.quantity += quantity
            basket_item.save()
        else:
            # Сохранение в сессию для гостя (здесь у вас всё работало верно)
            if product_id not in self.basket:
                self.basket[product_id] = {
                    'quantity': 0, 
                    'price': str(product.price)
                }

            if override_quantity:
                self.basket[product_id]['quantity'] = quantity
            else:
                self.basket[product_id]['quantity'] += quantity
            self.save()
    
    def save(self):
        # Помечаем сессию как измененную, чтобы Django сохранил её
        self.session.modified = True
    
    def remove(self, product):
        product_id = str(product.id)
        
        if self.user:
            BasketItem.objects.filter(user=self.user, product=product).delete()
        else:
            if product_id in self.basket:
                del self.basket[product_id]
                self.save()
    
    def __iter__(self):
        """
        Перебирает товары в корзине с сохранением порядка их добавления 
        и подтягивает актуальные объекты Product из базы данных.
        """
        if self.user:
            basket_items = BasketItem.objects.filter(user=self.user).select_related('product')
            for item in basket_items:
                yield {
                    'product': item.product,
                    'quantity': item.quantity,
                    'price': item.product.price,
                    'total_price': item.product.price * item.quantity
                }
        else:
            product_ids = self.basket.keys()
            products = Product.objects.filter(id__in=product_ids)
            
            # Создаем словарь для быстрого поиска товаров
            product_map = {str(p.id): p for p in products}

            for product_id in product_ids:
                if product_id in product_map:
                    # Создаем копию словаря из сессии, чтобы не мутировать оригинал
                    item = self.basket[product_id].copy()
                    item['product'] = product_map[product_id]
                    item['price'] = Decimal(item['price'])
                    item['total_price'] = item['price'] * item['quantity']
                    yield item

    def __len__(self):
        if self.user:
            items = BasketItem.objects.filter(user=self.user)
            return sum(item.quantity for item in items)
        return sum(item['quantity'] for item in self.basket.values())
    
    def get_subtotal_price(self):
        """Сумма без учета скидок"""
        if self.user:
            items = BasketItem.objects.filter(user=self.user).select_related('product')
            total = sum((item.product.price * item.quantity for item in items), Decimal('0.00'))
        else:
            total = sum((Decimal(item['price']) * item['quantity'] for item in self.basket.values()), Decimal('0.00'))
        
        return total.quantize(Decimal('0.01'))

    def _get_discount_data(self):
        """Вспомогательный метод для расчета скидок (избегаем дублирования кода)"""
        total_quantity = len(self)
        discount_percent = 0
        applied_discounts = []
        
        # Акция 1: Скидка при покупке от 3 товаров
        if total_quantity >= 3:
            discount_percent += 10
            applied_discounts.append('10% от 3 товаров')
            
        # Акция 2: Скидка для авторизованных пользователей
        if self.request.user.is_authenticated:
            discount_percent += 5
            applied_discounts.append('5% за регистрацию')
            
        # Ограничение максимальной скидки (например, не более 25%)
        discount_percent = min(discount_percent, 25)
        return discount_percent, applied_discounts

    def get_discount_percentage(self):
        """Возвращает общий процент скидки"""
        percent, _ = self._get_discount_data()
        return percent

    def get_basket_details(self):
        """Возвращает детальную информацию о суммах, процентах и примененных скидках"""
        subtotal = self.get_subtotal_price()
        discount_percent, applied_discounts = self._get_discount_data()
        
        # Считаем сумму скидки
        discount_amount = (subtotal * Decimal(discount_percent) / Decimal(100)).quantize(Decimal('0.01'))
        total_price = (subtotal - discount_amount).quantize(Decimal('0.01')) # <--- И здесь тоже
        
        return {
            'subtotal': subtotal,
            'discount_percent': discount_percent,
            'discount_amount': discount_amount,
            'total_price': total_price,
            'applied_discounts': applied_discounts,
        }

    def get_total_price(self):
        """Итоговая сумма с учетом всех скидок"""
        details = self.get_basket_details()
        return details['total_price']
    
    def clear(self):
        """Безопасная очистка корзины"""
        if self.user:
            BasketItem.objects.filter(user=self.user).delete()
        else:
            self.session.pop(settings.BASKET_SESSION_ID, None)
            self.save()