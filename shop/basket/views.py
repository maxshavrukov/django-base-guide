from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from main.models import Product
from .basket import Basket
from .forms import BasketAddProductForm

# Create your views here.

@require_POST
def basket_add(request, product_id):
    basket = Basket(request)
    product = get_object_or_404(Product, id=product_id)
    form = BasketAddProductForm(request.POST)

    if form.is_valid():
        cd = form.cleaned_data
        basket.add(product=product, quantity=cd['quantity'], override_quantity=cd['override'])
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # для AJAX просто возвращаем 200
        from django.http import JsonResponse
        return JsonResponse({'status': 'ok'})
    return redirect('basket:basket_detail')

@require_POST
def basket_remove(request, product_id):
    basket = Basket(request)
    product = get_object_or_404(Product, id=product_id)
    basket.remove(product)
    return redirect('basket:basket_detail')

def basket_detail(request):
    basket = Basket(request)
    for item in basket:
        item['update_quantity_form'] = BasketAddProductForm(initial={
            'quantity': item['quantity'], 
            'override': True
            })
    return render(request, 'basket/basket_detail.html', {'basket': basket})

