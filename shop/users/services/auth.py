from django.contrib.auth import login, logout


def authenticate_and_login(request, form):
    """Авторизует пользователя на основе валидной формы входа."""
    user = form.get_user()
    login(request, user)
    return user


def register_and_login(request, form):
    """Регистрирует нового пользователя и сразу авторизует его."""
    user = form.save()
    login(request, user)
    return user


def logout_user(request):
    """Завершает сеанс пользователя."""
    logout(request)