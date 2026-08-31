from decimal import Decimal

from django.conf import settings

from main.models import Product
from .models import BasketItem


class Basket:
    MAX_QUANTITY = 20

    def __init__(self, request):
        self.session = request.session
        self.request = request
        self.user = request.user if request.user.is_authenticated else None

        if not self.user:
            basket = self.session.get(settings.BASKET_SESSION_ID)
            if basket is None:
                basket = {}
                self.session[settings.BASKET_SESSION_ID] = basket
            self.basket = basket

    def add(self, product, quantity=1, override_quantity=False):
        quantity = int(quantity)
        product_id = str(product.id)

        if self.user:
            basket_item, created = BasketItem.objects.get_or_create(
                user=self.user,
                product=product,
                defaults={'quantity': 0},
            )

            if override_quantity or created:
                new_quantity = quantity
            else:
                new_quantity = basket_item.quantity + quantity

            new_quantity = max(0, min(new_quantity, self.MAX_QUANTITY))

            if new_quantity == 0:
                basket_item.delete()
            else:
                basket_item.quantity = new_quantity
                basket_item.save(update_fields=['quantity'])
            return

        if product_id not in self.basket:
            self.basket[product_id] = {
                'quantity': 0,
                # For guests keep the base price snapshot; current Product.discount
                # is applied dynamically when the basket is rendered/calculated.
                'price': str(product.price),
            }

        if override_quantity:
            new_quantity = quantity
        else:
            new_quantity = self.basket[product_id]['quantity'] + quantity

        new_quantity = max(0, min(new_quantity, self.MAX_QUANTITY))

        if new_quantity == 0:
            del self.basket[product_id]
        else:
            self.basket[product_id]['quantity'] = new_quantity

        self.save()

    def change_quantity(self, product, delta):
        """Change quantity consistently for guests and authenticated users."""
        delta = int(delta)

        if self.user:
            item = BasketItem.objects.filter(
                user=self.user,
                product=product,
            ).first()
            if not item:
                return

            new_quantity = max(0, min(item.quantity + delta, self.MAX_QUANTITY))
            if new_quantity == 0:
                item.delete()
            else:
                item.quantity = new_quantity
                item.save(update_fields=['quantity'])
            return

        product_id = str(product.id)
        if product_id not in self.basket:
            return

        new_quantity = max(
            0,
            min(self.basket[product_id]['quantity'] + delta, self.MAX_QUANTITY),
        )

        if new_quantity == 0:
            del self.basket[product_id]
        else:
            self.basket[product_id]['quantity'] = new_quantity

        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id)

        if self.user:
            BasketItem.objects.filter(user=self.user, product=product).delete()
        elif product_id in self.basket:
            del self.basket[product_id]
            self.save()

    @staticmethod
    def _product_price(product):
        """Current selling price after the product-specific discount."""
        return product.get_discounted_price()

    def __iter__(self):
        if self.user:
            basket_items = (
                BasketItem.objects
                .filter(user=self.user)
                .select_related('product', 'product__brand')
                .order_by('created_at', 'id')
            )
            for item in basket_items:
                product = item.product
                price = self._product_price(product)
                yield {
                    'product': product,
                    'quantity': item.quantity,
                    'price': price,
                    'original_price': product.price,
                    'product_discount_percent': product.discount_percent,
                    'product_discount_amount': product.get_discount_amount(),
                    'total_price': price * item.quantity,
                }
            return

        product_ids = list(self.basket.keys())
        if not product_ids:
            return

        products = Product.objects.filter(id__in=product_ids).select_related('brand')
        product_map = {str(product.id): product for product in products}

        for product_id in product_ids:
            product = product_map.get(product_id)
            if not product:
                continue

            quantity = self.basket[product_id]['quantity']
            price = self._product_price(product)
            yield {
                'product': product,
                'quantity': quantity,
                'price': price,
                'original_price': product.price,
                'product_discount_percent': product.discount_percent,
                'product_discount_amount': product.get_discount_amount(),
                'total_price': price * quantity,
            }

    def __len__(self):
        if self.user:
            return sum(
                item.quantity
                for item in BasketItem.objects.filter(user=self.user).only('quantity')
            )
        return sum(item['quantity'] for item in self.basket.values())

    def get_subtotal_price(self):
        """Full catalogue price before product- and promotion-level discounts."""
        total = Decimal('0.00')
        for item in self:
            total += item['original_price'] * item['quantity']
        return total.quantize(Decimal('0.01'))

    def get_product_discount_amount(self):
        """Total discount coming from Product.discount values."""
        total = Decimal('0.00')
        for item in self:
            total += item['product_discount_amount'] * item['quantity']
        return total.quantize(Decimal('0.01'))

    def _get_discount_data(self):
        total_quantity = len(self)
        discount_percent = 0
        applied_discounts = []

        if total_quantity >= 3:
            discount_percent += 10
            applied_discounts.append('10% от 3 товаров')

        if self.user:
            discount_percent += 5
            applied_discounts.append('5% за регистрацию')

        discount_percent = min(discount_percent, 25)
        return discount_percent, applied_discounts

    def get_discount_percentage(self):
        return self._get_discount_data()[0]

    def get_basket_details(self):
        subtotal = self.get_subtotal_price()
        product_discount_amount = self.get_product_discount_amount()
        after_product_discount = subtotal - product_discount_amount

        promo_percent, applied_discounts = self._get_discount_data()
        promo_discount_amount = (
            after_product_discount * Decimal(promo_percent) / Decimal('100')
        ).quantize(Decimal('0.01'))

        total_discount_amount = (
            product_discount_amount + promo_discount_amount
        ).quantize(Decimal('0.01'))
        total_price = (subtotal - total_discount_amount).quantize(Decimal('0.01'))

        return {
            'subtotal': subtotal,
            'product_discount_amount': product_discount_amount,
            'promo_discount_percent': promo_percent,
            'promo_discount_amount': promo_discount_amount,
            'discount_percent': promo_percent,
            'discount_amount': total_discount_amount,
            'total_price': total_price,
            'applied_discounts': applied_discounts,
        }

    def get_total_price(self):
        return self.get_basket_details()['total_price']

    def clear(self):
        if self.user:
            BasketItem.objects.filter(user=self.user).delete()
        else:
            self.session.pop(settings.BASKET_SESSION_ID, None)
            self.save()
