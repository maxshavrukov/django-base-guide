from collections import defaultdict

from main.constants import PRODUCT_TYPES
from main.models import Category, ProductGroup


PRODUCT_TYPE_TO_MODEL = {
    model._meta.model_name: model
    for _slug, _name, model in PRODUCT_TYPES
}
FILTER_KEY_BY_PRODUCT_TYPE = {
    model._meta.model_name: slug
    for slug, _name, model in PRODUCT_TYPES
}


def get_active_root_categories():
    return list(
        Category.objects
        .filter(parent__isnull=True, is_active=True)
        .order_by('sort_order', 'name')
    )


def get_category_descendant_ids(category) -> list[int]:
    """Return the selected category id plus all active descendant ids.
    If the category itself is inactive, returns an empty list.
    """
    if not category.is_active:
        return []

    categories = Category.objects.filter(is_active=True).values('id', 'parent_id')
    children = defaultdict(list)
    for item in categories:
        if item['parent_id'] is not None:
            children[item['parent_id']].append(item['id'])

    result = [category.id]
    queue = [category.id]
    while queue:
        parent_id = queue.pop(0)
        for child_id in children.get(parent_id, []):
            if child_id not in result:
                result.append(child_id)
                queue.append(child_id)
    return result


def get_product_model(product):
    """Return the concrete model for a base Product instance or a concrete instance."""
    model_name = product.__class__._meta.model_name
    direct_model = PRODUCT_TYPE_TO_MODEL.get(model_name)
    if direct_model:
        return direct_model

    for model in PRODUCT_TYPE_TO_MODEL.values():
        try:
            getattr(product, model._meta.model_name)
            return model
        except model.DoesNotExist:
            continue
    return None


def get_category_model(category):
    return PRODUCT_TYPE_TO_MODEL.get(category.get_effective_product_type())


def get_category_filter_key(category):
    """Return the existing filter config key for the concrete product type."""
    return FILTER_KEY_BY_PRODUCT_TYPE.get(category.get_effective_product_type())


def get_category_product_queryset(category):
    """Return active concrete products visible in a root or secondary category."""
    model = get_category_model(category)
    if model is None or not category.is_active:
        if model:
            return model.objects.none()
        return None

    if category.parent_id is None:
        return model.objects.filter(available=True).select_related('brand', 'group')

    category_ids = get_category_descendant_ids(category)
    if not category_ids:
        return model.objects.none()

    return (
        model.objects
        .filter(
            available=True,
            group__categories__id__in=category_ids,
        )
        .select_related('brand', 'group')
        .distinct()
    )


def get_category_group_queryset(category):
    """Return active product groups visible inside the selected category."""
    model = get_category_model(category)
    if model is None or not category.is_active:
        return ProductGroup.objects.none()

    if category.parent_id is None:
        group_ids = model.objects.filter(available=True).values_list('group_id', flat=True)
        return ProductGroup.objects.filter(id__in=group_ids).distinct().order_by('name')

    category_ids = get_category_descendant_ids(category)
    if not category_ids:
        return ProductGroup.objects.none()

    return (
        ProductGroup.objects
        .filter(
            products__available=True,
            categories__id__in=category_ids,
        )
        .distinct()
        .order_by('name')
    )


def get_product_root_category(product):
    """Return the active root category matching the concrete product type."""
    concrete_model = get_product_model(product)
    if concrete_model is None:
        return None
    product_type = concrete_model._meta.model_name
    return (
        Category.objects
        .filter(parent__isnull=True, product_type=product_type, is_active=True)
        .order_by('sort_order', 'name')
        .first()
    )


def get_catalog_tree():
    """Build root category → subcategories → brands/groups tree in memory."""
    roots = get_active_root_categories()
    root_by_type = {root.product_type: root for root in roots}

    children_by_parent = defaultdict(list)
    all_categories = (
        Category.objects
        .filter(is_active=True)
        .select_related('parent')
        .order_by('sort_order', 'name')
    )
    for category in all_categories:
        if category.parent_id:
            children_by_parent[category.parent_id].append(category)

    nodes = {
        root.id: {
            'id': root.id,
            'slug': root.slug,
            'name': root.name,
            'children': [
                {'id': child.id, 'slug': child.slug, 'name': child.name}
                for child in children_by_parent.get(root.id, [])
            ],
            'brands': {},
        }
        for root in roots
    }

    groups = list(
        ProductGroup.objects
        .filter(products__available=True)
        .prefetch_related('categories')
        .distinct()
        .order_by('name')
    )

    group_products = defaultdict(list)
    for _slug, _name, model in PRODUCT_TYPES:
        for product in (
            model.objects
            .filter(available=True, group__isnull=False)
            .select_related('brand', 'group')
        ):
            group_products[product.group_id].append(product)

    for group in groups:
        products = group_products.get(group.id, [])
        if not products:
            continue

        brand_nodes = {}
        for product in products:
            if product.brand_id and product.brand:
                brand_nodes.setdefault(
                    product.brand_id,
                    {
                        'id': product.brand_id,
                        'name': product.brand.name,
                        'slug': product.brand.slug,
                    },
                )

        root_types = {
            product.__class__._meta.model_name
            for product in products
            if product.__class__._meta.model_name in root_by_type
        }

        # All groups appear under their concrete root category.
        for product_type in root_types:
            root = root_by_type[product_type]
            root_brands = nodes[root.id]['brands']
            for brand_id, brand_data in brand_nodes.items():
                brand_node = root_brands.setdefault(
                    brand_id,
                    {**brand_data, 'groups': {}},
                )
                brand_node['groups'][group.id] = {
                    'id': group.id,
                    'name': group.name,
                    'slug': group.slug,
                    'url': group.get_absolute_url(),
                }

    return [
        {
            'slug': nodes[root.id]['slug'],
            'name': nodes[root.id]['name'],
            'children': nodes[root.id]['children'],
            'brands': [
                {
                    **brand,
                    'groups': sorted(brand['groups'].values(), key=lambda item: item['name'].casefold()),
                }
                for brand in sorted(
                    nodes[root.id]['brands'].values(),
                    key=lambda item: item['name'].casefold(),
                )
            ],
        }
        for root in roots
    ]