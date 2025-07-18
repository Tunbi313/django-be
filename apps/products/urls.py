from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, ProductListAllView, ProductsByCategoryView,RelatedProductsView

router = DefaultRouter()
router.register(r'categories',CategoryViewSet,basename='category')
router.register('', ProductViewSet, basename='product')


app_name = 'products'

urlpatterns = [
    path('all/', ProductListAllView.as_view(), name='product-list-all'),
    path('categories/<int:category_id>/products/', ProductsByCategoryView.as_view(), name='products-by-category'),
     path('<int:product_id>/related/', RelatedProductsView.as_view(), name='related-products'),
    path('', include(router.urls)),
   
] 