from django.db import models
from apps.products.models import Product
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class SaleProduct(models.Model):
    product = models.OneToOneField(Product,on_delete=models.CASCADE,related_name="sale_info")
    discount_percent = models.PositiveIntegerField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def is_active(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date

    def discounted_price(self):
        if self.is_active():
            return self.product.price*(100 - self.discount_percent)/100
        return self.product.price  

    def __str__(self):
        return f"{self.product.name} - {self.discount_percent}% sale"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Tự động cập nhật trạng thái sản phẩm
        self.update_product_status()
    
    def update_product_status(self):
        """Cập nhật trạng thái sản phẩm dựa trên sale"""
        if self.is_active():
            self.product.status = 'sale'
        else:
            # Kiểm tra nếu hết hàng thì giữ nguyên out_of_stock, không thì kiểm tra thời gian new
            if self.product.quantity == 0:
                self.product.status = 'out_of_stock'
            else:
                self.product.check_new_status()
        self.product.save()


# Signals để tự động cập nhật trạng thái sản phẩm
@receiver(post_save, sender=SaleProduct)
def update_product_status_on_sale_save(sender, instance, created, **kwargs):
    """Tự động cập nhật trạng thái sản phẩm khi tạo/cập nhật sale"""
    instance.update_product_status()

@receiver(post_delete, sender=SaleProduct)
def update_product_status_on_sale_delete(sender, instance, **kwargs):
    """Tự động cập nhật trạng thái sản phẩm khi xóa sale"""
    product = instance.product
    if product.quantity == 0:
        product.status = 'out_of_stock'
    else:
        product.check_new_status()
    product.save()
