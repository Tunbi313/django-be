from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', read_only=True, max_digits=10, decimal_places=2)
    product_image = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_price', 'quantity', 'price', 'product_image']

    def get_product_image(self, obj):
        image = obj.product.image
        request = self.context.get('request')
        if not image:
            return None

        # Nếu là ImageField (có thuộc tính url)
        if hasattr(image, 'url'):
            if request is not None:
                return request.build_absolute_uri(image.url)
            return image.url

        # Nếu là string (CharField hoặc URL)
        image_str = str(image)
        if image_str.startswith('http'):
            return image_str
        if request is not None:
            return request.build_absolute_uri(image_str)
        return image_str


class OrderSerializer(serializers.ModelSerializer):
    user_profile = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'status', 'total_price', 'created_at', 'receiver_name', 'address', 'phone', 'email', 'user_profile', 'items']

    def get_user_profile(self, obj):
        try:
            profile = obj.user.profile
            return {
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "address": profile.address,
                "phone": profile.phone,
                "email": profile.email,
                "image": profile.image
            }
        except:
            return None

    def get_items(self, obj):
        return OrderItemSerializer(obj.items.all(), many=True, context=self.context).data


class OrderUpdateInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['receiver_name', 'address', 'phone', 'email'] 