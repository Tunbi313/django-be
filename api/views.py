from rest_framework import generics,viewsets,permissions,status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from .models import Product,Order,OrderItem,CartItem,Cart,UserProfile
from django.contrib.auth.models import User
from .serializers import (ProductSerializer,OrderSerializer,OrderItemSerializer,UserSerializer,CartItemSerializer,CartSerializer,UserProfileSerializer,OrderUpdateInfoSerializer)
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny,IsAdminUser
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authtoken.models import Token
from .permissions import IsAdminOrReadOnly,IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.generics import ListAPIView,RetrieveAPIView,RetrieveUpdateDestroyAPIView
#user
class UserView(viewsets.ModelViewSet):
        queryset = User.objects.all()
        serializer_class =UserSerializer



#register view
class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        if not username or not password:
            return Response({'error': 'Vui lòng nhập username và password'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username đã tồn tại'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email).exists():
            return Response({'error':'email da ton tai'},status=status.HTTP_400_BAD_REQUEST)
        user = User(username=username,email=email)
        user.set_password(password)
        user.save()
        return Response({'message': 'Đăng ký thành công'}, status=status.HTTP_201_CREATED)

#api login
class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({"error": "Vui lòng nhập username và password"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            return Response({"error": "Username không tồn tại"}, status=status.HTTP_400_BAD_REQUEST)
        
        if user.check_password(password):
            # Tạo hoặc lấy token cho user
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                "message": "Đăng nhập thành công",
                "token": token.key,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_admin": user.is_staff
                }
            }, status=status.HTTP_200_OK)
        
        return Response({"error": "Mật khẩu không đúng"}, status=status.HTTP_400_BAD_REQUEST)


#api logout
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Xóa token của user hiện tại
            request.user.auth_token.delete()
            return Response({"message": "Đăng xuất thành công"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Có lỗi xảy ra khi đăng xuất"}, status=status.HTTP_400_BAD_REQUEST)


# Tạo admin user (chỉ dùng để test)
class CreateAdminView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        
        if not username or not password:
            return Response({'error': 'Vui lòng nhập username và password'}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username đã tồn tại'}, status=status.HTTP_400_BAD_REQUEST)
        
        if email and User.objects.filter(email=email).exists():
            return Response({'error': 'Email đã tồn tại'}, status=status.HTTP_400_BAD_REQUEST)

        user = User(username=username, email=email, is_staff=True, is_superuser=True)
        user.set_password(password)
        user.save()
        
        # Tạo token cho admin
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'message': 'Tạo admin thành công',
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_staff': user.is_staff
            }
        }, status=status.HTTP_201_CREATED)

#put,get userprofile
class MyProfileView(APIView) :
    permission_classes = [IsAuthenticated]

    def post(self,request):
        if hasattr(request.user, 'profile'):
            return Response({'detail': 'Profile đã tồn tại. Dùng PUT để cập nhật.'}, status=400)

        serializer = UserProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def get(self,request):
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    
    def put(self,request):
        profile,_ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


#CRUD Prodcut

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    
#getcartview
class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
#add to cart

class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get("product_id")
        raw_quantity = request.data.get("quantity", 1)

        #ép kiểu và check quantity
        try:
            quantity = int(raw_quantity)
            if quantity <1:
                raise ValueError
        
        except(ValueError,TypeError):
            return Response ({"error":"quantity >= 1"},status=400)

          # Kiểm tra product_id và quantity có hợp lệ không
        if not product_id:
            return Response({"error": "Thiếu product_id"}, status=status.HTTP_400_BAD_REQUEST)

        # Lấy product
        product = get_object_or_404(Product, id=product_id)

        # Kiểm tra tồn kho
        if quantity > product.quantity:
            return Response({"error": f"Số lượng vượt quá tồn kho ({product.quantity})"}, status=status.HTTP_400_BAD_REQUEST)

        # Tạo hoặc lấy Cart cho user
        cart, _ = Cart.objects.get_or_create(user=request.user)

        # Kiểm tra nếu sản phẩm đã có trong giỏ hàng
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        if not created:
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product.quantity:
                return Response({"error": f"Tổng số lượng vượt quá tồn kho ({product.quantity})"}, status=status.HTTP_400_BAD_REQUEST)
            cart_item.quantity = new_quantity
        else:
            cart_item.quantity = quantity

        # Lưu cart_item sau khi full_clean để kiểm tra logic
        try:
            cart_item.full_clean()
            cart_item.save()
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Đã thêm vào giỏ hàng"}, status=status.HTTP_200_OK)

#updatecartitem 
class UpdateCartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        quantity = int(request.data.get("quantity", 1))
        cart_item.quantity = quantity

        try:
            cart_item.full_clean()
            cart_item.save()
            return Response({"message": "Cập nhật thành công"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

#removecartitem
class RemoveCartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
        return Response({"message": "Đã xóa khỏi giỏ hàng"}, status=status.HTTP_200_OK)
    
#removecart
class RemoveCartView(APIView):
    permission_classes =[IsAuthenticated]

    def delete(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        cart.delete()
        return Response({"message": "Đã xóa giỏ hàng thành công"}, status=status.HTTP_200_OK)
        



#checkout
class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic()
    def post(self, request):
        user = request.user
        cart = Cart.objects.get(user=user)
        cart_items = cart.items.all()

        if not cart_items.exists():
            return Response({"error": "Giỏ hàng của bạn đang trống."}, status=400)

        #Lấy thông tin từ UserProfile
        try:
            profile = user.profile
        except:
            return Response({"error":"Người dùng chưa có thông tin"})



        # Kiểm tra đã có order pending chưa
        pending_order = Order.objects.filter(user=user, status='pending').first()
        if pending_order:
            # Gán lại thông tin người nhận từ profile
            pending_order.receiver_name = f"{profile.first_name} {profile.last_name}"
            pending_order.address = profile.address
            pending_order.phone = profile.phone
            pending_order.email = profile.email

            # Xóa hết OrderItem cũ
            pending_order.items.all().delete()
            # Thêm lại sản phẩm từ cart
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=pending_order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price
                )
            pending_order.update_total_price()
            pending_order.save()
            serializer = OrderSerializer(pending_order)
            return Response({
                "message": "Đã cập nhật đơn hàng đang chờ thanh toán.",
                "order": serializer.data
            }, status=200)

        # Nếu chưa có order pending, tạo mới như cũ
        order = Order.objects.create(user=user, status='pending', total_price=0)
        order.receiver_name = f"{profile.first_name} {profile.last_name}"
        order.address = profile.address
        order.phone = profile.phone
        order.email = profile.email    
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
        order.update_total_price()
        order.save()
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=201)
        
#pay oder
class PayOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        user = request.user
        order = get_object_or_404(Order, id=order_id, user=user)

        if order.status != 'pending':
            return Response({"error": "Đơn hàng đã thanh toán hoặc không hợp lệ"}, status=400)

        # Trừ tồn kho (nếu chưa trừ)
        for item in order.items.all():
            product = item.product
            if item.quantity > product.quantity:
                return Response({"error": f"Sản phẩm '{product.name}' đã hết hàng"}, status=400)
            product.quantity -= item.quantity
            product.save()

        order.status = 'paid'
        order.save()
        Cart.objects.filter(user=user).delete()

        return Response({"message": "Thanh toán thành công", "order_id": order.id,"status":order.status})

#oderlistview 

class OrderListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')
    

#orderDetailview
class OrderDetailView(RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Order.objects.all()  # Admin xem được tất cả
        return Order.objects.filter(user=user)  # User thường chỉ xem của mình
    
#all Products


class ProductListAllView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    
#all order
class AllOrdersAdminView(ListAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]  # Chỉ admin mới truy cập được
    pagination_class = None #tắt phân trang


#all userprofile
class AllUserProfilesAdminView(ListAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminUser]
    pagination_class = None  # Nếu muốn trả về toàn bộ, không phân trang


#update oder info

class UpdateOrderInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self,request,order_id):
        order = get_object_or_404(Order,id=order_id,user=request.user)

        if order.status != 'pending':
            return Response ({"error":"chỉ cập nhận đơn hàng khi chưa thanh toán"})

        serializer = OrderUpdateInfoSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"Cập nhật thông tin đơn hàng thành công"})
        return Response(serializer.errors,status=400)

# Admin RESTful order detail view
class AdminOrderDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]

