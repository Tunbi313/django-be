from rest_framework import serializers
from .models import Product,Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','name','description']



class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only = True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset = Category.objects.all(),
        source = 'category',
        write_only = True,
        required = False
    )
    current_price = serializers.SerializerMethodField()
    discount_percent = serializers.SerializerMethodField()
    original_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'current_price', 'original_price', 'discount_percent', 'image', 'quantity','category','category_id','created_at','status']
    
    def get_current_price(self, obj):
        """Giá hiện tại (có tính sale)"""
        return obj.get_current_price()
    
    def get_original_price(self, obj):
        """Giá gốc (không có sale)"""
        return obj.price
    
    def get_discount_percent(self, obj):
        """Phần trăm giảm giá"""
        return obj.get_discount_percent() 


