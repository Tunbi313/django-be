from django.urls import path, include
from apps.orders.views import VNPayReturnView

urlpatterns = [
    path('users/', include('apps.users.urls')),
    path('products/', include('apps.products.urls')),
    path('cart/', include('apps.cart.urls')),
    path('orders/', include('apps.orders.urls')),
    path('vnpay/return/', VNPayReturnView.as_view(), name='vnpay-return'),
] 