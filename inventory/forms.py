from django import forms
from django.forms import inlineformset_factory

from .models import (
    Coupon,
    Customer,
    DamagedLoss,
    Expense,
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

WIDGET_ATTRS = {'class': 'form-control'}
SELECT_ATTRS = {'class': 'form-select'}
CHECK_ATTRS = {'class': 'form-check-input'}


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'phone']
        widgets = {'name': forms.TextInput(attrs=WIDGET_ATTRS), 'phone': forms.TextInput(attrs=WIDGET_ATTRS)}


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'city', 'address', 'notes']
        widgets = {
            'name': forms.TextInput(attrs=WIDGET_ATTRS),
            'phone': forms.TextInput(attrs=WIDGET_ATTRS),
            'city': forms.TextInput(attrs=WIDGET_ATTRS),
            'address': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 2}),
            'notes': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 2}),
        }


class ProductForm(forms.ModelForm):
    opening_stock = forms.IntegerField(
        required=False, initial=0, min_value=0,
        help_text='Only used when creating a new product.',
        widget=forms.NumberInput(attrs=WIDGET_ATTRS),
    )

    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'category', 'brand', 'shade_color', 'supplier',
            'cost_price', 'sell_price', 'discount_price', 'min_stock_alert',
            'barcode', 'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs=WIDGET_ATTRS),
            'sku': forms.TextInput(attrs=WIDGET_ATTRS),
            'category': forms.TextInput(attrs=WIDGET_ATTRS),
            'brand': forms.TextInput(attrs=WIDGET_ATTRS),
            'shade_color': forms.TextInput(attrs=WIDGET_ATTRS),
            'supplier': forms.Select(attrs=SELECT_ATTRS),
            'cost_price': forms.NumberInput(attrs=WIDGET_ATTRS),
            'sell_price': forms.NumberInput(attrs=WIDGET_ATTRS),
            'discount_price': forms.NumberInput(attrs=WIDGET_ATTRS),
            'min_stock_alert': forms.NumberInput(attrs=WIDGET_ATTRS),
            'barcode': forms.TextInput(attrs=WIDGET_ATTRS),
            'notes': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields.pop('opening_stock')


class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ['product', 'quantity_delta', 'reason', 'reference_id', 'notes']
        widgets = {
            'product': forms.Select(attrs=SELECT_ATTRS),
            'quantity_delta': forms.NumberInput(attrs=WIDGET_ATTRS),
            'reason': forms.Select(attrs=SELECT_ATTRS),
            'reference_id': forms.TextInput(attrs=WIDGET_ATTRS),
            'notes': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 2}),
        }


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'order_number', 'customer', 'order_date', 'channel', 'payment_method',
            'payment_status', 'delivery_status', 'shipping_cost', 'notes',
        ]
        widgets = {
            'order_number': forms.TextInput(attrs={**WIDGET_ATTRS, 'placeholder': 'Auto-generated if left blank'}),
            'customer': forms.Select(attrs=SELECT_ATTRS),
            'order_date': forms.DateInput(attrs={**WIDGET_ATTRS, 'type': 'date'}),
            'channel': forms.Select(attrs=SELECT_ATTRS),
            'payment_method': forms.TextInput(attrs=WIDGET_ATTRS),
            'payment_status': forms.Select(attrs=SELECT_ATTRS),
            'delivery_status': forms.Select(attrs=SELECT_ATTRS),
            'shipping_cost': forms.NumberInput(attrs=WIDGET_ATTRS),
            'notes': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order_number'].required = False


OrderItemFormSet = inlineformset_factory(
    Order, OrderItem,
    fields=['product', 'quantity', 'unit_price'],
    extra=1, can_delete=True,
    widgets={
        'product': forms.Select(attrs=SELECT_ATTRS),
        'quantity': forms.NumberInput(attrs=WIDGET_ATTRS),
        'unit_price': forms.NumberInput(attrs=WIDGET_ATTRS),
    },
)


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['supplier', 'purchase_date', 'payment_status', 'notes']
        widgets = {
            'supplier': forms.Select(attrs=SELECT_ATTRS),
            'purchase_date': forms.DateInput(attrs={**WIDGET_ATTRS, 'type': 'date'}),
            'payment_status': forms.Select(attrs=SELECT_ATTRS),
            'notes': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 2}),
        }


PurchaseItemFormSet = inlineformset_factory(
    Purchase, PurchaseItem,
    fields=['product', 'quantity', 'cost_per_unit'],
    extra=1, can_delete=True,
    widgets={
        'product': forms.Select(attrs=SELECT_ATTRS),
        'quantity': forms.NumberInput(attrs=WIDGET_ATTRS),
        'cost_per_unit': forms.NumberInput(attrs=WIDGET_ATTRS),
    },
)


class ReturnForm(forms.ModelForm):
    class Meta:
        model = Return
        fields = ['product', 'order', 'return_date', 'quantity', 'reason', 'restock', 'refund_amount']
        widgets = {
            'product': forms.Select(attrs=SELECT_ATTRS),
            'order': forms.Select(attrs=SELECT_ATTRS),
            'return_date': forms.DateInput(attrs={**WIDGET_ATTRS, 'type': 'date'}),
            'quantity': forms.NumberInput(attrs=WIDGET_ATTRS),
            'reason': forms.TextInput(attrs=WIDGET_ATTRS),
            'restock': forms.CheckboxInput(attrs=CHECK_ATTRS),
            'refund_amount': forms.NumberInput(attrs=WIDGET_ATTRS),
        }


class DamagedLossForm(forms.ModelForm):
    class Meta:
        model = DamagedLoss
        fields = ['product', 'date', 'quantity', 'reason', 'cost_value']
        widgets = {
            'product': forms.Select(attrs=SELECT_ATTRS),
            'date': forms.DateInput(attrs={**WIDGET_ATTRS, 'type': 'date'}),
            'quantity': forms.NumberInput(attrs=WIDGET_ATTRS),
            'reason': forms.TextInput(attrs=WIDGET_ATTRS),
            'cost_value': forms.NumberInput(attrs=WIDGET_ATTRS),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['date', 'category', 'description', 'amount']
        widgets = {
            'date': forms.DateInput(attrs={**WIDGET_ATTRS, 'type': 'date'}),
            'category': forms.TextInput(attrs=WIDGET_ATTRS),
            'description': forms.TextInput(attrs=WIDGET_ATTRS),
            'amount': forms.NumberInput(attrs=WIDGET_ATTRS),
        }


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            'code', 'discount_type', 'discount_value', 'min_order_value',
            'start_date', 'end_date', 'active', 'description',
        ]
        widgets = {
            'code': forms.TextInput(attrs=WIDGET_ATTRS),
            'discount_type': forms.Select(attrs=SELECT_ATTRS),
            'discount_value': forms.NumberInput(attrs=WIDGET_ATTRS),
            'min_order_value': forms.NumberInput(attrs=WIDGET_ATTRS),
            'start_date': forms.DateInput(attrs={**WIDGET_ATTRS, 'type': 'date'}),
            'end_date': forms.DateInput(attrs={**WIDGET_ATTRS, 'type': 'date'}),
            'active': forms.CheckboxInput(attrs=CHECK_ATTRS),
            'description': forms.TextInput(attrs=WIDGET_ATTRS),
        }


class SpecialOrderForm(forms.ModelForm):
    class Meta:
        model = SpecialOrder
        fields = [
            'customer_name', 'phone', 'item_requested', 'shade_color', 'quantity',
            'agreed_price', 'deposit_paid', 'status', 'date_requested', 'notes',
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs=WIDGET_ATTRS),
            'phone': forms.TextInput(attrs=WIDGET_ATTRS),
            'item_requested': forms.TextInput(attrs=WIDGET_ATTRS),
            'shade_color': forms.TextInput(attrs=WIDGET_ATTRS),
            'quantity': forms.NumberInput(attrs=WIDGET_ATTRS),
            'agreed_price': forms.NumberInput(attrs=WIDGET_ATTRS),
            'deposit_paid': forms.NumberInput(attrs=WIDGET_ATTRS),
            'status': forms.Select(attrs=SELECT_ATTRS),
            'date_requested': forms.DateInput(attrs={**WIDGET_ATTRS, 'type': 'date'}),
            'notes': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 2}),
        }
