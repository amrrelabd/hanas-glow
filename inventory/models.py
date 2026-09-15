from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=64, unique=True)
    category = models.CharField(max_length=100)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    sell_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class StockMovement(models.Model):
    class Reason(models.TextChoices):
        PURCHASE = 'purchase', 'Purchase'
        SALE = 'sale', 'Sale'
        RETURN = 'return', 'Return'
        DAMAGED_LOST = 'damaged_lost', 'Damaged/Lost'
        ADJUSTMENT = 'adjustment', 'Adjustment'

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    quantity_delta = models.IntegerField()
    reason = models.CharField(max_length=20, choices=Reason.choices)
    reference_id = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name}: {self.quantity_delta:+d} ({self.reason})"


@receiver(post_save, sender=StockMovement)
@receiver(post_delete, sender=StockMovement)
def sync_product_stock_quantity(sender, instance, **kwargs):
    total = instance.product.stock_movements.aggregate(total=Sum('quantity_delta'))['total'] or 0
    Product.objects.filter(pk=instance.product_id).update(stock_quantity=total)
