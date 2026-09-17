from django.urls import path

from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # Products
    path('products/', views.product_list, name='product_list'),
    path('products/new/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),

    # Orders
    path('orders/', views.order_list, name='order_list'),
    path('orders/new/', views.order_create, name='order_create'),
    path('orders/<int:pk>/edit/', views.order_edit, name='order_edit'),
    path('orders/<int:pk>/delete/', views.order_delete, name='order_delete'),

    # Purchases
    path('purchases/', views.purchase_list, name='purchase_list'),
    path('purchases/new/', views.purchase_create, name='purchase_create'),
    path('purchases/<int:pk>/edit/', views.purchase_edit, name='purchase_edit'),
    path('purchases/<int:pk>/delete/', views.purchase_delete, name='purchase_delete'),

    # Customers
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/new/', views.CustomerCreateView.as_view(), name='customer_create'),
    path('customers/<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='customer_edit'),
    path('customers/<int:pk>/delete/', views.CustomerDeleteView.as_view(), name='customer_delete'),

    # Suppliers
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/new/', views.SupplierCreateView.as_view(), name='supplier_create'),
    path('suppliers/<int:pk>/edit/', views.SupplierUpdateView.as_view(), name='supplier_edit'),
    path('suppliers/<int:pk>/delete/', views.SupplierDeleteView.as_view(), name='supplier_delete'),

    # Expenses
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/new/', views.ExpenseCreateView.as_view(), name='expense_create'),
    path('expenses/<int:pk>/edit/', views.ExpenseUpdateView.as_view(), name='expense_edit'),
    path('expenses/<int:pk>/delete/', views.ExpenseDeleteView.as_view(), name='expense_delete'),

    # Stock Movements
    path('stock-movements/', views.stock_movement_list, name='stock_movement_list'),
    path('stock-movements/new/', views.StockMovementCreateView.as_view(), name='stock_movement_create'),

    # Returns
    path('returns/', views.return_list, name='return_list'),
    path('returns/new/', views.ReturnCreateView.as_view(), name='return_create'),
    path('returns/<int:pk>/edit/', views.ReturnUpdateView.as_view(), name='return_edit'),
    path('returns/<int:pk>/delete/', views.ReturnDeleteView.as_view(), name='return_delete'),

    # Damaged / Lost
    path('damaged-loss/', views.damaged_loss_list, name='damaged_loss_list'),
    path('damaged-loss/new/', views.DamagedLossCreateView.as_view(), name='damaged_loss_create'),
    path('damaged-loss/<int:pk>/edit/', views.DamagedLossUpdateView.as_view(), name='damaged_loss_edit'),
    path('damaged-loss/<int:pk>/delete/', views.DamagedLossDeleteView.as_view(), name='damaged_loss_delete'),

    # Special Orders
    path('special-orders/', views.special_order_list, name='special_order_list'),
    path('special-orders/new/', views.SpecialOrderCreateView.as_view(), name='special_order_create'),
    path('special-orders/<int:pk>/edit/', views.SpecialOrderUpdateView.as_view(), name='special_order_edit'),
    path('special-orders/<int:pk>/delete/', views.SpecialOrderDeleteView.as_view(), name='special_order_delete'),

    # Coupons
    path('coupons/', views.coupon_list, name='coupon_list'),
    path('coupons/new/', views.CouponCreateView.as_view(), name='coupon_create'),
    path('coupons/<int:pk>/edit/', views.CouponUpdateView.as_view(), name='coupon_edit'),
    path('coupons/<int:pk>/delete/', views.CouponDeleteView.as_view(), name='coupon_delete'),

    # Accounting
    path('accounting/chart-of-accounts/', views.chart_of_accounts, name='chart_of_accounts'),
    path('accounting/accounts/<int:pk>/', views.account_ledger, name='account_ledger'),
    path('accounting/journal/', views.journal_entry_list, name='journal_entry_list'),
    path('accounting/trial-balance/', views.trial_balance, name='trial_balance'),
    path('accounting/profit-and-loss/', views.profit_and_loss, name='profit_and_loss'),
    path('accounting/balance-sheet/', views.balance_sheet, name='balance_sheet'),
]
