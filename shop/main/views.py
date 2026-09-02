from decimal import Decimal, InvalidOperation
from itertools import chain

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.http import QueryDict

from .constants import CATEGORY_BY_SLUG, PRODUCT_CATEGORIES
from .models import Banner, Brand, Product, ProductGroup, ProductImage
from .services.catalog import category_menu, product_category_slug
from .utils import transliterate_to_cyrillic


def _all_available_products():
    """Return all active concrete product instances."""
    querysets = [
        model.objects.filter(available=True).select_related('brand', 'group')
        for _, _, model in PRODUCT_CATEGORIES
    ]
    return list(chain.from_iterable(querysets))


def _sort_products(products, sort):
    if sort == 'price_asc':
        products.sort(key=lambda item: item.get_discounted_price())
    elif sort == 'price_desc':
        products.sort(key=lambda item: item.get_discounted_price(), reverse=True)
    elif sort == 'name_asc':
        products.sort(key=lambda item: item.name.casefold())
    elif sort == 'name_desc':
        products.sort(key=lambda item: item.name.casefold(), reverse=True)


def _sort_urls(request):
    """Build sorting links without losing currently active filters."""
    params = request.GET.copy()
    urls = {}
    for value, key in (
        ('price_asc', 'price_asc'),
        ('price_desc', 'price_desc'),
        ('name_asc', 'name_asc'),
        ('name_desc', 'name_desc'),
    ):
        query = params.copy()
        query['sort'] = value
        encoded = query.urlencode()
        urls[key] = f'{request.path}?{encoded}' if encoded else request.path
    return urls


def _decimal_param(value):
    if value in (None, ''):
        return None
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError):
        return None
    return max(number, Decimal('0'))


def _filter_products(products, request):
    """Apply sidebar filters consistently to concrete product objects."""
    brand_id = request.GET.get('brand')
    price_min = _decimal_param(request.GET.get('price_min'))
    price_max = _decimal_param(request.GET.get('price_max'))
    in_stock = request.GET.get('in_stock') == '1'

    if brand_id:
        products = [
            product for product in products
            if str(product.brand_id) == str(brand_id)
        ]

    if price_min is not None:
        products = [
            product for product in products
            if product.get_discounted_price() >= price_min
        ]

    if price_max is not None:
        products = [
            product for product in products
            if product.get_discounted_price() <= price_max
        ]

    if in_stock:
        products = [product for product in products if product.stock > 0]

    return products, brand_id


def _category_groups(products):
    group_ids = {product.group_id for product in products if product.group_id}
    if not group_ids:
        return []
    return list(ProductGroup.objects.filter(id__in=group_ids).order_by('name'))


def _recently_viewed_products(request):
    ids = request.session.get('recently_viewed', [])
    if not ids:
        return []

    objects = {}
    for _, _, model in PRODUCT_CATEGORIES:
        for product in model.objects.filter(id__in=ids, available=True).select_related('brand', 'group'):
            objects[product.id] = product

    return [objects[product_id] for product_id in ids if product_id in objects]


def product_list(request, category_slug=None, group_slug=None, brand_slug=None):
    banners = Banner.objects.filter(is_active=True)
    brands = Brand.objects.all()
    category_groups = []
    current_group = None
    current_brand = None

    if brand_slug:
        current_brand = get_object_or_404(Brand, slug=brand_slug)
        category_name = f'Товары бренда {current_brand.name}'
        products = [
            product for product in _all_available_products()
            if product.brand_id == current_brand.id
        ]

    elif group_slug:
        current_group = get_object_or_404(ProductGroup, slug=group_slug)
        products = list(
            Product.objects
            .filter(group=current_group, available=True)
            .select_related('brand', 'group', 'smartphone', 'headphone', 'charger', 'cable', 'powerbank')
        )
        category_name = current_group.name

    elif category_slug:
        selected = CATEGORY_BY_SLUG.get(category_slug)
        if selected:
            category_name, model = selected
            products = list(
                model.objects.filter(available=True)
                .select_related('brand', 'group')
            )
            category_groups = _category_groups(products)
        else:
            products = []
            category_name = 'Каталог'

    else:
        products = _all_available_products()
        category_name = 'Все товары'

    products, brand_id = _filter_products(products, request)
    _sort_products(products, request.GET.get('sort'))

    recently_viewed_products = _recently_viewed_products(request)
    discounted_products = [product for product in products if product.discount_percent > 0]

    return render(
        request,
        'main/product/list.html',
        {
            'banners': banners,
            'brands': brands,
            'products': products,
            'category_name': category_name,
            'category_slug': category_slug,
            'categories': category_menu(),
            'recently_viewed_products': recently_viewed_products,
            'discounted_products': discounted_products,
            'current_sort': request.GET.get('sort'),
            'selected_brand': str(brand_id) if brand_id else '',
            'category_groups': category_groups,
            'current_group': current_group,
            'current_brand': current_brand,
            'sort_urls': _sort_urls(request),
        },
    )


def delivery_and_payment(request):
    return render(request, 'main/delivery_and_payment.html', {'categories': category_menu()})


def contacts(request):
    return render(request, 'main/contacts.html', {'categories': category_menu()})


def new_products(request):
    products = sorted(_all_available_products(), key=lambda item: item.id, reverse=True)[:12]
    return render(
        request,
        'main/new_products.html',
        {'title': 'Новинки', 'products': products, 'categories': category_menu()},
    )


def _search_products(query):
    result = []
    conditions = Q(name__icontains=query) | Q(description__icontains=query) | Q(brand__name__icontains=query)
    for _, _, model in PRODUCT_CATEGORIES:
        result.extend(
            model.objects.filter(available=True)
            .filter(conditions)
            .select_related('brand', 'group')
        )
    return result


def search_results(request):
    query = (request.GET.get('q') or '').strip()
    products = _search_products(query) if query else []

    if query and not products:
        translated = transliterate_to_cyrillic(query)
        if translated != query:
            products = _search_products(translated)

    return render(
        request,
        'main/search_results.html',
        {'query': query, 'products': products, 'categories': category_menu()},
    )


def product_detail(request, id, slug):
    product = get_object_or_404(
        Product.objects
        .select_related('brand', 'group', 'smartphone', 'headphone', 'charger', 'cable', 'powerbank')
        .prefetch_related('images'),
        id=id,
        slug=slug,
        available=True,
    )

    category_slug, category_name = product_category_slug(product)

    recently_viewed = request.session.get('recently_viewed', [])
    recently_viewed = [product_id for product_id in recently_viewed if product_id != product.id]
    recently_viewed.insert(0, product.id)
    request.session['recently_viewed'] = recently_viewed[:4]
    request.session.modified = True

    gallery = []
    if product.image:
        gallery.append({'url': product.image.url, 'alt': product.name, 'is_primary': True})

    for image in product.images.all():
        if image.image:
            gallery.append({'url': image.image.url, 'alt': product.name, 'is_primary': False})

    variants = []
    if product.group_id:
        variants = list(
            product.group.products
            .filter(available=True)
            .exclude(pk=product.pk)
            .order_by('color', 'name')
        )
        variants.insert(0, product)

    concrete_model = None
    if category_slug:
        category_data = CATEGORY_BY_SLUG.get(category_slug)
        if category_data:
            concrete_model = category_data[1]

    related_products = []
    if concrete_model:
        related_products = list(
            concrete_model.objects
            .filter(available=True)
            .exclude(pk=product.pk)
            .select_related('brand', 'group')
            .order_by('-id')[:4]
        )

    return render(
        request,
        'main/product/detail.html',
        {
            'product': product,
            'gallery': gallery,
            'variants': variants,
            'related_products': related_products,
            'categories': category_menu(),
            'category_slug': category_slug,
            'category_name': category_name,
        },
    )
