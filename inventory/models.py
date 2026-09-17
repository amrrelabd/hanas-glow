from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_delete, post_save, pre_save
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
    brand = models.CharField(max_length=100, blank=True)
    shade_color = models.CharField(max_length=100, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    sell_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock_quantity = models.IntegerField(default=0)
    min_stock_alert = models.IntegerField(default=0)
    barcode = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
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


class Customer(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    class Channel(models.TextChoices):
        WHATSAPP = 'whatsapp', 'WhatsApp'
        FACEBOOK = 'facebook', 'Facebook'
        INSTAGRAM = 'instagram', 'Instagram'
        WEBSITE = 'website', 'Website'
        OTHER = 'other', 'Other'

    class PaymentStatus(models.TextChoices):
        PAID = 'paid', 'Paid'
        UNPAID = 'unpaid', 'Unpaid'
        PARTIAL = 'partial', 'Partial'

    class DeliveryStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'

    order_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    order_date = models.DateField()
    channel = models.CharField(max_length=20, choices=Channel.choices, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    delivery_status = models.CharField(max_length=20, choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.order.order_number} - {self.product.name} x{self.quantity}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity


@receiver(post_save, sender=OrderItem)
def create_sale_stock_movement(sender, instance, created, **kwargs):
    if created:
        StockMovement.objects.create(
            product=instance.product,
            quantity_delta=-instance.quantity,
            reason=StockMovement.Reason.SALE,
            reference_id=instance.order.order_number,
        )


class Purchase(models.Model):
    class PaymentStatus(models.TextChoices):
        PAID = 'paid', 'Paid'
        UNPAID = 'unpaid', 'Unpaid'

    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    purchase_date = models.DateField()
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Purchase #{self.pk} - {self.supplier}"


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.purchase} - {self.product.name} x{self.quantity}"

    @property
    def line_total(self):
        return self.cost_per_unit * self.quantity


@receiver(post_save, sender=PurchaseItem)
def create_purchase_stock_movement(sender, instance, created, **kwargs):
    if created:
        StockMovement.objects.create(
            product=instance.product,
            quantity_delta=instance.quantity,
            reason=StockMovement.Reason.PURCHASE,
            reference_id=str(instance.purchase_id),
        )


class Return(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    return_date = models.DateField()
    quantity = models.PositiveIntegerField(default=1)
    reason = models.CharField(max_length=255, blank=True)
    restock = models.BooleanField(default=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Return - {self.product.name} x{self.quantity}"


@receiver(post_save, sender=Return)
def create_return_stock_movement(sender, instance, created, **kwargs):
    if created and instance.restock:
        StockMovement.objects.create(
            product=instance.product,
            quantity_delta=instance.quantity,
            reason=StockMovement.Reason.RETURN,
            reference_id=instance.order.order_number if instance.order else '',
        )


class DamagedLoss(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    date = models.DateField()
    quantity = models.PositiveIntegerField(default=1)
    reason = models.CharField(max_length=255, blank=True)
    cost_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Damaged/Lost - {self.product.name} x{self.quantity}"


@receiver(post_save, sender=DamagedLoss)
def create_damaged_loss_stock_movement(sender, instance, created, **kwargs):
    if created:
        StockMovement.objects.create(
            product=instance.product,
            quantity_delta=-instance.quantity,
            reason=StockMovement.Reason.DAMAGED_LOST,
        )


class Expense(models.Model):
    date = models.DateField()
    category = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.category} - {self.amount}"


class Coupon(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', 'Percentage'
        FIXED = 'fixed', 'Fixed'

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DiscountType.choices)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.code


class SpecialOrder(models.Model):
    class Status(models.TextChoices):
        REQUESTED = 'requested', 'Requested'
        ORDERED = 'ordered', 'Ordered from Supplier'
        RECEIVED = 'received', 'Received'
        GIVEN = 'given', 'Given to Customer'

    customer_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    item_requested = models.CharField(max_length=255)
    shade_color = models.CharField(max_length=100, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    agreed_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deposit_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    date_requested = models.DateField()
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.customer_name} - {self.item_requested}"

    @property
    def balance_remaining(self):
        return self.agreed_price - self.deposit_paid


# ---------------------------------------------------------------------------
# Accounting: Chart of Accounts + double-entry Journal
# ---------------------------------------------------------------------------

class Account(models.Model):
    class Type(models.TextChoices):
        ASSET = 'asset', 'Asset'
        LIABILITY = 'liability', 'Liability'
        EQUITY = 'equity', 'Equity'
        INCOME = 'income', 'Income'
        EXPENSE = 'expense', 'Expense'

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=Type.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f'{self.code} - {self.name}'

    @property
    def balance(self):
        totals = self.lines.aggregate(debit=Sum('debit'), credit=Sum('credit'))
        debit = totals['debit'] or Decimal('0')
        credit = totals['credit'] or Decimal('0')
        if self.type in (Account.Type.ASSET, Account.Type.EXPENSE):
            return debit - credit
        return credit - debit


class JournalEntry(models.Model):
    class Source(models.TextChoices):
        ORDER = 'order', 'Order'
        PURCHASE = 'purchase', 'Purchase'
        EXPENSE = 'expense', 'Expense'
        RETURN = 'return', 'Return'
        DAMAGED_LOST = 'damaged_lost', 'Damaged/Lost'
        SPECIAL_ORDER = 'special_order', 'Special Order Deposit'
        MANUAL = 'manual', 'Manual'

    date = models.DateField()
    reference = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=255, blank=True)
    source_type = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']
        verbose_name_plural = 'Journal Entries'

    def __str__(self):
        return f'{self.date} - {self.description}'

    @property
    def total_debit(self):
        return self.lines.aggregate(total=Sum('debit'))['total'] or Decimal('0')

    @property
    def total_credit(self):
        return self.lines.aggregate(total=Sum('credit'))['total'] or Decimal('0')


class JournalLine(models.Model):
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='lines')
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f'{self.account.code} D:{self.debit} C:{self.credit}'


def post_journal_entry(date, source_type, reference='', description='', lines=None):
    """Create a balanced journal entry. `lines` is a list of (account_code, debit, credit)."""
    lines = lines or []
    entry = JournalEntry.objects.create(
        date=date, reference=reference, description=description, source_type=source_type,
    )
    for account_code, debit, credit in lines:
        account = Account.objects.get(code=account_code)
        JournalLine.objects.create(entry=entry, account=account, debit=debit or 0, credit=credit or 0)
    return entry


# --- Auto-posting signals -------------------------------------------------

@receiver(post_save, sender=OrderItem)
def post_sale_journal_entry(sender, instance, created, **kwargs):
    if not created:
        return
    order = instance.order
    revenue = instance.unit_price * instance.quantity
    cogs = instance.product.cost_price * instance.quantity
    receivable_account = '1010' if order.payment_status != Order.PaymentStatus.PAID else '1000'
    post_journal_entry(
        date=order.order_date,
        source_type=JournalEntry.Source.ORDER,
        reference=order.order_number,
        description=f'Sale - {instance.product.name} x{instance.quantity}',
        lines=[
            (receivable_account, revenue, 0),
            ('4000', 0, revenue),
            ('5000', cogs, 0),
            ('1020', 0, cogs),
        ],
    )


@receiver(post_save, sender=PurchaseItem)
def post_purchase_journal_entry(sender, instance, created, **kwargs):
    if not created:
        return
    purchase = instance.purchase
    amount = instance.cost_per_unit * instance.quantity
    credit_account = '1000' if purchase.payment_status == Purchase.PaymentStatus.PAID else '2000'
    post_journal_entry(
        date=purchase.purchase_date,
        source_type=JournalEntry.Source.PURCHASE,
        reference=str(purchase.pk),
        description=f'Purchase - {instance.product.name} x{instance.quantity}',
        lines=[
            ('1020', amount, 0),
            (credit_account, 0, amount),
        ],
    )


@receiver(post_save, sender=Expense)
def post_expense_journal_entry(sender, instance, created, **kwargs):
    if not created:
        return
    post_journal_entry(
        date=instance.date,
        source_type=JournalEntry.Source.EXPENSE,
        reference=str(instance.pk),
        description=f'Expense - {instance.category}',
        lines=[
            ('5010', instance.amount, 0),
            ('1000', 0, instance.amount),
        ],
    )


@receiver(post_save, sender=Return)
def post_return_journal_entry(sender, instance, created, **kwargs):
    if not created:
        return
    cogs_value = instance.product.cost_price * instance.quantity
    receivable_account = '1010' if (instance.order and instance.order.payment_status != Order.PaymentStatus.PAID) else '1000'
    lines = [
        ('4000', instance.refund_amount, 0),
        (receivable_account, 0, instance.refund_amount),
    ]
    if instance.restock:
        lines += [
            ('1020', cogs_value, 0),
            ('5000', 0, cogs_value),
        ]
    post_journal_entry(
        date=instance.return_date,
        source_type=JournalEntry.Source.RETURN,
        reference=instance.order.order_number if instance.order else '',
        description=f'Return - {instance.product.name} x{instance.quantity}',
        lines=lines,
    )


@receiver(post_save, sender=DamagedLoss)
def post_damaged_loss_journal_entry(sender, instance, created, **kwargs):
    if not created:
        return
    value = instance.cost_value or (instance.product.cost_price * instance.quantity)
    post_journal_entry(
        date=instance.date,
        source_type=JournalEntry.Source.DAMAGED_LOST,
        reference='',
        description=f'Damaged/Lost - {instance.product.name} x{instance.quantity}',
        lines=[
            ('5020', value, 0),
            ('1020', 0, value),
        ],
    )


@receiver(pre_save, sender=SpecialOrder)
def post_special_order_deposit_journal_entry(sender, instance, **kwargs):
    previous_deposit = Decimal('0')
    if instance.pk:
        previous = SpecialOrder.objects.filter(pk=instance.pk).values_list('deposit_paid', flat=True).first()
        previous_deposit = previous or Decimal('0')
    delta = (instance.deposit_paid or Decimal('0')) - previous_deposit
    if delta > 0:
        post_journal_entry(
            date=instance.date_requested,
            source_type=JournalEntry.Source.SPECIAL_ORDER,
            reference=str(instance.pk or ''),
            description=f'Special order deposit - {instance.customer_name}',
            lines=[
                ('1000', delta, 0),
                ('4000', 0, delta),
            ],
        )
