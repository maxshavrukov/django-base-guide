from django.conf import settings
from main.models import Product

class Basket:
    def __init__(self, request):
        self.session = request.session
        self.request = request  # Сохраняем request, чтобы проверять пользователя
        basket = self.session.get(settings.BASKET_SESSION_ID)
        if not basket:
            basket = self.session[settings.BASKET_SESSION_ID] = {}
        self.basket = basket
    
    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        if product_id not in self.basket:
            self.basket[product_id] = {'quantity': 0, 'price': str(product.price)}

        if override_quantity:
            self.basket[product_id]['quantity'] = quantity
        else:
            self.basket[product_id]['quantity'] += quantity
        self.save()
    
    def save(self):
        self.session.modified = True
    
    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.basket:
            del self.basket[product_id]
            self.save()
    
    def __iter__(self):
        product_ids = self.basket.keys()
        products = Product.objects.filter(id__in=product_ids)
        basket = self.basket.copy()

        for product in products:
            basket[str(product.id)]['product'] = product

        for item in basket.values():
            item['price'] = float(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.basket.values())
    
    def get_subtotal_price(self):
        """Сумма без учета скидок"""
        return sum(float(item['price']) * item['quantity'] for item in self.basket.values())

    def get_discount_percentage(self):
        """Считает процент скидки (от количества и авторизации)"""
        total_quantity = len(self)
        discount = 0
        
        # Акция 1: Скидка при покупке от 3 товаров (например, 10% или 5% — подставь свой процент)
        # Судя по твоему расчету, ты закладывал 10% за количество или за регистрацию. 
        # Давай разделим: допустим, за 3+ товара даем 10%, а за авторизацию — 5% (или наоборот).
        if total_quantity >= 3:
            discount += 10  # Скидка за 3+ товара
            
        # Акция 2: Скидка для зарегистрированных пользователей
        if self.request.user.is_authenticated:
            discount += 5   # Скидка за авторизацию
            
        return min(discount, 25) # Ограничение максимальной скидки

    def get_total_price(self):
        """Итоговая сумма с учетом скидки (считается от базовой суммы)"""
        subtotal = self.get_subtotal_price()
        discount = self.get_discount_percentage()
        
        if discount > 0:
            # Считаем единой скидкой от базовой суммы (subtotal)
            total = subtotal * (1 - discount / 100)
            return round(total, 2)
        return round(subtotal, 2)
    
    def clear(self):
        del self.session[settings.BASKET_SESSION_ID]
        self.save()

    def get_basket_details(self):
        """Возвращает детальную информацию о суммах и примененных скидках"""
        subtotal = self.get_subtotal_price()
        total_quantity = len(self)
        
        applied_discounts = []
        discount_percent = 0
        
        # Проверяем скидку за количество (от 3 товаров)
        if total_quantity >= 3:
            discount_percent += 10
            applied_discounts.append('10% от 3 товаров')
            
        # Проверяем скидку за регистрацию
        if self.request.user.is_authenticated:
            discount_percent += 5
            applied_discounts.append('5% за регистрацию')
            
        discount_percent = min(discount_percent, 25)
        
        # Считаем сумму скидки в гривнах
        discount_amount = round(subtotal * (discount_percent / 100), 2)
        total_price = round(subtotal - discount_amount, 2)
        
        return {
            'subtotal': subtotal,
            'discount_percent': discount_percent,
            'discount_amount': discount_amount,
            'total_price': total_price,
            'applied_discounts': applied_discounts,
        }