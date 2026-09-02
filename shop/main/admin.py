from django import forms
from django.contrib import admin, messages
from django.db.models import Count
from django.shortcuts import render

from .models import Banner, Brand, Cable, Charger, Headphone, PowerBank, Product, ProductGroup, ProductImage, Smartphone


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
        # 1. Сохраняем фотографии исходного товара в память
        original_images = list(ProductImage.objects.filter(product=obj))

        # 2. Клонируем запись товара
        obj.pk = None
        obj.id = None
        # Если модель наследуется от Product, сбрасываем указатель на родителя
        if hasattr(obj, 'product_ptr_id'):
            obj.product_ptr_id = None

        obj.name = f"{obj.name} (Копия)"

        # Генерируем уникальный slug, чтобы не было ошибок IntegrityError
        if hasattr(obj, 'slug') and obj.slug:
            base_slug = f"{obj.slug}-copy"
            new_slug = base_slug
            counter = 1
            while modeladmin.model.objects.filter(slug=new_slug).exists():
                new_slug = f"{base_slug}-{counter}"
                counter += 1
            obj.slug = new_slug

        # Сохраняем новый товар
        obj.save()

        # 3. Создаем копии фотографий галереи для нового товара
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


@admin.register(Smartphone)
class SmartphoneAdmin(CommonProductAdminMixin, admin.ModelAdmin):
    fieldsets = (
        ('Группа и цвет', {'fields': ('group', 'color', 'color_code')}),
        ('Основная информация', {'fields': ('brand', 'name', 'slug', 'image', 'description', 'price', 'discount', 'stock', 'available')}),
        ('Дисплей', {'fields': ('display_type', 'display_refresh_rate', 'display_size', 'display_resolution'), 'classes': ('collapse',)}),
        ('Связь и SIM-карты', {'fields': ('communication_standards', 'quantity_of_sim_cards', 'sim_card_type'), 'classes': ('collapse',)}),
        ('Память и процессор', {'fields': ('ram', 'storage', 'extra_storage', 'processor', 'core_count', 'core_speed'), 'classes': ('collapse',)}),
        ('Автономность и ОС', {'fields': ('battery_capacity', 'charging_type', 'operating_system'), 'classes': ('collapse',)}),
        ('Камера', {'fields': ('main_camera', 'front_camera'), 'classes': ('collapse',)}),
        ('Интерфейсы и корпус', {'fields': ('wi_fi_standards', 'bluetooth_version', 'nfc_support', 'navigational_systems', 'interfaces_usb', 'protection_class', 'material'), 'classes': ('collapse',)}),
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
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_products_count=Count('products', distinct=True))

    @admin.display(description='Количество товаров', ordering='_products_count')
    def products_count(self, obj):
        return obj._products_count