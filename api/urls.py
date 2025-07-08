from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet,
    RegisterView,
    LoginView,
    LogoutView,
    CreateAdminView,
    UserView,
    CartView,
    AddToCartView,
    UpdateCartItemView,
    RemoveCartItemView,
    CheckoutView,
    PayOrderView,
    OrderListView
)

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register('users',UserView)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('create-admin/', CreateAdminView.as_view(), name='create-admin'),
    path('cart/', CartView.as_view(), name='view-cart'),
    path('cart/add/', AddToCartView.as_view(), name='add-to-cart'),
    path('cart/item/<int:item_id>/update/', UpdateCartItemView.as_view(), name='update-cart-item'),
    path('cart/item/<int:item_id>/remove/', RemoveCartItemView.as_view(), name='remove-cart-item'),
    path('orders/checkout/', CheckoutView.as_view(), name='checkout'),
    path('orders/<int:order_id>/pay/', PayOrderView.as_view(), name='pay-order'),
    path('orders/', OrderListView.as_view(), name='order-list'),
]   
