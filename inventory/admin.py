from django.contrib import admin

from .models import (
    Account,
    Coupon,
    Customer,
    DamagedLoss,
    Expense,
    JournalEntry,
    JournalLine,
    Order,
    OrderItem,
    Product,
    Purchase,
    PurchaseItem,
    Return,
    SpecialOrder,
    StockMovement,
    Supplier,
)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'stock_quantity', 'sell_price')
    search_fields = ('name', 'sku', 'barcode')
    list_filter = ('category', 'brand', 'supplier')


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone')
    search_fields = ('name',)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity_delta', 'reason', 'reference_id', 'created_at')
    list_filter = ('reason',)
    search_fields = ('product__name', 'reference_id')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'city')
    search_fields = ('name', 'phone')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'order_date', 'payment_status', 'delivery_status')
    list_filter = ('payment_status', 'delivery_status', 'channel')
    search_fields = ('order_number', 'customer__name')
    inlines = [OrderItemInline]


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'purchase_date', 'payment_status')
    list_filter = ('supplier', 'payment_status')
    inlines = [PurchaseItemInline]


@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'return_date', 'restock', 'refund_amount')
    list_filter = ('restock',)


@admin.register(DamagedLoss)
class DamagedLossAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'date', 'cost_value')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('date', 'category', 'amount')
    list_filter = ('category',)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'active')
    list_filter = ('active', 'discount_type')


@admin.register(SpecialOrder)
class SpecialOrderAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'item_requested', 'status', 'date_requested')
    list_filter = ('status',)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'type', 'balance', 'is_active')
    list_filter = ('type', 'is_active')


class JournalLineInline(admin.TabularInline):
    model = JournalLine
    extra = 0


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('date', 'description', 'source_type', 'reference', 'total_debit', 'total_credit')
    list_filter = ('source_type',)
    search_fields = ('reference', 'description')
    inlines = [JournalLineInline]
