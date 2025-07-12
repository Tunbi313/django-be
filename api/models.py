from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='profile')
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    address = models.TextField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField()
    image = models.URLField(null = True)

    def __str__(self):
        return f"{self.first_name}{self.lastname}({self.user.username})"



# product
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10,decimal_places=2)
    image = models.URLField()
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name
    
#cart
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Giỏ hàng của {self.user.username}"
    
#cartitem

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')  # Mỗi sản phẩm chỉ 1 dòng trong giỏ

    def clean(self):
        if self.quantity > self.product.quantity:
            raise ValidationError(f"Số lượng đặt ({self.quantity}) vượt quá tồn kho ({self.product.quantity})")

    def __str__(self):
        return f"{self.quantity} x {self.product.name} trong giỏ của {self.cart.user.username}"    

#order    
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    #Thông tin người nhận
    receiver_name = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)


    def update_total_price(self):
        total = sum(item.price * item.quantity for item in self.items.all())
        self.total_price = total

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Đơn hàng #{self.id} của {self.user.username}"
#orderitem
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def clean(self):
        if self.quantity > self.product.quantity:
            raise ValidationError(f"Số lượng mua ({self.quantity}) vượt quá tồn kho ({self.product.quantity})")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.order.update_total_price()
        self.order.save()

        # Trừ tồn kho
        self.product.quantity -= self.quantity
        self.product.save()

    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        order.update_total_price()
        order.save()

    def __str__(self):
        return f"{self.quantity} x {self.product.name} trong đơn #{self.order.id}"

