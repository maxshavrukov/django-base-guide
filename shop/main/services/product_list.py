from decimal import Decimal, InvalidOperation
from itertools import chain
from django.http import QueryDict
from django.shortcuts import get_object_or_404

from main.constants import CATEGORY_BY_SLUG, PRODUCT_CATEGORIES
from main.models import Brand, Product, ProductGroup
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
        products = [p for p in products if str(p.brand_id) == str(brand_id)]

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
    """
    Основной резолвер данных каталога: определяет список товаров, 
    фильтры категории, текущую группу и бренд.
    """
    # Если параметры не переданы, используем пустой QueryDict
    request_get = request_get if request_get is not None else QueryDict()
    category_groups = []
    category_filters = []
    current_group = None
    current_brand = None

    if brand_slug:
        current_brand = get_object_or_404(Brand, slug=brand_slug)
        category_name = f'Товары бренда {current_brand.name}'
        products = [p for p in get_all_available_products() if p.brand_id == current_brand.id]

    elif group_slug:
        current_group = get_object_or_404(ProductGroup, slug=group_slug)
        category_name = current_group.name

        cat_slug = None
        if hasattr(current_group, 'category') and current_group.category:
            cat_slug = current_group.category.slug
        else:
            for slug_key, (_, model_cls) in CATEGORY_BY_SLUG.items():
                if model_cls.objects.filter(group=current_group).exists():
                    cat_slug = slug_key
                    break

        category_slug = cat_slug
        selected = CATEGORY_BY_SLUG.get(cat_slug) if cat_slug else None

        if selected:
            _, model = selected
            queryset = model.objects.filter(group=current_group, available=True).select_related('brand', 'group')
            all_cat_queryset = model.objects.filter(available=True).select_related('brand', 'group')

            category_filters = get_category_filter_options(cat_slug, queryset, request_get)
            queryset = apply_category_filters(queryset, cat_slug, request_get)

            products = list(queryset)
            category_groups = get_category_groups(list(all_cat_queryset))
        else:
            products = list(
                Product.objects
                .filter(group=current_group, available=True)
                .select_related('brand', 'group')
            )

    elif category_slug:
        selected = CATEGORY_BY_SLUG.get(category_slug)
        if selected:
            category_name, model = selected
            queryset = model.objects.filter(available=True).select_related('brand', 'group')

            category_filters = get_category_filter_options(category_slug, queryset, request_get)
            queryset = apply_category_filters(queryset, category_slug, request_get)

            products = list(queryset)
            category_groups = get_category_groups(products)
        else:
            products = []
            category_name = 'Каталог'

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
    }