from django.core.management.base import BaseCommand
from apps.products.models import Product
from apps.saleproduct.models import SaleProduct
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Đồng bộ trạng thái sản phẩm dựa trên sale và số lượng hàng'

    def handle(self, *args, **options):
        products = Product.objects.all()
        updated_count = 0
        
        for product in products:
            old_status = product.status
            
            # Kiểm tra hết hàng
            if product.quantity == 0:
                product.status = 'out_of_stock'
            # Kiểm tra có sale active không
            elif product.has_active_sale():
                product.status = 'sale'
            # Kiểm tra thời gian new
            else:
                product.check_new_status()
            
            if old_status != product.status:
                product.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Sản phẩm "{product.name}" đã chuyển từ {old_status} sang {product.status}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Hoàn thành! Đã cập nhật {updated_count} sản phẩm.'
            )
        ) 