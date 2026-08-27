from .models import Brand

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