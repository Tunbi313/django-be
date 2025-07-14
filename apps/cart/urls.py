from django.urls import path
from .views import CartView, AddToCartView, UpdateCartItemView, RemoveCartItemView, RemoveCartView

app_name = 'cart'

urlpatterns = [
    path('', CartView.as_view(), name='view-cart'),
    path('add/', AddToCartView.as_view(), name='add-to-cart'),
    path('item/<int:item_id>/update/', UpdateCartItemView.as_view(), name='update-cart-item'),
    path('item/<int:item_id>/remove/', RemoveCartItemView.as_view(), name='remove-cart-item'),
    path('remove/', RemoveCartView.as_view(), name='remove-cart'),
] 