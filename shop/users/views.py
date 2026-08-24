from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegistrationForm

# Отображение единого окна (Вход / Регистрация)
def auth_view(request):
    if request.user.is_authenticated:
        return redirect('main:product_list')

    return render(request, 'users/auth.html', {
        'login_form': AuthenticationForm(),
        'register_form': UserRegistrationForm()
    })

# Обработка формы Входа
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
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
            'login_form': AuthenticationForm(),
            'register_form': form
        })
    return redirect('users:auth')

# Выход из аккаунта
def user_logout(request):
    logout(request)
    return redirect('main:product_list')