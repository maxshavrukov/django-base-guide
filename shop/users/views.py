from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from .forms import UserLoginForm, UserRegistrationForm
from django.contrib.auth.decorators import login_required
from orders.models import Order

# Отображение единого окна (Вход / Регистрация)
def auth_view(request):
    if request.user.is_authenticated:
        return redirect('main:product_list')

    return render(request, 'users/auth.html', {
        'login_form': UserLoginForm(),
        'register_form': UserRegistrationForm()
    })

# Обработка формы Входа
def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('main:product_list')
        return render(request, 'users/auth.html', {
            'login_form': form,
            'register_form': UserRegistrationForm()
        })
    return redirect('users:auth')

# Обработка формы Регистрации
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('main:product_list')
        return render(request, 'users/auth.html', {
            'login_form': UserLoginForm(),
            'register_form': form
        })
    return redirect('users:auth')

# Выход из аккаунта
def user_logout(request):
    logout(request)
    return redirect('main:product_list')

@login_required
def profile_view(request):
    return render(request, 'users/profile.html', {
        'user': request.user
    })

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product')
    return render(request, 'users/order_list.html', {'orders': orders})
