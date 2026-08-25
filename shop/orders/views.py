from django.shortcuts import render
from basket.basket import Basket
from .models import Order, OrderItem
from .forms import OrderCreateForm
from django.contrib.auth.decorators import login_required


def order_create(request):
    basket = Basket(request)

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)

        if form.is_valid():
            order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
            order.save()

            for item in basket:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity']
                )

            basket.clear()

            return render(
                request,
                'orders/created.html',
                {'order': order}
            )

    else:
        form = OrderCreateForm()

    return render(
        request,
        'orders/create.html',
        {
            'basket': basket,
            'form': form
        }
    )

