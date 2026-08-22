from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0
    readonly_fields = ['price', 'quantity']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'first_name', 
        'phone', 
        'address', 
        'get_items_summary', 
        'get_total_cost', 
        'paid', 
        'created'
    ]
    
    list_filter = ['paid', 'created']
    search_fields = ['first_name', 'phone', 'address', 'email']
    inlines = [OrderItemInline]
    ordering = ['-created']

    @admin.display(description='Состав заказа')
    def get_items_summary(self, obj):
        # Если обратная связь называется иначе (например, order_items), 
        # Django использует obj.items по умолчанию для related_name='items'
        items = getattr(obj, 'items', None)
        if items:
            return ", ".join([f"{item.product.name} (x{item.quantity})" for item in items.all()])
        return "—"

    @admin.display(description='Сумма (грн)')
    def get_total_cost(self, obj):
        if hasattr(obj, 'get_total_cost'):
            return f"{obj.get_total_cost()} грн."
        items = getattr(obj, 'items', None)
        if items:
            total = sum(item.price * item.quantity for item in items.all())
            return f"{total} грн."
        return "0 грн."