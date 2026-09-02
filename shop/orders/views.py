from django.shortcuts import render

from basket.services.basket import Basket
from .forms import OrderCreateForm
from .services.order import create_order


def order_create(request):
    basket = Basket(request)
    basket_details = basket.get_basket_details()

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)

        if form.is_valid():
            order = create_order(
                user=request.user,
                form=form,
                basket=basket
            )

            return render(request, 'orders/created.html', {
                'order': order,
                'basket_details': basket_details,
            })

    else:
        form = OrderCreateForm()

    return render(
        request,
        'orders/create.html',
        {
            'basket': basket,
            'basket_details': basket_details,
            'form': form
        }
    )