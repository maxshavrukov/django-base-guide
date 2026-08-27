from itertools import chain
from django.shortcuts import render, get_object_or_404
from .models import Product, Smartphone, Headphone, Charger, Cable, Banner, Brand, PowerBank

def product_list(request, category_slug=None):
    banners = Banner.objects.filter(is_active=True)
    
    category_name = None
    if category_slug == 'smartphones':
        products = list(Smartphone.objects.filter(available=True))
        category_name = "Смартфоны"
    elif category_slug == 'headphones':
        products = list(Headphone.objects.filter(available=True))
        category_name = "Наушники"
    elif category_slug == 'chargers':
        products = list(Charger.objects.filter(available=True))
        category_name = "Зарядные устройства"
    elif category_slug == 'cables':
        products = list(Cable.objects.filter(available=True))
        category_name = "Кабели питания"
    elif category_slug == 'powerbanks':
        products = list(PowerBank.objects.filter(available=True))
        category_name = "Повербанки"
    else:
        smartphones = list(Smartphone.objects.filter(available=True))
        headphones = list(Headphone.objects.filter(available=True))
        chargers = list(Charger.objects.filter(available=True))
        cables = list(Cable.objects.filter(available=True))
        powerbanks = list(PowerBank.objects.filter(available=True))
        products = list(chain(smartphones, headphones, chargers, cables, powerbanks))
    
    sort = request.GET.get('sort')
    if sort == 'price_asc':
        products.sort(key=lambda x: x.price)
    elif sort == 'price_desc':
        products.sort(key=lambda x: x.price, reverse=True)
    elif sort == 'name_asc':
        products.sort(key=lambda x: x.name)
    elif sort == 'name_desc':
        products.sort(key=lambda x: x.name, reverse=True)

    category = {'name': category_name} if category_name else None

    context = {
        'banners': banners,
        'products': products,
        'category': category,
    }
    return render(request, 'main/product/list.html', context)

def delivery_and_payment(request):
    return render(request, 'main/delivery_and_payment.html')

def contacts(request):
    return render(request, 'main/contacts.html')

def new_products(request):
    return render(request, 'main/new_products.html')

def search_results(request):
    query = request.GET.get('q')
    if query:
        smartphones = Smartphone.objects.filter(name__icontains=query, available=True)
        headphones = Headphone.objects.filter(name__icontains=query, available=True)
        chargers = Charger.objects.filter(name__icontains=query, available=True)
        cables = Cable.objects.filter(name__icontains=query, available=True)
        powerbanks = PowerBank.objects.filter(name__icontains=query, available=True)
    else:
        smartphones = Smartphone.objects.none()
        headphones = Headphone.objects.none()
        chargers = Charger.objects.none()
        cables = Cable.objects.none()
        powerbanks = PowerBank.objects.none()

    context = {
        'query': query,
        'smartphones': smartphones,
        'headphones': headphones,
        'chargers': chargers,
        'cables': cables,
        'powerbanks': powerbanks
    }
    return render(request, 'main/search_results.html', context)

def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    
    context = {
        'product': product,
    }
    return render(request, 'main/product/detail.html', context)

