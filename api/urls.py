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
    OrderListView,
    RemoveCartView,
    MyProfileView,
    OrderDetailView,
    ProductListAllView,
    AllOrdersAdminView,
    AllUserProfilesAdminView,
    UpdateOrderInfoView,
    AdminOrderDetailView
)

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register('users',UserView)

urlpatterns = [
    path('products/all/', ProductListAllView.as_view(), name='product-list-all'),
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
    path('cart/remove/',RemoveCartView.as_view(),name='remove-cart'),
    path('profile/',MyProfileView.as_view(),name='my-profile'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('admin/orders/', AllOrdersAdminView.as_view(), name='all-orders-admin'),
    path('admin/userprofiles/', AllUserProfilesAdminView.as_view(), name='all-userprofiles-admin'),
    path('orders/<int:order_id>/update-info',UpdateOrderInfoView.as_view(),name ='update-order-info'),
    path('admin/orders/<int:pk>/', AdminOrderDetailView.as_view(), name='admin-order-detail'),

    
]   
