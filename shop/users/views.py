from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import UserLoginForm, UserRegistrationForm, UserProfileForm
from .services.auth import authenticate_and_login, logout_user, register_and_login
from .services.profile import get_recently_viewed, get_user_orders, get_user_profile
from .services.bonuses import BonusService


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
    profile = get_user_profile(request.user)
    account = BonusService.get_or_create_account(request.user)
    BonusService.ensure_birthday_bonus(request.user)
    return render(request, 'users/profile.html', {
        'user': request.user,
        'profile': profile,
        'bonus_balance': BonusService.get_available_balance(account),
        'recent_transactions': account.transactions.order_by('-created_at', '-id')[:5],
        'birthday_bonus': BonusService.BIRTHDAY_BONUS,
    })


@login_required
def personal_data_view(request):
    profile = get_user_profile(request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('users:personal_data')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'users/personal_data.html', {'form': form, 'profile': profile})


@login_required
def bonus_history_view(request):
    account = BonusService.get_or_create_account(request.user)
    BonusService.ensure_birthday_bonus(request.user)
    transactions = account.transactions.select_related('order').order_by('-created_at', '-id')
    return render(request, 'users/bonus_history.html', {
        'transactions': transactions,
        'bonus_balance': BonusService.get_available_balance(account),
    })


@login_required
def recently_viewed_view(request):
    return render(request, 'users/recently_viewed.html', {
        'recent_products': get_recently_viewed(request.user),
    })


@login_required
def order_list(request):
    orders = get_user_orders(request.user)
    return render(request, 'users/order_list.html', {'orders': orders})
