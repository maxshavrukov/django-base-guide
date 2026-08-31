from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from main.models import Product
from .basket import Basket
from .forms import BasketAddProductForm


def _ajax_payload(basket):
    items_data = []
    for item in basket:
        product = item['product']
        items_data.append({
            'product_id': product.id,
            'name': product.name,
            'price': str(item['price']),
            'original_price': str(item['original_price']),
            'product_discount_percent': item['product_discount_percent'],
            'quantity': item['quantity'],
            'total_price': str(item['total_price']),
            'image_url': product.image.url if product.image else '',
        })

    details = basket.get_basket_details()
    return {
        'status': 'ok',
        'total_price': str(details['total_price']),
        'subtotal': str(details['subtotal']),
        'product_discount_amount': str(details['product_discount_amount']),
        'promo_discount_percent': details['promo_discount_percent'],
        'promo_discount_amount': str(details['promo_discount_amount']),
        'discount_amount': str(details['discount_amount']),
        'basket_len': len(basket),
        'items': items_data,
    }


@require_POST
def basket_add(request, product_id):
    basket = Basket(request)
    product = get_object_or_404(Product, id=product_id)
    form = BasketAddProductForm(request.POST or None)

    if form.is_valid():
        cleaned = form.cleaned_data
        basket.add(
            product=product,
            quantity=cleaned.get('quantity', 1),
            override_quantity=cleaned.get('override', False),
        )
    else:
        basket.add(product=product, quantity=1)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(_ajax_payload(basket))

    referer_url = request.META.get('HTTP_REFERER')
    return redirect(referer_url or 'basket:basket_detail')


@require_POST
def basket_remove(request, product_id):
    basket = Basket(request)
    product = get_object_or_404(Product, id=product_id)
    basket.remove(product)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(_ajax_payload(basket))

    return redirect('basket:basket_detail')


def basket_detail(request):
    basket = Basket(request)
    return render(request, 'basket/basket_detail.html', {
        'basket': basket,
        'basket_details': basket.get_basket_details(),
    })


@require_POST
def basket_update(request, product_id, action):
    basket = Basket(request)
    product = get_object_or_404(Product, id=product_id)

    if action == 'plus':
        basket.change_quantity(product, 1)
    elif action == 'minus':
        basket.change_quantity(product, -1)

    return redirect('basket:basket_detail')
