from collections import OrderedDict

from django.db.models import Prefetch

from main.constants import PRODUCT_CATEGORIES
from main.models import Product, ProductGroup


def category_menu():
    return [{'slug': slug, 'name': name} for slug, name, _ in PRODUCT_CATEGORIES]


def product_category_slug(product):
    """Return (category_slug, category_name) for a concrete Product instance."""
    for slug, name, model in PRODUCT_CATEGORIES:
        try:
            getattr(product, model._meta.model_name)
            return slug, name
        except model.DoesNotExist:
            continue
    return None, 'Товары'


def get_catalog_tree():
    """Build Category → Brand → ProductGroup without template-side DB queries."""
    product_queryset = (
        Product.objects
        .filter(available=True)
        .select_related('brand', 'group')
        .only(
            'id', 'brand_id', 'group_id',
            'brand__id', 'brand__name', 'brand__slug',
            'group__id', 'group__name', 'group__slug',
        )
    )

    groups = list(
        ProductGroup.objects
        .prefetch_related(
            Prefetch('products', queryset=product_queryset, to_attr='active_products')
        )
        .order_by('name')
    )

    product_ids = {
        product.id
        for group in groups
        for product in getattr(group, 'active_products', [])
    }

    category_by_product_id = {}
    if product_ids:
        for slug, _name, model in PRODUCT_CATEGORIES:
            for product_id in model.objects.filter(
                id__in=product_ids,
                available=True,
            ).values_list('id', flat=True):
                category_by_product_id[product_id] = slug

    tree = OrderedDict(
        (
            slug,
            {'slug': slug, 'name': name, 'brands': OrderedDict()},
        )
        for slug, name, _ in PRODUCT_CATEGORIES
    )

    for group in groups:
        for product in getattr(group, 'active_products', []):
            category_slug = category_by_product_id.get(product.id)
            if not category_slug or not product.brand:
                continue

            brand_id = product.brand_id
            category = tree[category_slug]
            brand_node = category['brands'].setdefault(
                brand_id,
                {
                    'id': brand_id,
                    'name': product.brand.name,
                    'slug': product.brand.slug,
                    'groups': OrderedDict(),
                },
            )

            brand_node['groups'].setdefault(
                group.id,
                {
                    'id': group.id,
                    'name': group.name,
                    'slug': group.slug,
                    'url': group.get_absolute_url(),
                },
            )

    result = []
    for category in tree.values():
        brands = sorted(category['brands'].values(), key=lambda item: item['name'].casefold())
        result.append({
            'slug': category['slug'],
            'name': category['name'],
            'brands': [
                {
                    'id': brand['id'],
                    'name': brand['name'],
                    'slug': brand['slug'],
                    'groups': sorted(
                        brand['groups'].values(),
                        key=lambda item: item['name'].casefold(),
                    ),
                }
                for brand in brands
            ],
        })

    return result
