from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import F, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, UpdateView

from .forms import (
    CouponForm,
    CustomerForm,
    DamagedLossForm,
    ExpenseForm,
    OrderForm,
    OrderItemFormSet,
    ProductForm,
    PurchaseForm,
    PurchaseItemFormSet,
    ReturnForm,
    SpecialOrderForm,
    StockMovementForm,
    SupplierForm,
)
from .models import (
    Account,
    Coupon,
    Customer,
    DamagedLoss,
    Expense,
    JournalEntry,
    Order,
    OrderItem,
    Product,
    Purchase,
    Return,
    SpecialOrder,
    StockMovement,
    Supplier,
)


@login_required
def dashboard(request):
    today = date.today()
    month_start = today.replace(day=1)

    revenue_this_month = OrderItem.objects.filter(
        order__order_date__gte=month_start
    ).aggregate(total=Sum(F('unit_price') * F('quantity')))['total'] or 0

    expenses_this_month = Expense.objects.filter(date__gte=month_start).aggregate(
        total=Sum('amount')
    )['total'] or 0

    context = {
        'product_count': Product.objects.count(),
        'low_stock_count': Product.objects.filter(stock_quantity__lte=F('min_stock_alert')).count(),
        'pending_orders': Order.objects.filter(delivery_status=Order.DeliveryStatus.PENDING).count(),
        'customer_count': Customer.objects.count(),
        'supplier_count': Supplier.objects.count(),
        'revenue_this_month': revenue_this_month,
        'expenses_this_month': expenses_this_month,
        'special_orders_open': SpecialOrder.objects.exclude(status=SpecialOrder.Status.GIVEN).count(),
    }
    return render(request, 'inventory/dashboard.html', context)


# ---------------------------------------------------------------------------
# Generic CRUD base classes
# ---------------------------------------------------------------------------

class CrudCreateView(LoginRequiredMixin, CreateView):
    template_name = 'inventory/generic_form.html'

    def form_valid(self, form):
        messages.success(self.request, f'{self.object_label} created successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'New {self.object_label}'
        return ctx


class CrudUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'inventory/generic_form.html'

    def form_valid(self, form):
        messages.success(self.request, f'{self.object_label} updated successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Edit {self.object_label}'
        return ctx


class CrudDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'inventory/generic_confirm_delete.html'

    def form_valid(self, form):
        messages.success(self.request, f'{self.object_label} deleted.')
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------

@login_required
def product_list(request):
    return render(request, 'inventory/product_list.html', {'products': Product.objects.select_related('supplier')})


class ProductCreateView(CrudCreateView):
    model = Product
    form_class = ProductForm
    object_label = 'Product'
    success_url = reverse_lazy('inventory:product_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        opening_stock = form.cleaned_data.get('opening_stock') or 0
        if opening_stock:
            StockMovement.objects.create(
                product=self.object,
                quantity_delta=opening_stock,
                reason=StockMovement.Reason.ADJUSTMENT,
                reference_id='opening-stock',
                notes='Opening stock set on product creation',
            )
        return response


class ProductUpdateView(CrudUpdateView):
    model = Product
    form_class = ProductForm
    object_label = 'Product'
    success_url = reverse_lazy('inventory:product_list')


class ProductDeleteView(CrudDeleteView):
    model = Product
    object_label = 'Product'
    success_url = reverse_lazy('inventory:product_list')


# ---------------------------------------------------------------------------
# Supplier
# ---------------------------------------------------------------------------

@login_required
def supplier_list(request):
    return render(request, 'inventory/supplier_list.html', {'suppliers': Supplier.objects.all()})


class SupplierCreateView(CrudCreateView):
    model = Supplier
    form_class = SupplierForm
    object_label = 'Supplier'
    success_url = reverse_lazy('inventory:supplier_list')


class SupplierUpdateView(CrudUpdateView):
    model = Supplier
    form_class = SupplierForm
    object_label = 'Supplier'
    success_url = reverse_lazy('inventory:supplier_list')


class SupplierDeleteView(CrudDeleteView):
    model = Supplier
    object_label = 'Supplier'
    success_url = reverse_lazy('inventory:supplier_list')


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------

@login_required
def customer_list(request):
    return render(request, 'inventory/customer_list.html', {'customers': Customer.objects.all()})


class CustomerCreateView(CrudCreateView):
    model = Customer
    form_class = CustomerForm
    object_label = 'Customer'
    success_url = reverse_lazy('inventory:customer_list')


class CustomerUpdateView(CrudUpdateView):
    model = Customer
    form_class = CustomerForm
    object_label = 'Customer'
    success_url = reverse_lazy('inventory:customer_list')


class CustomerDeleteView(CrudDeleteView):
    model = Customer
    object_label = 'Customer'
    success_url = reverse_lazy('inventory:customer_list')


# ---------------------------------------------------------------------------
# Stock Movements (manual adjustments)
# ---------------------------------------------------------------------------

@login_required
def stock_movement_list(request):
    return render(
        request,
        'inventory/stock_movement_list.html',
        {'movements': StockMovement.objects.select_related('product').order_by('-created_at')[:200]},
    )


class StockMovementCreateView(CrudCreateView):
    model = StockMovement
    form_class = StockMovementForm
    object_label = 'Stock Movement'
    success_url = reverse_lazy('inventory:stock_movement_list')


# ---------------------------------------------------------------------------
# Orders (with inline OrderItem formset)
# ---------------------------------------------------------------------------

@login_required
def order_list(request):
    return render(request, 'inventory/order_list.html', {'orders': Order.objects.select_related('customer')})


def _next_order_number():
    last = Order.objects.order_by('-id').first()
    next_id = (last.id + 1) if last else 1
    return f'ORD-{next_id:04d}'


@login_required
def order_create(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        formset = OrderItemFormSet(request.POST, instance=Order())
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                if not order.order_number:
                    order.order_number = _next_order_number()
                order.save()
                formset.instance = order
                formset.save()
            messages.success(request, f'Order {order.order_number} created successfully.')
            return redirect('inventory:order_list')
    else:
        form = OrderForm()
        formset = OrderItemFormSet(instance=Order())
    return render(request, 'inventory/order_form.html', {'form': form, 'formset': formset, 'title': 'New Order'})


@login_required
def order_edit(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        formset = OrderItemFormSet(request.POST, instance=order)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
            messages.success(request, f'Order {order.order_number} updated successfully.')
            return redirect('inventory:order_list')
    else:
        form = OrderForm(instance=order)
        formset = OrderItemFormSet(instance=order)
    return render(
        request, 'inventory/order_form.html',
        {'form': form, 'formset': formset, 'title': f'Edit Order {order.order_number}'},
    )


@login_required
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.delete()
        messages.success(request, 'Order deleted.')
        return redirect('inventory:order_list')
    return render(request, 'inventory/generic_confirm_delete.html', {'object': order})


# ---------------------------------------------------------------------------
# Purchases (with inline PurchaseItem formset)
# ---------------------------------------------------------------------------

@login_required
def purchase_list(request):
    return render(request, 'inventory/purchase_list.html', {'purchases': Purchase.objects.select_related('supplier')})


@login_required
def purchase_create(request):
    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        formset = PurchaseItemFormSet(request.POST, instance=Purchase())
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                purchase = form.save()
                formset.instance = purchase
                formset.save()
            messages.success(request, 'Purchase recorded successfully.')
            return redirect('inventory:purchase_list')
    else:
        form = PurchaseForm()
        formset = PurchaseItemFormSet(instance=Purchase())
    return render(
        request, 'inventory/purchase_form.html',
        {'form': form, 'formset': formset, 'title': 'New Purchase'},
    )


@login_required
def purchase_edit(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    if request.method == 'POST':
        form = PurchaseForm(request.POST, instance=purchase)
        formset = PurchaseItemFormSet(request.POST, instance=purchase)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
            messages.success(request, 'Purchase updated successfully.')
            return redirect('inventory:purchase_list')
    else:
        form = PurchaseForm(instance=purchase)
        formset = PurchaseItemFormSet(instance=purchase)
    return render(
        request, 'inventory/purchase_form.html',
        {'form': form, 'formset': formset, 'title': f'Edit Purchase #{purchase.pk}'},
    )


@login_required
def purchase_delete(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    if request.method == 'POST':
        purchase.delete()
        messages.success(request, 'Purchase deleted.')
        return redirect('inventory:purchase_list')
    return render(request, 'inventory/generic_confirm_delete.html', {'object': purchase})


# ---------------------------------------------------------------------------
# Returns
# ---------------------------------------------------------------------------

@login_required
def return_list(request):
    return render(request, 'inventory/return_list.html', {'returns': Return.objects.select_related('product')})


class ReturnCreateView(CrudCreateView):
    model = Return
    form_class = ReturnForm
    object_label = 'Return'
    success_url = reverse_lazy('inventory:return_list')


class ReturnUpdateView(CrudUpdateView):
    model = Return
    form_class = ReturnForm
    object_label = 'Return'
    success_url = reverse_lazy('inventory:return_list')


class ReturnDeleteView(CrudDeleteView):
    model = Return
    object_label = 'Return'
    success_url = reverse_lazy('inventory:return_list')


# ---------------------------------------------------------------------------
# Damaged / Lost
# ---------------------------------------------------------------------------

@login_required
def damaged_loss_list(request):
    return render(
        request, 'inventory/damaged_loss_list.html', {'losses': DamagedLoss.objects.select_related('product')}
    )


class DamagedLossCreateView(CrudCreateView):
    model = DamagedLoss
    form_class = DamagedLossForm
    object_label = 'Damaged/Lost record'
    success_url = reverse_lazy('inventory:damaged_loss_list')


class DamagedLossUpdateView(CrudUpdateView):
    model = DamagedLoss
    form_class = DamagedLossForm
    object_label = 'Damaged/Lost record'
    success_url = reverse_lazy('inventory:damaged_loss_list')


class DamagedLossDeleteView(CrudDeleteView):
    model = DamagedLoss
    object_label = 'Damaged/Lost record'
    success_url = reverse_lazy('inventory:damaged_loss_list')


# ---------------------------------------------------------------------------
# Special Orders
# ---------------------------------------------------------------------------

@login_required
def special_order_list(request):
    return render(request, 'inventory/special_order_list.html', {'special_orders': SpecialOrder.objects.all()})


class SpecialOrderCreateView(CrudCreateView):
    model = SpecialOrder
    form_class = SpecialOrderForm
    object_label = 'Special Order'
    success_url = reverse_lazy('inventory:special_order_list')


class SpecialOrderUpdateView(CrudUpdateView):
    model = SpecialOrder
    form_class = SpecialOrderForm
    object_label = 'Special Order'
    success_url = reverse_lazy('inventory:special_order_list')


class SpecialOrderDeleteView(CrudDeleteView):
    model = SpecialOrder
    object_label = 'Special Order'
    success_url = reverse_lazy('inventory:special_order_list')


# ---------------------------------------------------------------------------
# Coupons
# ---------------------------------------------------------------------------

@login_required
def coupon_list(request):
    return render(request, 'inventory/coupon_list.html', {'coupons': Coupon.objects.all()})


class CouponCreateView(CrudCreateView):
    model = Coupon
    form_class = CouponForm
    object_label = 'Coupon'
    success_url = reverse_lazy('inventory:coupon_list')


class CouponUpdateView(CrudUpdateView):
    model = Coupon
    form_class = CouponForm
    object_label = 'Coupon'
    success_url = reverse_lazy('inventory:coupon_list')


class CouponDeleteView(CrudDeleteView):
    model = Coupon
    object_label = 'Coupon'
    success_url = reverse_lazy('inventory:coupon_list')


# ---------------------------------------------------------------------------
# Expenses
# ---------------------------------------------------------------------------

@login_required
def expense_list(request):
    return render(request, 'inventory/expense_list.html', {'expenses': Expense.objects.order_by('-date')})


class ExpenseCreateView(CrudCreateView):
    model = Expense
    form_class = ExpenseForm
    object_label = 'Expense'
    success_url = reverse_lazy('inventory:expense_list')


class ExpenseUpdateView(CrudUpdateView):
    model = Expense
    form_class = ExpenseForm
    object_label = 'Expense'
    success_url = reverse_lazy('inventory:expense_list')


class ExpenseDeleteView(CrudDeleteView):
    model = Expense
    object_label = 'Expense'
    success_url = reverse_lazy('inventory:expense_list')


# ---------------------------------------------------------------------------
# Accounting
# ---------------------------------------------------------------------------

@login_required
def chart_of_accounts(request):
    accounts = Account.objects.all()
    return render(request, 'inventory/chart_of_accounts.html', {'accounts': accounts})


@login_required
def account_ledger(request, pk):
    account = get_object_or_404(Account, pk=pk)
    lines = account.lines.select_related('entry').order_by('entry__date', 'entry__id')
    running_balance = 0
    rows = []
    for line in lines:
        if account.type in (Account.Type.ASSET, Account.Type.EXPENSE):
            running_balance += line.debit - line.credit
        else:
            running_balance += line.credit - line.debit
        rows.append({'line': line, 'balance': running_balance})
    return render(request, 'inventory/account_ledger.html', {'account': account, 'rows': rows})


@login_required
def journal_entry_list(request):
    entries = JournalEntry.objects.prefetch_related('lines__account').order_by('-date', '-id')[:300]
    return render(request, 'inventory/journal_entry_list.html', {'entries': entries})


@login_required
def trial_balance(request):
    accounts = Account.objects.all()
    rows = []
    total_debit = Decimal('0')
    total_credit = Decimal('0')
    for account in accounts:
        totals = account.lines.aggregate(debit=Sum('debit'), credit=Sum('credit'))
        debit = totals['debit'] or Decimal('0')
        credit = totals['credit'] or Decimal('0')
        if debit == 0 and credit == 0:
            continue
        rows.append({'account': account, 'debit': debit, 'credit': credit})
        total_debit += debit
        total_credit += credit
    return render(
        request, 'inventory/trial_balance.html',
        {'rows': rows, 'total_debit': total_debit, 'total_credit': total_credit},
    )


@login_required
def profit_and_loss(request):
    income_accounts = Account.objects.filter(type=Account.Type.INCOME)
    expense_accounts = Account.objects.filter(type=Account.Type.EXPENSE)

    income_rows = [{'account': a, 'amount': a.balance} for a in income_accounts]
    expense_rows = [{'account': a, 'amount': a.balance} for a in expense_accounts]

    total_income = sum((r['amount'] for r in income_rows), Decimal('0'))
    total_expense = sum((r['amount'] for r in expense_rows), Decimal('0'))
    net_profit = total_income - total_expense

    return render(
        request, 'inventory/profit_and_loss.html',
        {
            'income_rows': income_rows, 'expense_rows': expense_rows,
            'total_income': total_income, 'total_expense': total_expense, 'net_profit': net_profit,
        },
    )


@login_required
def balance_sheet(request):
    asset_accounts = Account.objects.filter(type=Account.Type.ASSET)
    liability_accounts = Account.objects.filter(type=Account.Type.LIABILITY)
    equity_accounts = Account.objects.filter(type=Account.Type.EQUITY)

    asset_rows = [{'account': a, 'amount': a.balance} for a in asset_accounts]
    liability_rows = [{'account': a, 'amount': a.balance} for a in liability_accounts]
    equity_rows = [{'account': a, 'amount': a.balance} for a in equity_accounts]

    total_assets = sum((r['amount'] for r in asset_rows), Decimal('0'))
    total_liabilities = sum((r['amount'] for r in liability_rows), Decimal('0'))

    # Retained earnings = net profit not yet posted to equity (Income - Expenses to date)
    retained_earnings = (
        sum((a.balance for a in Account.objects.filter(type=Account.Type.INCOME)), Decimal('0'))
        - sum((a.balance for a in Account.objects.filter(type=Account.Type.EXPENSE)), Decimal('0'))
    )
    total_equity = sum((r['amount'] for r in equity_rows), Decimal('0')) + retained_earnings

    return render(
        request, 'inventory/balance_sheet.html',
        {
            'asset_rows': asset_rows, 'liability_rows': liability_rows, 'equity_rows': equity_rows,
            'total_assets': total_assets, 'total_liabilities': total_liabilities,
            'retained_earnings': retained_earnings, 'total_equity': total_equity,
            'balanced': total_assets == (total_liabilities + total_equity),
        },
    )
