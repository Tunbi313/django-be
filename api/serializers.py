from rest_framework import serializers
from .models import Product,Order,OrderItem,User,CartItem,Cart,UserProfile
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken


#UserProfile
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['first_name','last_name','address','phone','email','image','user_id']

#customer
class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['id','username','email']
    
#cartitem
class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', read_only=True, max_digits=10, decimal_places=2)
    product_image = serializers.CharField(source='product.image', read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_name', 'product_price', 'product_image', 'quantity']

#cart
class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'created_at']
        read_only_fields = ['user']


#product
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields =['id', 'name', 'description', 'price', 'image', 'quantity']

#orderitem
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', read_only=True, max_digits=10, decimal_places=2)
    product_image = serializers.SerializerMethodField()
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_price', 'quantity', 'price','product_image']

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

#order
class OrderSerializer(serializers.ModelSerializer):
    user_profile = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'status', 'total_price', 'created_at',
            'receiver_name', 'address', 'phone', 'email',  # Thông tin riêng của order
            'user_profile',  # Thông tin profile gốc của user
            'items'
        ]

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

#order update

class OrderUpdateInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['receiver_name','address','phone','email']