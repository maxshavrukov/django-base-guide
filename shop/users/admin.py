from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from users.models import BonusAccount, BonusConsumption, BonusTransaction, RecentlyViewedProduct, UserProfile


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'phone', 'birth_date', 'city', 'updated_at')
    search_fields = ('user__username', 'user__email', 'first_name', 'last_name', 'phone')
    list_filter = ('birth_date',)


@admin.register(BonusAccount)
class BonusAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'available_balance', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')

    @admin.display(description='Доступно бонусов')
    def available_balance(self, obj):
        return obj.get_available_balance()


@admin.register(BonusTransaction)
class BonusTransactionAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'account', 'transaction_type', 'amount', 'expires_at', 'order', 'reference_year')
    list_filter = ('transaction_type',)
    search_fields = ('account__user__username', 'account__user__email', 'description')
    readonly_fields = ('created_at',)


@admin.register(BonusConsumption)
class BonusConsumptionAdmin(admin.ModelAdmin):
    list_display = ('spend_transaction', 'source_transaction', 'amount')
    search_fields = ('spend_transaction__account__user__username',)


@admin.register(RecentlyViewedProduct)
class RecentlyViewedProductAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'viewed_at')
    search_fields = ('user__username', 'user__email', 'product__name')
    list_filter = ('viewed_at',)
