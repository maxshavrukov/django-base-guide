from django.shortcuts import render
from django.shortcuts import get_object_or_404
from .models import Category, Product, Banner
from basket.forms import BasketAddProductForm
from django.db.models import Q
# Create your views here.

from django.db.models import Q

def product_list(request, category_slug=None):
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    banners = Banner.objects.filter(is_active=True)

    category = None
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
        
    # Логика поиска
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    # Сортировка
    sort = request.GET.get('sort')  # получаем параметр sort
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'name_asc':
        products = products.order_by('name')
    elif sort == 'name_desc':
        products = products.order_by('-name')
    
    return render(request, 'main/product/list.html',
                  {'category': category,
                   'categories': categories,
                   'products': products,
                   'current_sort': sort,  # передаём текущую сортировку в шаблон
                   'banners': banners,    # передаём текущие баннеры в шаблон
                   'query': query,        # передаём поисковый запрос в шаблон
                  })

def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug)
    related_products = (
        Product.objects.filter(category=product.category)
        .exclude(id=product.id)[:3]
    )
    categories = Category.objects.all()

    basket_product_form = BasketAddProductForm()

    return render(request, 'main/product/detail.html', {
        'product': product,
        'related_products': related_products,
        'categories': categories,
        'basket_product_form': basket_product_form,
    })

def delivery_and_payment(request):
    context = {
        'title': 'Доставка и оплата',
    }
    return render(request, 'main/delivery_and_payment.html', context)

def contacts(request):
    context = {
        'title': 'Контакты',
    }
    return render(request, 'main/contacts.html', context)

def new_products(request):
    # Берём последние 12 товаров (если есть поле created — используй '-created')
    latest_products = Product.objects.filter(available=True).order_by('-id')[:12]
    
    context = {
        'title': 'Новинки',
        'products': latest_products,
    }
    return render(request, 'main/new_products.html', context)