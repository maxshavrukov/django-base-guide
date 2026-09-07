from copy import copy

from django import forms
from django.contrib import admin, messages
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from .models import (
    Banner, Brand, Cable, Category, CartPromotion, Charger, Headphone, PowerBank,
    Product, ProductGroup, ProductImage, ProductPromotion, Smartphone, MainCategory, SubCategory,
)


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

    with transaction.atomic():
        for original in queryset:
            original_images = list(ProductImage.objects.filter(product=original))
            obj = copy(original)
            obj.pk = None
            obj.id = None
            if hasattr(obj, 'product_ptr_id'):
                obj.product_ptr_id = None

            obj.name = f"{original.name} (Копия)"

            if getattr(obj, 'slug', None):
                base_slug = f"{original.slug}-copy"
                new_slug = base_slug
                counter = 1
                while modeladmin.model.objects.filter(slug=new_slug).exists():
                    new_slug = f"{base_slug}-{counter}"
                    counter += 1
                obj.slug = new_slug

            obj.save()

            for img in original_images:
                ProductImage.objects.create(product=obj, image=img.image)

            created_count += 1

    modeladmin.message_user(
        request,
        f'Успешно дублировано товаров: {created_count} (все фото скопированы).',
        messages.SUCCESS,
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




class RootCategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'slug', 'product_type', 'sort_order', 'is_active')

    def clean_parent(self):
        return None


class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'slug', 'parent', 'sort_order', 'is_active')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = Category.objects.filter(
            parent__isnull=True,
            is_active=True,
        ).order_by('sort_order', 'name')
        if self.instance and self.instance.parent_id:
            queryset = Category.objects.filter(
                Q(pk=self.instance.parent_id) | Q(parent__isnull=True, is_active=True)
            ).order_by('sort_order', 'name')
        self.fields['parent'].queryset = queryset
        self.fields['parent'].label = 'Родительская категория'
        self.fields['parent'].help_text = 'Выберите основную категорию, внутри которой находится эта подкатегория.'

    def clean_parent(self):
        parent = self.cleaned_data['parent']
        if parent and parent.parent_id is not None:
            raise forms.ValidationError('Родительской категорией может быть только основная категория.')
        return parent


@admin.register(MainCategory)
class MainCategoryAdmin(admin.ModelAdmin):
    form = RootCategoryForm
    list_display = ('name', 'slug', 'product_type', 'sort_order', 'is_active')
    list_filter = ('product_type', 'is_active')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('sort_order', 'is_active')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(parent__isnull=True)

    def save_model(self, request, obj, form, change):
        obj.parent = None
        super().save_model(request, obj, form, change)


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    form = SubCategoryForm
    list_display = ('name', 'parent', 'sort_order', 'is_active')
    list_filter = ('parent', 'is_active')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('sort_order', 'is_active')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(parent__isnull=False)

    def save_model(self, request, obj, form, change):
        obj.product_type = obj.get_effective_product_type()
        super().save_model(request, obj, form, change)


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


@admin.register(ProductPromotion)
class ProductPromotionAdmin(admin.ModelAdmin):
    list_display = ('name', 'target_type', 'discount_percent', 'starts_at', 'ends_at', 'current_status', 'is_active')
    list_filter = ('target_type', 'is_active')
    search_fields = ('name',)
    list_editable = ('discount_percent', 'is_active')
    fieldsets = (
        ('Основная информация', {'fields': ('name', 'discount_percent', 'is_active', 'starts_at', 'ends_at')}),
        ('На что распространяется', {'fields': ('target_type', 'brand', 'category', 'group', 'product')}),
    )

    @admin.display(description='Статус', ordering='is_active')
    def current_status(self, obj):
        if not obj.is_active:
            return 'Отключена'
        now = timezone.now()
        if obj.starts_at and obj.starts_at > now:
            return 'Запланирована'
        if obj.ends_at and obj.ends_at < now:
            return 'Завершена'
        return 'Действует'


@admin.register(CartPromotion)
class CartPromotionAdmin(admin.ModelAdmin):
    list_display = ('name', 'rule_type', 'discount_percent', 'min_quantity', 'registered_only', 'starts_at', 'ends_at', 'current_status', 'is_active')
    list_filter = ('rule_type', 'registered_only', 'is_active')
    search_fields = ('name',)
    list_editable = ('discount_percent', 'min_quantity', 'is_active')
    fieldsets = (
        ('Основная информация', {'fields': ('name', 'discount_percent', 'is_active', 'starts_at', 'ends_at')}),
        ('Правило применения', {'fields': ('rule_type', 'min_quantity', 'nth_position', 'registered_only')}),
    )


    @admin.display(description='Статус', ordering='is_active')
    def current_status(self, obj):
        if not obj.is_active:
            return 'Отключена'
        now = timezone.now()
        if obj.starts_at and obj.starts_at > now:
            return 'Запланирована'
        if obj.ends_at and obj.ends_at < now:
            return 'Завершена'
        return 'Действует'


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


class ProductGroupForm(forms.ModelForm):
    class Meta:
        model = ProductGroup
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = Category.objects.filter(
            parent__isnull=False,
            is_active=True,
        ).select_related('parent').order_by('parent__sort_order', 'sort_order', 'name')
        selected_ids = list(self.instance.categories.values_list('pk', flat=True)) if self.instance.pk else []
        if selected_ids:
            queryset = Category.objects.filter(
                Q(pk__in=selected_ids) | Q(parent__isnull=False, is_active=True)
            ).select_related('parent').order_by('parent__sort_order', 'sort_order', 'name')
        self.fields['categories'].queryset = queryset


@admin.register(ProductGroup)
class ProductGroupAdmin(admin.ModelAdmin):
    form = ProductGroupForm
    list_display = ('name', 'slug', 'products_count')
    filter_horizontal = ('categories',)
    list_filter = ('categories',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_products_count=Count('products', distinct=True))

    @admin.display(description='Количество товаров', ordering='_products_count')
    def products_count(self, obj):
        return obj._products_count


# ==========================================
# Виртуальная группировка моделей в админке
# ==========================================
_original_get_app_list = admin.AdminSite.get_app_list

def get_grouped_app_list(self, request, app_label=None):
    app_list = _original_get_app_list(self, request, app_label)
    groups = {
        '1. Структура каталога': [
            'maincategory',
            'subcategory',
            'brand',
            'productgroup',
        ],
        '2. Товары': [
            'smartphone',
            'headphone',
            'powerbank',
            'charger',
            'cable',
        ],
        '3. Маркетинг': [
            'productpromotion',
            'cartpromotion',
            'banner',
        ],
    }
    models_dict = {}
    for app in app_list:
        for model in app['models']:
            models_dict[model['object_name'].lower()] = model
    placed_models = set()
    new_app_list = []
    for group_name, model_names in groups.items():
        group_models = []
        for name in model_names:
            if name in models_dict:
                group_models.append(models_dict[name])
                placed_models.add(name)
        if group_models:
            new_app_list.append({
                'name': group_name,
                'app_label': group_name.lower().replace(' ', '_'),
                'app_url': '',
                'has_module_perms': True,
                'models': group_models,
            })
    for app in app_list:
        remaining_models = [
            m for m in app['models']
            if m['object_name'].lower() not in placed_models
        ]
        if remaining_models:
            app_copy = app.copy()
            app_copy['models'] = remaining_models
            new_app_list.append(app_copy)
    return new_app_list

admin.AdminSite.get_app_list = get_grouped_app_list
