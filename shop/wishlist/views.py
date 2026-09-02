from django.shortcuts import redirect, render
from .services.wishlist import Wishlist


def wishlist_detail(request):
    wishlist = Wishlist(request)
    return render(request, 'wishlist/wishlist_detail.html', {'wishlist': wishlist})


def wishlist_add(request, product_id):
    wishlist = Wishlist(request)
    wishlist.add(product_id)
    return redirect(request.META.get('HTTP_REFERER', 'main:product_list'))


def wishlist_remove(request, product_id):
    wishlist = Wishlist(request)
    wishlist.remove(product_id)
    return redirect(request.META.get('HTTP_REFERER', 'main:product_list'))