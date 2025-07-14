from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from .serializers import CartSerializer
from apps.products.models import Product


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get("product_id")
        raw_quantity = request.data.get("quantity", 1)

        try:
            quantity = int(raw_quantity)
            if quantity < 1:
                raise ValueError
        except (ValueError, TypeError):
            return Response({"error": "quantity >= 1"}, status=400)

        if not product_id:
            return Response({"error": "Thiếu product_id"}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, id=product_id)

        if quantity > product.quantity:
            return Response({"error": f"Số lượng vượt quá tồn kho ({product.quantity})"}, status=status.HTTP_400_BAD_REQUEST)

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        if not created:
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product.quantity:
                return Response({"error": f"Tổng số lượng vượt quá tồn kho ({product.quantity})"}, status=status.HTTP_400_BAD_REQUEST)
            cart_item.quantity = new_quantity
        else:
            cart_item.quantity = quantity

        try:
            cart_item.full_clean()
            cart_item.save()
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Đã thêm vào giỏ hàng"}, status=status.HTTP_200_OK)


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


class RemoveCartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
        return Response({"message": "Đã xóa khỏi giỏ hàng"}, status=status.HTTP_200_OK)


class RemoveCartView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        cart.delete()
        return Response({"message": "Đã xóa giỏ hàng thành công"}, status=status.HTTP_200_OK) 