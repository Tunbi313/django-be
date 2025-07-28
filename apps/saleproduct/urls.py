from django.urls import path
from .views import ActiveSaleProductListAPIView
from .views import SaleProductCreateUpdateAPIView

app_name = 'saleproduct'

urlpatterns = [
    path('sale-products/', ActiveSaleProductListAPIView.as_view(), name='sale-product-list'),
    path('sale-products/manage/', SaleProductCreateUpdateAPIView.as_view(), name='sale-product-manage'),
]