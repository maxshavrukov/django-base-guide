from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

# Перерегистрируем стандартную модель User с красивыми настройками таблицы
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')

# Снимаем с регистрации стандартную и регистрируем нашу расширенную
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)