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
    
    return render(request, 'main/product/list.html',
                  {'category': category,
                   'categories': categories,
                   'products': products})


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