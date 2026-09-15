from django.contrib import admin

from .models import Product, StockMovement, Supplier


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'stock_quantity', 'sell_price')


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    pass


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    pass
