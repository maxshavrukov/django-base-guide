from .models import Brand, ProductGroup

def categories(request):
    shop_categories = [
        {'name': 'Смартфоны', 'slug': 'smartphones'},
        {'name': 'Наушники', 'slug': 'headphones'},
        {'name': 'Зарядные устройства', 'slug': 'chargers'},
        {'name': 'Кабели питания', 'slug': 'cables'},
        {'name': 'Повербанки', 'slug': 'powerbanks'},
    ]
    brands = Brand.objects.all()
    
    return {
        'categories': shop_categories,
        'brands': brands,
    }

def catalog_menu(request):
    # Получаем бренды вместе с их группами товаров за один запрос без проседания FPS
    groups_by_brand = ProductGroup.objects.prefetch_related('products__brand').all()
    # Возвращаем сформированное дерево категорий, брендов и серий
    return {
        'catalog_tree': ... # сформированное дерево
    }

