from django import forms
from django.contrib import admin, messages
from django.db.models import Count
from django.shortcuts import render

from .models import Banner, Brand, Cable, Category, Charger, Headphone, PowerBank, Product, ProductGroup, ProductImage, Smartphone


class CustomDiscountForm(forms.Form):
    discount_percent = forms.IntegerField(
        label='Процент скидки (%)',
        min_value=0,
        max_value=100,
        initial=10,
        widget=forms.NumberInput(attrs={'class': 'vIntegerField', 'min': 0, 'max': 100}),
    )


@admin.action(description='Установить скидку для выбранных товаров')
def set_custom_discount(modeladmin, request, queryset):
    if 'apply' in request.POST:
        form = CustomDiscountForm(request.POST)
        if form.is_valid():
            value = form.cleaned_data['discount_percent']
            count = queryset.update(discount=value)
            modeladmin.message_user(request, f'Скидка {value}% применена к {count} товарам.')
            return None
    else:
        form = CustomDiscountForm()

    return render(request, 'admin/apply_discount_intermediate.html', {
        'form': form,
        'queryset': queryset,
        'action_name': 'set_custom_discount',
        'opts': modeladmin.model._meta,
        'title': 'Установка скидки',
    })


@admin.action(description='Дублировать выбранные товары (вместе с фото)')
def duplicate_products(modeladmin, request, queryset):
    created_count = 0

    for obj in queryset:
        original_images = list(ProductImage.objects.filter(product=obj))

        obj.pk = None
        obj.id = None
        if hasattr(obj, 'product_ptr_id'):
            obj.product_ptr_id = None

        obj.name = f"{obj.name} (Копия)"

        if hasattr(obj, 'slug') and obj.slug:
            base_slug = f"{obj.slug}-copy"
            new_slug = base_slug
            counter = 1
            while modeladmin.model.objects.filter(slug=new_slug).exists():
                new_slug = f"{base_slug}-{counter}"
                counter += 1
            obj.slug = new_slug

        obj.save()

        for img in original_images:
            ProductImage.objects.create(
                product=obj,
                image=img.image
            )

        created_count += 1

    modeladmin.message_user(
        request,
        f'Успешно дублировано товаров: {created_count} (все фото скопированы).',
        messages.SUCCESS
    )


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 4
    fields = ('image',)
    ordering = ('id',)


class CommonProductAdminMixin:
    save_as = True
    list_display = ('name', 'brand', 'price', 'discount', 'stock', 'available')
    list_editable = ('price', 'discount', 'stock', 'available')
    list_filter = ('available', 'brand', 'discount')
    search_fields = ('name', 'slug', 'brand__name')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    actions = [set_custom_discount, duplicate_products]


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}




@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'product_type', 'sort_order', 'is_active')
    list_filter = ('product_type', 'is_active', 'parent')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('sort_order', 'is_active')

@admin.register(Smartphone)
class SmartphoneAdmin(CommonProductAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'brand', 'price', 'discount', 'stock', 'ram', 'storage', 'available')
    list_filter = ('brand', 'operating_system', 'nfc_support', 'has_esim', 'available')
    
    fieldsets = (
        ("Основная информация", {
            "fields": ("name", "slug", "brand", "group", "price", "discount", "stock", "available", "color", "color_code", "image", "description")
        }),
        ("Дисплей", {
            "fields": ("display_type", "display_size", "display_resolution", "display_refresh_rate")
        }),
        ("Процессор и графика", {
            "fields": ("processor", "gpu", "core_count", "core_speed")
        }),
        ("Память и слоты", {
            "fields": ("ram", "storage", "slot_config", "max_sd_capacity")
        }),
        ("Камеры", {
            "fields": ("main_camera_mp", "main_camera_desc", "front_camera_mp", "max_video_resolution", "optical_zoom")
        }),
        ("Аккумулятор и зарядка", {
            "fields": ("battery_capacity", "charging_power", "has_wireless_charging", "has_reverse_charging")
        }),
        ("Связь и интерфейсы", {
            "fields": ("communication_standards", "sim_count", "has_esim", "usb_type", "nfc_support", "has_jack_3_5", "wi_fi_standards", "bluetooth_version")
        }),
        ("Корпус и ОС", {
            "fields": ("operating_system", "os_version", "protection_class", "material")
        }),
    )


@admin.register(Headphone)
class HeadphoneAdmin(CommonProductAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'brand', 'price', 'discount', 'stock', 'headphone_type', 'connection_type', 'has_anc', 'available')
    list_filter = ('brand', 'headphone_type', 'connection_type', 'has_anc', 'available')
    
    fieldsets = (
        ("Основная информация", {"fields": ("name", "slug", "brand", "group", "price", "discount", "stock", "available", "color", "color_code", "image", "description")}),
        ("Тип и звук", {"fields": ("headphone_type", "connection_type", "has_anc", "has_transparency_mode", "audio_codecs")}),
        ("Автономность", {"fields": ("battery_life_hours", "total_battery_life_hours", "has_wireless_charging_case")}),
        ("Дополнительно", {"fields": ("bluetooth_version", "has_microphone", "protection_class")}),
    )


@admin.register(Charger)
class ChargerAdmin(CommonProductAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'brand', 'price', 'discount', 'stock', 'charger_type', 'max_power_w', 'is_gan', 'available')
    list_filter = ('brand', 'charger_type', 'is_gan', 'available')
    
    fieldsets = (
        ("Основная информация", {"fields": ("name", "slug", "brand", "group", "price", "discount", "stock", "available", "color", "color_code", "image", "description")}),
        ("Характеристики", {"fields": ("charger_type", "max_power_w", "usb_c_ports", "usb_a_ports", "is_gan", "fast_charging_protocols", "has_cable_included")}),
    )


@admin.register(Cable)
class CableAdmin(CommonProductAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'brand', 'price', 'discount', 'stock', 'connector_from', 'connector_to', 'length_m', 'max_power_w', 'available')
    list_filter = ('brand', 'connector_from', 'connector_to', 'available')
    
    fieldsets = (
        ("Основная информация", {"fields": ("name", "slug", "brand", "group", "price", "discount", "stock", "available", "color", "color_code", "image", "description")}),
        ("Параметры кабеля", {"fields": ("connector_from", "connector_to", "length_m", "max_power_w", "max_current_a", "data_transfer_speed", "braiding_material")}),
    )


@admin.register(PowerBank)
class PowerBankAdmin(CommonProductAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'brand', 'price', 'discount', 'stock', 'capacity_mah', 'max_power_w', 'has_wireless_charging', 'available')
    list_filter = ('brand', 'has_wireless_charging', 'has_magsafe', 'available')
    
    fieldsets = (
        ("Основная информация", {"fields": ("name", "slug", "brand", "group", "price", "discount", "stock", "available", "color", "color_code", "image", "description")}),
        ("Емкость и мощность", {"fields": ("capacity_mah", "max_power_w", "usb_c_ports", "usb_a_ports", "display_type")}),
        ("Доп. функции", {"fields": ("has_wireless_charging", "has_magsafe", "has_built_in_cable", "is_pass_through_supported")}),
    )


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    list_editable = ('is_active',)
    list_filter = ('is_active',)
    search_fields = ('title', 'subtitle')


class ProductInline(admin.TabularInline):
    model = Product
    fields = ('name', 'brand', 'color', 'color_code', 'price', 'discount', 'stock', 'available')
    readonly_fields = ('name', 'brand', 'color', 'color_code', 'price', 'discount', 'stock', 'available')
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ProductGroup)
class ProductGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'products_count')
    filter_horizontal = ('categories',)
    list_filter = ('categories',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductInline]

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'categories':
            kwargs['queryset'] = Category.objects.filter(parent__isnull=False, is_active=True).select_related('parent')
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_products_count=Count('products', distinct=True))

    @admin.display(description='Количество товаров', ordering='_products_count')
    def products_count(self, obj):
        return obj._products_count