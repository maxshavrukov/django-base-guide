from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from main.models import Brand, Category, CartPromotion, Headphone, ProductGroup, ProductPromotion, Smartphone

User = get_user_model()


class ProductPromotionTest(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name='Sony', slug='sony')
        self.group = ProductGroup.objects.create(name='WH-CH720N', slug='wh-ch720n')
        self.product = Headphone.objects.create(
            brand=self.brand, group=self.group, name='Sony WH-CH720N Black', slug='sony-wh-ch720n-black',
            price=Decimal('5000.00'), stock=5, available=True, headphone_type='over_ear', connection_type='wireless'
        )

    def test_brand_promotion_changes_effective_price(self):
        ProductPromotion.objects.create(name='Sony Week', target_type='brand', brand=self.brand, discount_percent=7)
        self.assertEqual(self.product.effective_discount_percent, 7)
        self.assertEqual(self.product.get_discounted_price(), Decimal('4650.00'))

    def test_inactive_or_expired_promotion_does_not_apply(self):
        ProductPromotion.objects.create(name='Disabled', target_type='brand', brand=self.brand, discount_percent=7, is_active=False)
        self.assertEqual(self.product.effective_discount_percent, 0)

    def test_group_promotion_applies_to_all_variants_in_group(self):
        ProductPromotion.objects.create(name='Model promo', target_type='group', group=self.group, discount_percent=10)
        other = Headphone.objects.create(
            brand=self.brand, group=self.group, name='Sony WH-CH720N White', slug='sony-wh-ch720n-white',
            price=Decimal('5000.00'), stock=5, available=True, headphone_type='over_ear', connection_type='wireless'
        )
        self.assertEqual(other.effective_discount_percent, 10)


class CartPromotionTest(TestCase):
    def setUp(self):
        self.product = Smartphone.objects.create(
            name='Test Phone', slug='test-phone-promo', price=Decimal('1000.00'), stock=10, available=True,
            display_size='6.1', ram=8, storage=256, main_camera_mp=50, battery_capacity=5000,
        )

    def make_items(self, prices):
        return [
            {'price': Decimal(str(price)), 'quantity': 1}
            for price in prices
        ]

    def test_cart_promotion_can_discount_whole_cart(self):
        promo = CartPromotion.objects.create(name='5% cart', rule_type='cart', discount_percent=5, min_quantity=3)
        amount = promo.calculate_discount(self.make_items([100, 200, 300]))
        self.assertEqual(amount, Decimal('30.00'))

    def test_cart_promotion_can_discount_cheapest_item(self):
        promo = CartPromotion.objects.create(name='5% cheapest', rule_type='cheapest', discount_percent=5, min_quantity=3)
        amount = promo.calculate_discount(self.make_items([100, 200, 300]))
        self.assertEqual(amount, Decimal('5.00'))

    def test_only_best_cart_promotion_is_used(self):
        CartPromotion.objects.create(name='Cheap item', rule_type='cheapest', discount_percent=50, min_quantity=3)
        CartPromotion.objects.create(name='Whole cart', rule_type='cart', discount_percent=1, min_quantity=3)
        amount, promo = CartPromotion.get_best_for_basket(self.make_items([100, 200, 300]))
        self.assertEqual(amount, Decimal('50.00'))
        self.assertEqual(promo.name, 'Cheap item')

    def test_registered_only_requires_authenticated_user(self):
        promo = CartPromotion.objects.create(name='Members', rule_type='cart', discount_percent=10, registered_only=True)
        guest_amount = promo.calculate_discount(self.make_items([100]))
        user = User.objects.create_user(username='member', password='pass12345')
        member_amount = promo.calculate_discount(self.make_items([100]), user=user)
        self.assertEqual(guest_amount, Decimal('0.00'))
        self.assertEqual(member_amount, Decimal('10.00'))
