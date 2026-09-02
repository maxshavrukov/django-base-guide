from .constants import PRODUCT_CATEGORIES
from .models import Brand
from .services.catalog import get_catalog_tree


def categories(request):
    """Shared simple category/brand data for public templates."""
    if request.path.startswith('/admin/'):
        return {'categories': [], 'brands': []}

    return {
        'categories': [
            {'name': name, 'slug': slug}
            for slug, name, _ in PRODUCT_CATEGORIES
        ],
        'brands': Brand.objects.all(),
    }


def catalog_menu(request):
    """Shared Каталог → категория → бренд → линейка tree."""
    if request.path.startswith('/admin/'):
        return {'catalog_tree': []}

    return {'catalog_tree': get_catalog_tree()}
