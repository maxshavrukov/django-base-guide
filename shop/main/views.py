from django.shortcuts import get_object_or_404, render

from .models import Banner, Brand, Product
from .services.catalog import category_menu, product_category_slug
from .services.product_detail import (
    get_product_gallery,
    get_product_variants,
    get_related_products,
    update_recently_viewed,
)
from .services.product_list import (
    build_sort_urls,
    filter_products,
    get_all_available_products,
    get_recently_viewed_products,
    resolve_catalog_data,
    sort_products,
)
from .services.search import search_products


def product_list(request, category_slug=None, group_slug=None, brand_slug=None):
    catalog_data = resolve_catalog_data(category_slug, group_slug, brand_slug, request.GET)
    products, selected_brand = filter_products(catalog_data['products'], request)
    sort_products(products, request.GET.get('sort'))

    return render(
        request,
        'main/product/list.html',
        {
            'banners': Banner.objects.filter(is_active=True),
            'brands': Brand.objects.all(),
            'products': products,
            'category_name': catalog_data['category_name'],
            'category_slug': catalog_data['category_slug'],
            'category_filters': catalog_data['category_filters'],
            'categories': category_menu(),
            'recently_viewed_products': get_recently_viewed_products(request),
            'discounted_products': [p for p in products if p.discount_percent > 0],
            'current_sort': request.GET.get('sort'),
            'selected_brand': selected_brand,
            'category_groups': catalog_data['category_groups'],
            'current_group': catalog_data['current_group'],
            'current_brand': catalog_data['current_brand'],
            'sort_urls': build_sort_urls(request),
        },
    )


def delivery_and_payment(request):
    return render(request, 'main/delivery_and_payment.html', {'categories': category_menu()})


def contacts(request):
    return render(request, 'main/contacts.html', {'categories': category_menu()})


def new_products(request):
    products = sorted(get_all_available_products(), key=lambda item: item.id, reverse=True)[:12]
    return render(
        request,
        'main/new_products.html',
        {'title': 'Новинки', 'products': products, 'categories': category_menu()},
    )


def search_results(request):
    query = request.GET.get('q', '')
    products = search_products(query)
    return render(
        request,
        'main/search_results.html',
        {'query': query.strip(), 'products': products, 'categories': category_menu()},
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
    update_recently_viewed(request, product.id)
    storage_variants, color_variants = get_product_variants(product)

    return render(
        request,
        'main/product/detail.html',
        {
            'product': product,
            'gallery': get_product_gallery(product),
            'storage_variants': storage_variants,
            'color_variants': color_variants,
            'related_products': get_related_products(product),
            'categories': category_menu(),
            'category_slug': category_slug,
            'category_name': category_name,
        },
    )