from decimal import Decimal, InvalidOperation
from itertools import chain

from django.http import QueryDict
from django.shortcuts import get_object_or_404

from main.constants import PRODUCT_CATEGORIES
from main.models import Brand, Product, ProductGroup
from main.services.categories import (
    get_category_filter_key,
    get_category_group_queryset,
    get_category_product_queryset,
    get_product_model,
)
from main.services.filters import apply_category_filters, get_category_filter_options


def get_all_available_products() -> list:
    """Возвращает список всех активных товаров."""
    querysets = [
        model.objects.filter(available=True).select_related('brand', 'group')
        for _, _, model in PRODUCT_CATEGORIES
    ]
    return list(chain.from_iterable(querysets))


def _decimal_param(value):
    if value in (None, ''):
        return None
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError):
        return None
    return max(number, Decimal('0'))


def filter_products(products: list, request) -> tuple[list, str]:
    """Применяет базовые фильтры (бренд, цена, наличие)."""
    brand_id = request.GET.get('brand')
    price_min = _decimal_param(request.GET.get('price_min'))
    price_max = _decimal_param(request.GET.get('price_max'))
    in_stock = request.GET.get('in_stock') == '1'

    if brand_id:
        brand_value = str(brand_id).strip().casefold()
        products = [
            p for p in products
            if p.brand and p.brand.name.strip().casefold() == brand_value
        ]

    if price_min is not None:
        products = [p for p in products if p.get_discounted_price() >= price_min]

    if price_max is not None:
        products = [p for p in products if p.get_discounted_price() <= price_max]

    if in_stock:
        products = [p for p in products if p.stock > 0]

    return products, str(brand_id) if brand_id else ''


def sort_products(products: list, sort_key: str | None) -> None:
    """Сортирует список товаров на месте."""
    if sort_key == 'price_asc':
        products.sort(key=lambda item: item.get_discounted_price())
    elif sort_key == 'price_desc':
        products.sort(key=lambda item: item.get_discounted_price(), reverse=True)
    elif sort_key == 'name_asc':
        products.sort(key=lambda item: item.name.casefold())
    elif sort_key == 'name_desc':
        products.sort(key=lambda item: item.name.casefold(), reverse=True)


def build_sort_urls(request) -> dict[str, str]:
    """Формирует ссылки для сортировки с сохранением текущих GET-параметров."""
    params = request.GET.copy()
    urls = {}
    for key in ('price_asc', 'price_desc', 'name_asc', 'name_desc'):
        query = params.copy()
        query['sort'] = key
        encoded = query.urlencode()
        urls[key] = f'{request.path}?{encoded}' if encoded else request.path
    return urls


def get_category_groups(products: list) -> list:
    """Возвращает список групп (линеек) для переданных товаров."""
    group_ids = {p.group_id for p in products if p.group_id}
    if not group_ids:
        return []
    return list(ProductGroup.objects.filter(id__in=group_ids).order_by('name'))


def get_recently_viewed_products(request) -> list:
    """Возвращает объекты товаров, ранее просмотренных пользователем."""
    ids = request.session.get('recently_viewed', [])
    if not ids:
        return []

    objects = {}
    for _, _, model in PRODUCT_CATEGORIES:
        for product in model.objects.filter(id__in=ids, available=True).select_related('brand', 'group'):
            objects[product.id] = product

    return [objects[p_id] for p_id in ids if p_id in objects]


def resolve_catalog_data(category_slug=None, group_slug=None, brand_slug=None, request_get=None) -> dict:
    """Resolve catalog data for root/secondary categories, groups and brands."""
    request_get = request_get if request_get is not None else QueryDict()
    category_groups = []
    category_filters = []
    current_group = None
    current_brand = None
    current_category = None

    if brand_slug:
        current_brand = get_object_or_404(Brand, slug=brand_slug)
        category_name = f'Товары бренда {current_brand.name}'
        products = [p for p in get_all_available_products() if p.brand_id == current_brand.id]

    elif group_slug:
        current_group = get_object_or_404(ProductGroup, slug=group_slug)
        category_name = current_group.name

        # ProductGroup describes one concrete model, so derive its type from its products.
        group_products = list(
            Product.objects
            .filter(group=current_group, available=True)
            .select_related('brand', 'group')
        )
        products = group_products
        if group_products:
            category_slug, category_name_for_group = _find_product_category(group_products[0])
            if category_slug:
                current_category = _get_category_or_none(category_slug)
                category_name = current_group.name
                filter_key = _get_filter_key_for_product(group_products[0])
                model_products = _get_group_concrete_queryset(current_group, group_products[0])
                category_filters = get_category_filter_options(filter_key, model_products, request_get) if filter_key else []
                filtered = apply_category_filters(model_products, filter_key, request_get) if filter_key else model_products
                products = list(filtered)
                category_groups = list(
                    get_category_group_queryset(current_category)
                    if current_category else ProductGroup.objects.none()
                )

    elif category_slug:
        current_category = get_object_or_404(
            __import__('main.models', fromlist=['Category']).Category,
            slug=category_slug,
            is_active=True,
        )
        category_name = current_category.name
        filter_key = get_category_filter_key(current_category)
        queryset = get_category_product_queryset(current_category)
        if queryset is None:
            products = []
        else:
            category_filters = get_category_filter_options(filter_key, queryset, request_get) if filter_key else []
            queryset = apply_category_filters(queryset, filter_key, request_get) if filter_key else queryset
            products = list(queryset)
            category_groups = list(get_category_group_queryset(current_category))

    else:
        products = get_all_available_products()
        category_name = 'Все товары'

    return {
        'products': products,
        'category_name': category_name,
        'category_slug': category_slug,
        'category_filters': category_filters,
        'category_groups': category_groups,
        'current_group': current_group,
        'current_brand': current_brand,
        'current_category': current_category,
    }


def _get_category_or_none(slug):
    from main.models import Category
    return Category.objects.filter(slug=slug, is_active=True).first()


def _find_product_category(product):
    from main.services.catalog import product_category_slug
    return product_category_slug(product)


def _get_filter_key_for_product(product):
    concrete_model = get_product_model(product)
    if concrete_model is None:
        return None
    for slug, _name, model in PRODUCT_CATEGORIES:
        if model is concrete_model:
            return slug
    return None


def _get_group_concrete_queryset(group, product):
    concrete_model = get_product_model(product)
    if concrete_model is not None:
        return concrete_model.objects.filter(group=group, available=True).select_related('brand', 'group')
    return Product.objects.filter(group=group, available=True).select_related('brand', 'group')
