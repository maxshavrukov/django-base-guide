from django.shortcuts import render
from django.shortcuts import get_object_or_404
from .models import Category, Product
from basket.forms import BasketAddProductForm
# Create your views here.

def product_list(request, category_slug=None):
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    category = None
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
        
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