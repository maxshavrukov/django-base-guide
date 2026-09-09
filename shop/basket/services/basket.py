from decimal import Decimal
from django.conf import settings

from basket.models import BasketItem
from main.models import CartPromotion, Product
from users.services.bonuses import BonusService


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
                    'product_discount_percent': product.effective_discount_percent,
                    'product_discount_amount': product.get_discount_amount(),
                    'total_price': price * item.quantity,
                }
            return

        product_ids = list(self.basket.keys())
        if not product_ids:
            return

        products = Product.objects.filter(id__in=product_ids).select_related(
            "brand",
            "smartphone",
            "headphone",
            "charger",
            "cable",
            "powerbank",
        )
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
                'product_discount_percent': product.effective_discount_percent,
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

    def get_bonus_requested_amount(self):
        """Requested bonus amount from the current checkout POST.

        No bonus amount is stored in the session: it is recalculated from the
        current basket at checkout time, which avoids stale redemption state.
        """
        if not self.user:
            return 0
        raw = self.request.POST.get("bonus_spend", "") if getattr(self.request, "method", "GET") == "POST" else ""
        try:
            return max(0, int(raw or 0))
        except (TypeError, ValueError):
            return 0

    def get_max_bonus_redemption(self):
        if not self.user:
            return 0
        items = list(self)
        promo_amount = self._get_discount_data()[2]
        # Full-price means no product discount and no cart promotion.
        if promo_amount > 0:
            return 0
        return BonusService.calculate_max_spend(items)

    def get_bonus_available_balance(self):
        if not self.user:
            return 0
        account = BonusService.get_or_create_account(self.user)
        BonusService.ensure_birthday_bonus(self.user)
        return BonusService.get_available_balance(account)

    def get_bonus_discount_amount(self):
        requested = self.get_bonus_requested_amount()
        if requested <= 0:
            return Decimal("0.00")
        allowed = min(requested, self.get_max_bonus_redemption(), self.get_bonus_available_balance())
        return (Decimal(allowed) * BonusService.BONUS_VALUE_UAH).quantize(Decimal("0.01"))

    def _get_discount_data(self):
        items = list(self)
        discount_amount, promotion = CartPromotion.get_best_for_basket(items, user=self.user)
        if not promotion or discount_amount <= 0:
            return 0, [], Decimal('0.00')

        if promotion.rule_type == CartPromotion.RuleType.CART:
            subtotal = sum((item['price'] * item['quantity'] for item in items), Decimal('0.00'))
            percent = promotion.discount_percent
        else:
            subtotal = sum((item['price'] * item['quantity'] for item in items), Decimal('0.00'))
            percent = promotion.discount_percent
        return percent, [promotion.name], discount_amount

    def get_discount_percentage(self):
        return self._get_discount_data()[0]

    def get_basket_details(self):
        subtotal = self.get_subtotal_price()
        product_discount_amount = self.get_product_discount_amount()
        promo_percent, applied_discounts, promo_discount_amount = self._get_discount_data()
        bonus_discount_amount = self.get_bonus_discount_amount()

        total_discount_amount = (
            product_discount_amount + promo_discount_amount + bonus_discount_amount
        ).quantize(Decimal('0.01'))
        total_price = (subtotal - total_discount_amount).quantize(Decimal('0.01'))

        return {
            'subtotal': subtotal,
            'product_discount_amount': product_discount_amount,
            'promo_discount_percent': promo_percent,
            'promo_discount_amount': promo_discount_amount,
            'bonus_discount_amount': bonus_discount_amount,
            'bonus_spend_requested': self.get_bonus_requested_amount(),
            'bonus_available_balance': self.get_bonus_available_balance(),
            'bonus_max_redemption': self.get_max_bonus_redemption(),
            'bonus_rules': BonusService.get_rules(),
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


def get_basket_ajax_payload(basket: Basket) -> dict:
    """Формирует структурированные данные для AJAX-ответов корзины."""
    items_data = []
    for item in basket:
        product = item['product']
        items_data.append({
            'product_id': product.id,
            'name': product.name,
            'price': str(item['price']),
            'original_price': str(item['original_price']),
            'product_discount_percent': item['product_discount_percent'],
            'quantity': item['quantity'],
            'total_price': str(item['total_price']),
            'image_url': product.image.url if product.image else '',
        })

    details = basket.get_basket_details()
    return {
        'status': 'ok',
        'total_price': str(details['total_price']),
        'subtotal': str(details['subtotal']),
        'product_discount_amount': str(details['product_discount_amount']),
        'promo_discount_percent': details['promo_discount_percent'],
        'promo_discount_amount': str(details['promo_discount_amount']),
        'bonus_discount_amount': str(details['bonus_discount_amount']),
        'bonus_available_balance': details['bonus_available_balance'],
        'bonus_max_redemption': details['bonus_max_redemption'],
        'discount_amount': str(details['discount_amount']),
        'basket_len': len(basket),
        'items': items_data,
    }