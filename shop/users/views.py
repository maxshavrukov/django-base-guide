from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import UserLoginForm, UserRegistrationForm
from .services.auth import authenticate_and_login, logout_user, register_and_login
from .services.profile import get_user_orders


def auth_view(request):
    if request.user.is_authenticated:
        return redirect('main:product_list')

    return render(request, 'users/auth.html', {
        'login_form': UserLoginForm(),
        'register_form': UserRegistrationForm(),
    })


def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            authenticate_and_login(request, form)
            return redirect('main:product_list')
        return render(request, 'users/auth.html', {
            'login_form': form,
            'register_form': UserRegistrationForm(),
        })
    return redirect('users:auth')


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            register_and_login(request, form)
            return redirect('main:product_list')
        return render(request, 'users/auth.html', {
            'login_form': UserLoginForm(),
            'register_form': form,
        })
    return redirect('users:auth')


def user_logout(request):
    logout_user(request)
    return redirect('main:product_list')


@login_required
def profile_view(request):
    return render(request, 'users/profile.html', {
        'user': request.user,
    })


@login_required
def order_list(request):
    orders = get_user_orders(request.user)
    return render(request, 'users/order_list.html', {'orders': orders})