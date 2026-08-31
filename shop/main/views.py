from itertools import chain

from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import (
    Banner,
    Brand,
    Cable,
    Charger,
    Headphone,
    PowerBank,
    Product,
    Smartphone,
)


PRODUCT_CATEGORIES = (
    ("smartphones", "Смартфоны", Smartphone),
    ("headphones", "Наушники", Headphone),
    ("chargers", "Зарядные устройства", Charger),
    ("cables", "Кабели", Cable),
    ("powerbanks", "Повербанки", PowerBank),
)


def _category_menu():
    return [{"slug": slug, "name": name} for slug, name, _ in PRODUCT_CATEGORIES]


def _all_available_products():
    querysets = [
        model.objects.filter(available=True).select_related("brand")
        for _, _, model in PRODUCT_CATEGORIES
    ]
    return list(chain.from_iterable(querysets))


def product_list(request, category_slug=None):
    banners = Banner.objects.filter(is_active=True)
    brands = Brand.objects.all()

    if category_slug:
        category_map = {slug: (name, model) for slug, name, model in PRODUCT_CATEGORIES}
        selected = category_map.get(category_slug)

        if selected:
            category_name, model = selected
            products = list(
                model.objects.filter(available=True).select_related("brand")
            )
        else:
            products = []
            category_name = "Каталог"
    else:
        products = _all_available_products()
        category_name = "Все товары"

    brand_id = request.GET.get("brand")
    if brand_id:
        products = [
            product for product in products
            if str(product.brand_id) == str(brand_id)
        ]

    sort = request.GET.get("sort")
    if sort == "price_asc":
        products.sort(key=lambda item: item.price)
    elif sort == "price_desc":
        products.sort(key=lambda item: item.price, reverse=True)
    elif sort == "name_asc":
        products.sort(key=lambda item: item.name.lower())
    elif sort == "name_desc":
        products.sort(key=lambda item: item.name.lower(), reverse=True)

    recently_viewed_ids = request.session.get("recently_viewed", [])
    recent_objects = {
        product.id: product
        for product in Product.objects.filter(
            id__in=recently_viewed_ids,
            available=True,
        ).select_related("brand")
    }
    recently_viewed_products = [
        recent_objects[product_id]
        for product_id in recently_viewed_ids
        if product_id in recent_objects
    ]

    discounted_products = [
        product for product in products if product.discount_percent > 0
    ]

    return render(
        request,
        "main/product/list.html",
        {
            "banners": banners,
            "brands": brands,
            "products": products,
            "category": {"name": category_name},
            "categories": _category_menu(),
            "recently_viewed_products": recently_viewed_products,
            "discounted_products": discounted_products,
            "current_sort": sort,
            "selected_brand": str(brand_id) if brand_id else "",
        },
    )


def delivery_and_payment(request):
    return render(
        request,
        "main/delivery_and_payment.html",
        {"categories": _category_menu()},
    )


def contacts(request):
    return render(
        request,
        "main/contacts.html",
        {"categories": _category_menu()},
    )


def new_products(request):
    products = list(
        Product.objects.filter(available=True)
        .select_related("brand")
        .order_by("-id")[:12]
    )
    return render(
        request,
        "main/new_products.html",
        {
            "title": "Новинки",
            "products": products,
            "categories": _category_menu(),
        },
    )


def search_results(request):
    query = (request.GET.get("q") or "").strip()
    products = []

    if query:
        products = [
            product
            for product in _all_available_products()
            if query.lower() in product.name.lower()
            or query.lower() in (product.description or "").lower()
            or (
                product.brand
                and query.lower() in product.brand.name.lower()
            )
        ]

    return render(
        request,
        "main/search_results.html",
        {
            "query": query,
            "products": products,
            "categories": _category_menu(),
        },
    )


def product_detail(request, id, slug):
    product = get_object_or_404(
        Product.objects.select_related("brand").prefetch_related("images"),
        id=id,
        slug=slug,
        available=True,
    )

    # Безопасно определяем slug и название категории
    category_slug = None
    category_name = "Товары"

    for cat_slug, cat_name, model in PRODUCT_CATEGORIES:
        rel_name = model._meta.model_name  # 'smartphone', 'headphone' и т.д.
        try:
            if getattr(product, rel_name, None) is not None:
                category_slug = cat_slug
                category_name = cat_name
                break
        except Exception:
            continue

    recently_viewed = request.session.get("recently_viewed", [])
    if product.id in recently_viewed:
        recently_viewed.remove(product.id)
    recently_viewed.insert(0, product.id)
    request.session["recently_viewed"] = recently_viewed[:4]
    request.session.modified = True

    gallery = []
    if product.image:
        gallery.append(
            {
                "url": product.image.url,
                "alt": product.name,
                "is_primary": True,
            }
        )

    for image in product.images.all():
        if image.image:
            gallery.append(
                {
                    "url": image.image.url,
                    "alt": product.name,
                    "is_primary": False,
                }
            )

    concrete_model = next(
        (
            model
            for _, _, model in PRODUCT_CATEGORIES
            if hasattr(product, model._meta.model_name)
        ),
        None,
    )
    if concrete_model:
        related_products = list(
            concrete_model.objects.filter(available=True)
            .exclude(pk=product.pk)
            .select_related("brand")
            .order_by("-id")[:4]
        )
    else:
        related_products = []

    return render(
        request,
        "main/product/detail.html",
        {
            "product": product,
            "gallery": gallery,
            "related_products": related_products,
            "categories": _category_menu(),
            "category_slug": category_slug,
            "category_name": category_name,
        },
    )
