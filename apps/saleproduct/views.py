from rest_framework import generics
from .models import SaleProduct
from .serializers import SaleProductSerializer
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser,AllowAny
from django.utils import timezone

class ActiveSaleProductListAPIView(generics.ListAPIView):
    serializer_class = SaleProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        now = timezone.now()
        return SaleProduct.objects.filter(start_date__lte=now, end_date__gte=now)

class SaleProductCreateUpdateAPIView(generics.CreateAPIView, generics.UpdateAPIView):
    queryset = SaleProduct.objects.all()
    serializer_class = SaleProductSerializer
    permission_classes = [IsAdminUser]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        product_id = data.get('product')
        if not product_id:
            raise ValidationError({'product': 'This field is required.'})

        # Nếu không có start_date thì lấy thời gian hiện tại
        if not data.get('start_date'):
            data['start_date'] = timezone.now().isoformat()

        # Kiểm tra đã có sale cho product này chưa
        try:
            sale = SaleProduct.objects.get(product_id=product_id)
            serializer = self.get_serializer(sale, data=data)
        except SaleProduct.DoesNotExist:
            serializer = self.get_serializer(data=data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)