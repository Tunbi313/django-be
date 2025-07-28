from rest_framework import serializers
from apps.saleproduct.models import SaleProduct

class SaleProductSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    original_price = serializers.DecimalField(source='product.price', read_only=True, max_digits=10, decimal_places=2)
    discounted_price = serializers.SerializerMethodField()

    class Meta:
        model = SaleProduct
        fields = ['id', 'product', 'product_name', 'original_price', 'discount_percent', 'start_date', 'end_date', 'discounted_price']

    def get_discounted_price(self, obj):
        return obj.discounted_price()  