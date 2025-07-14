from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, ProductListAllView

router = DefaultRouter()
router.register('', ProductViewSet, basename='product')

app_name = 'products'

urlpatterns = [
    path('', include(router.urls)),
    path('all/', ProductListAllView.as_view(), name='product-list-all'),
] 