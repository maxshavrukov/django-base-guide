from main.services.categories import (
    get_active_root_categories,
    get_catalog_tree,
    get_product_root_category,
)


def category_menu():
    return [
        {'slug': category.slug, 'name': category.name}
        for category in get_active_root_categories()
    ]


def product_category_slug(product):
    category = get_product_root_category(product)
    if not category:
        return None, 'Товары'
    return category.slug, category.name
