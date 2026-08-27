from django.contrib import admin
from .models import Brand, Smartphone, Headphone, Charger, Cable, PowerBank, Banner, ProductImage

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 4  # Количество пустых строк для загрузки новых фото по умолчанию

@admin.register(Smartphone)
class SmartphoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'price', 'stock', 'available']
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]  # Добавляем возможность загружать фото прямо в админке смартфонов
    
    # Группировка полей по блокам в админке
    fieldsets = (
        ('Основная информация', {
            'fields': ('brand', 'name', 'slug', 'image', 'description', 'color', 'price', 'stock', 'available')
        }),
        ('Дисплей', {
            'fields': ('display_type', 'display_refresh_rate', 'display_size', 'display_resolution'),
            'classes': ('collapse',), # Блок можно сворачивать
        }),
        ('Связь и SIM-карты', {
            'fields': ('communication_standards', 'quantity_of_sim_cards', 'sim_card_type'),
            'classes': ('collapse',),
        }),
        ('Память и процессор', {
            'fields': ('ram', 'storage', 'extra_storage', 'processor', 'core_count', 'core_speed'),
            'classes': ('collapse',),
        }),
        ('Автономность и ОС', {
            'fields': ('battery_capacity', 'charging_type', 'operating_system'),
            'classes': ('collapse',),
        }),
        ('Камера', {
            'fields': ('main_camera', 'front_camera'),
            'classes': ('collapse',),
        }),
        ('Интерфейсы и корпус', {
            'fields': ('wi_fi_standards', 'bluetooth_version', 'nfc_support', 'navigational_systems', 'interfaces_usb', 'protection_class', 'material'),
            'classes': ('collapse',),
        }),
    )

@admin.register(Headphone)
class HeadphoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'price', 'stock', 'available']
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]

@admin.register(Charger)
class ChargerAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'price', 'stock', 'available']
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]

@admin.register(Cable)
class CableAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'price', 'stock', 'available']
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]

@admin.register(PowerBank)
class PowerBankAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'price', 'stock', 'available']
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'created_at']