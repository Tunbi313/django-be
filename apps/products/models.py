from pickle import TRUE
from django.db import models
from django.utils import timezone
from datetime import timedelta

class Category(models.Model):
    name = models.CharField(max_length = 100,unique = True)
    description = models.TextField(blank = True,null = True)

    def __str__(self):
        return self.name



class Product(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('sale', 'Sale'),
        ('out_of_stock', 'Out of Stock'),
        ('regular', 'Regular'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.URLField()
    quantity = models.PositiveIntegerField(default=1)
    category = models.ForeignKey('Category',on_delete = models.SET_NULL,null=True,related_name='products')
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')

    def save(self, *args, **kwargs):
        # Tự động cập nhật trạng thái dựa trên quantity
        self.update_status_based_on_quantity()
        super().save(*args, **kwargs)
    
    def update_status_based_on_quantity(self):
        """Cập nhật trạng thái dựa trên số lượng hàng"""
        # Nếu hết hàng thì chuyển sang out_of_stock
        if self.quantity == 0:
            self.status = 'out_of_stock'
        # Nếu có hàng và không có sale active thì kiểm tra thời gian new
        elif self.quantity > 0 and not self.has_active_sale():
            self.check_new_status()
        # Nếu có sale active thì giữ nguyên sale (được xử lý bởi SaleProduct)
    
    def check_new_status(self):
        """Kiểm tra xem sản phẩm có còn là new không dựa trên thời gian"""
        # Sản phẩm chỉ được coi là "new" trong 7 ngày đầu
        new_duration = timedelta(days=7)
        current_time = timezone.now()
        
        if current_time - self.created_at <= new_duration:
            self.status = 'new'
        else:
            # Sau 7 ngày, nếu không có sale thì không có trạng thái đặc biệt
            # Có thể thêm trạng thái 'regular' nếu cần
            self.status = 'regular'  # hoặc có thể để trống nếu không cần trạng thái
    
    def has_active_sale(self):
        """Kiểm tra xem sản phẩm có sale đang active không"""
        try:
            sale_info = self.sale_info
            return sale_info.is_active()
        except:
            return False
    
    def get_current_price(self):
        """Lấy giá hiện tại (có tính sale nếu có)"""
        if self.has_active_sale():
            return self.sale_info.discounted_price()
        return self.price
    
    def get_discount_percent(self):
        """Lấy phần trăm giảm giá hiện tại"""
        if self.has_active_sale():
            return self.sale_info.discount_percent
        return 0

    def __str__(self):
        return self.name 