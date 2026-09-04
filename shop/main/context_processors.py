from .models import Brand
from .services.catalog import get_catalog_tree
from .services.categories import get_active_root_categories


def categories(request):
    """Shared simple category/brand data for public templates."""
    if request.path.startswith('/admin/'):
        return {'categories': [], 'brands': []}

    return {
        'categories': [
            {'name': category.name, 'slug': category.slug}
            for category in get_active_root_categories()
        ],
        'brands': Brand.objects.all(),
    }


def catalog_menu(request):
    """Shared Каталог → категория → бренд → линейка tree."""
    if request.path.startswith('/admin/'):
        return {'catalog_tree': []}

    return {'catalog_tree': get_catalog_tree()}
