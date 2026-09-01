from django import forms
from django.contrib import admin
from django.shortcuts import render

from .models import (
    Banner,
    Brand,
    Cable,
    Charger,
    Headphone,
    PowerBank,
    Product,
    ProductGroup,
    ProductImage,
    Smartphone,
)


class CustomDiscountForm(forms.Form):
    discount_percent = forms.IntegerField(
        label="Процент скидки (%)",
        min_value=0,
        max_value=100,
        initial=10,
        widget=forms.NumberInput(
            attrs={
                "class": "vIntegerField",
                "style": "width: 120px;",
                "min": 0,
                "max": 100,
            }
        ),
    )


@admin.action(description="Установить скидку для выбранных товаров")
def set_custom_discount(modeladmin, request, queryset):
    if "apply" in request.POST:
        form = CustomDiscountForm(request.POST)
        if form.is_valid():
            discount_value = form.cleaned_data["discount_percent"]
            updated_count = queryset.update(discount=discount_value)
            modeladmin.message_user(
                request,
                f"Скидка {discount_value}% успешно применена к {updated_count} товарам.",
            )
            return None
    else:
        form = CustomDiscountForm()

    return render(
        request,
        "admin/apply_discount_intermediate.html",
        {
            "form": form,
            "queryset": queryset,
            "action_name": "set_custom_discount",
            "opts": modeladmin.model._meta,
            "title": "Установка скидки",
        },
    )


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 4
    fields = ("image",)
    ordering = ("id",)


class CommonProductAdminMixin:
    list_display = ("name", "brand", "price", "discount", "stock", "available")
    list_editable = ("price", "stock", "available")
    list_filter = ("available", "brand")
    search_fields = ("name", "slug", "brand__name")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline]
    actions = [set_custom_discount]


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Smartphone)
class SmartphoneAdmin(CommonProductAdminMixin, admin.ModelAdmin):
    fieldsets = (
        (
            "Группа и цвет",
            {
                "fields": (
                    "group",
                    "color",
                    "color_code",
                )
            },
        ),
        (
            "Основная информация",
            {
                "fields": (
                    "brand",
                    "name",
                    "slug",
                    "image",
                    "description",
                    "price",
                    "discount",
                    "stock",
                    "available",
                )
            },
        ),
        (
            "Дисплей",
            {
                "fields": (
                    "display_type",
                    "display_refresh_rate",
                    "display_size",
                    "display_resolution",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Связь и SIM-карты",
            {
                "fields": (
                    "communication_standards",
                    "quantity_of_sim_cards",
                    "sim_card_type",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Память и процессор",
            {
                "fields": (
                    "ram",
                    "storage",
                    "extra_storage",
                    "processor",
                    "core_count",
                    "core_speed",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Автономность и ОС",
            {
                "fields": ("battery_capacity", "charging_type", "operating_system"),
                "classes": ("collapse",),
            },
        ),
        (
            "Камера",
            {
                "fields": ("main_camera", "front_camera"),
                "classes": ("collapse",),
            },
        ),
        (
            "Интерфейсы и корпус",
            {
                "fields": (
                    "wi_fi_standards",
                    "bluetooth_version",
                    "nfc_support",
                    "navigational_systems",
                    "interfaces_usb",
                    "protection_class",
                    "material",
                ),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Headphone)
class HeadphoneAdmin(CommonProductAdminMixin, admin.ModelAdmin):
    pass


@admin.register(Charger)
class ChargerAdmin(CommonProductAdminMixin, admin.ModelAdmin):
    pass


@admin.register(Cable)
class CableAdmin(CommonProductAdminMixin, admin.ModelAdmin):
    pass


@admin.register(PowerBank)
class PowerBankAdmin(CommonProductAdminMixin, admin.ModelAdmin):
    pass


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "created_at")
    list_editable = ("is_active",)
    list_filter = ("is_active",)
    search_fields = ("title", "subtitle")


class ProductInline(admin.TabularInline):
    model = Product
    fields = ("name", "color", "color_code", "price", "stock", "available")
    readonly_fields = ("name", "color", "color_code", "price", "stock", "available")
    extra = 0
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ProductGroup)
class ProductGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "get_products_count")
    search_fields = ("name",)
    inlines = [ProductInline]

    @admin.display(description="Количество товаров")
    def get_products_count(self, obj):
        return obj.products.count()