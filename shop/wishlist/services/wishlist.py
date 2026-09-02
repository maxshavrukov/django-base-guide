from main.models import Product
from wishlist.models import WishlistItem

CONCRETE_RELATIONS = (
    "smartphone",
    "headphone",
    "charger",
    "cable",
    "powerbank",
)


def _concrete_product(product):
    """Возвращает конкретный экземпляр модели-потомка для Product, если он существует."""
    if product.__class__ is not Product:
        return product

    for relation_name in CONCRETE_RELATIONS:
        try:
            return getattr(product, relation_name)
        except Product.DoesNotExist:
            continue

    return product


class Wishlist:
    def __init__(self, request):
        self.session = request.session
        self.request = request
        self.user = request.user if request.user.is_authenticated else None

        if not self.user:
            wishlist = self.session.get("wishlist")
            if not wishlist:
                wishlist = self.session["wishlist"] = []
            self.wishlist = wishlist

    def add(self, product_id):
        product_id = str(product_id)

        if self.user:
            product = Product.objects.get(id=product_id)
            WishlistItem.objects.get_or_create(user=self.user, product=product)
        else:
            if product_id not in self.wishlist:
                self.wishlist.append(product_id)
                self.save()

    def remove(self, product_id):
        product_id = str(product_id)

        if self.user:
            WishlistItem.objects.filter(user=self.user, product_id=product_id).delete()
        else:
            if product_id in self.wishlist:
                self.wishlist.remove(product_id)
                self.save()

    def save(self):
        self.session.modified = True

    def __iter__(self):
        if self.user:
            product_ids = WishlistItem.objects.filter(user=self.user).values_list(
                "product_id", flat=True
            )
        else:
            product_ids = self.wishlist

        products = Product.objects.filter(id__in=product_ids).select_related(
            "brand", "group", "smartphone", "headphone", "charger", "cable", "powerbank"
        )

        for product in products:
            yield _concrete_product(product)

    def __len__(self):
        if self.user:
            return WishlistItem.objects.filter(user=self.user).count()
        return len(self.wishlist)

    def clear(self):
        if self.user:
            WishlistItem.objects.filter(user=self.user).delete()
        else:
            if "wishlist" in self.session:
                del self.session["wishlist"]
                self.save()