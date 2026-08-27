from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from main.models import Product
from .basket import Basket
from .forms import BasketAddProductForm

# Create your views here.

@require_POST
def basket_add(request, product_id):
    basket = Basket(request)
    product = get_object_or_404(Product, id=product_id)
    # Передаем request.POST, а если данные пустые — используем дефолтные значения (количество 1)
    form = BasketAddProductForm(request.POST or None)

    if form.is_valid():
        cd = form.cleaned_data
        basket.add(product=product, quantity=cd.get('quantity', 1), override_quantity=cd.get('override', False))
    else:
        # Если форма по какой-то причине не прошла валидацию (например, прилетела из карточки новинок без полей), 
        # добавляем товар с количеством по умолчанию (1) принудительно:
        basket.add(product=product, quantity=1)

    # Если запрос пришел через AJAX (для мини-корзины и всплывающего окна)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        items_data = []
        
        # Перебираем товары (итератор Basket сам подгружает актуальные объекты Product из базы)
        for item in basket:
            product_obj = item.get('product')
            if product_obj:
                img_url = product_obj.image.url if (hasattr(product_obj, 'image') and product_obj.image) else ''
                items_data.append({
                    'name': product_obj.name,
                    'price': str(item.get('price', 0)),
                    'quantity': item.get('quantity', 1),
                    'image_url': img_url,
                })

        return JsonResponse({
            'status': 'ok',
            'total_price': str(basket.get_total_price()),
            'basket_len': len(basket),
            'items': items_data
        })

    # Обычный запрос — возвращаем пользователя обратно на страницу товара
    referer_url = request.META.get('HTTP_REFERER')
    if referer_url:
        return redirect(referer_url)
    return redirect('basket:basket_detail')

@require_POST
def basket_remove(request, product_id):
    basket = Basket(request)
    product = get_object_or_404(Product, id=product_id)
    basket.remove(product)
    # Если запрос пришел через AJAX (из мини-корзины)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        items_data = []
        for item in basket:
            product_obj = item.get('product')
            if product_obj:
                img_url = product_obj.image.url if (hasattr(product_obj, 'image') and product_obj.image) else ''
                items_data.append({
                    'product_id': product_obj.id,  # Обязательно передаем id для кнопки удаления!
                    'name': product_obj.name,
                    'price': str(item.get('price', 0)),
                    'quantity': item.get('quantity', 1),
                    'image_url': img_url,
                })
        return JsonResponse({
            'status': 'ok',
            'total_price': str(basket.get_total_price()),
            'basket_len': len(basket),
            'items': items_data
        })
                
    return redirect('basket:basket_detail')

def basket_detail(request):
    basket = Basket(request)
    
    # Добавляем форму изменения количества для каждого товара в деталях корзины
    for item in basket:
        item['update_quantity_form'] = BasketAddProductForm(initial={
            'quantity': item['quantity'], 
            'override': True
        })
        
    # Получаем детальную информацию о скидках и суммах через новый метод класса Basket
    basket_details = basket.get_basket_details()
    
    return render(request, 'basket/basket_detail.html', {
        'basket': basket,
        'basket_details': basket_details
    })

@require_POST
def basket_update(request, product_id, action):
    basket = Basket(request)
    product = get_object_or_404(Product, id=product_id)
    product_id_str = str(product.id)

    if action == 'plus':
        basket.add(product=product, quantity=1)

    elif action == 'minus':
        if product_id_str in basket.basket:
            if basket.basket[product_id_str]['quantity'] <= 1:
                basket.remove(product)
            else:
                basket.add(product=product, quantity=-1)
                
    return redirect('basket:basket_detail')