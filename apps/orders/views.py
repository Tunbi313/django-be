from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.generics import ListAPIView, RetrieveAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderUpdateInfoSerializer
from apps.cart.models import Cart, CartItem


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic()
    def post(self, request):
        user = request.user
        cart = Cart.objects.get(user=user)
        cart_items = cart.items.all()

        if not cart_items.exists():
            return Response({"error": "Giỏ hàng của bạn đang trống."}, status=400)

        # Lấy thông tin từ UserProfile
        try:
            profile = user.profile
        except:
            return Response({"error": "Người dùng chưa có thông tin profile."}, status=400)

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

        return Response({"message": "Thanh toán thành công", "order_id": order.id, "status": order.status})


class OrderListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class OrderDetailView(RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Chỉ cho phép user lấy đơn hàng của chính mình
        return Order.objects.filter(user=self.request.user)


class UpdateOrderInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)

        if order.status != 'pending':
            return Response({"error": "chỉ cập nhật đơn hàng khi chưa thanh toán"})

        serializer = OrderUpdateInfoSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Cập nhật thông tin đơn hàng thành công"})
        return Response(serializer.errors, status=400)


class AllOrdersAdminView(ListAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]
    pagination_class = None


class AdminOrderDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser] 