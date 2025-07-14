TEST API - E-COMMERCE BACKEND

## 1. THIẾT LẬP BAN ĐẦU

### Khởi động server
```bash
python manage.py runserver
```

## 2. TEST API AUTHENTICATION (USERS)

### 2.1 Đăng ký tài khoản mới
```bash
curl -X POST http://127.0.0.1:8000/api/v1/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
  }'
```

**Response mong đợi:**
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "first_name": "Test",
  "last_name": "User",
  "is_active": true,
  "date_joined": "2024-01-01T00:00:00Z"
}
```

### 2.2 Đăng nhập
```bash
curl -X POST http://127.0.0.1:8000/api/v1/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

**Response mong đợi:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 2.3 Lấy thông tin user hiện tại
```bash
curl -X GET http://127.0.0.1:8000/api/v1/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 2.4 Cập nhật thông tin user
```bash
curl -X PUT http://127.0.0.1:8000/api/v1/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Updated",
    "last_name": "Name"
  }'
```

## 3. TEST API PRODUCTS

### 3.1 Lấy danh sách sản phẩm (không cần auth)
```bash
curl -X GET http://127.0.0.1:8000/api/v1/products/
```

### 3.2 Lấy chi tiết sản phẩm
```bash
curl -X GET http://127.0.0.1:8000/api/v1/products/1/
```

### 3.3 Tìm kiếm sản phẩm
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/products/?search=laptop"
```

### 3.4 Lọc theo danh mục
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/products/?category=electronics"
```

### 3.5 Admin: Tạo sản phẩm mới
```bash
curl -X POST http://127.0.0.1:8000/api/v1/products/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop Gaming",
    "description": "Laptop gaming hiệu suất cao",
    "price": 25000000,
    "category": "electronics",
    "quantity": 10,
    "image": "laptop.jpg"
  }'
```

### 3.6 Admin: Cập nhật sản phẩm
```bash
curl -X PUT http://127.0.0.1:8000/api/v1/products/1/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop Gaming Pro",
    "price": 28000000,
    "quantity": 15
  }'
```

### 3.7 Admin: Xóa sản phẩm
```bash
curl -X DELETE http://127.0.0.1:8000/api/v1/products/1/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

## 4. TEST API CART

### 4.1 Thêm sản phẩm vào giỏ hàng
```bash
curl -X POST http://127.0.0.1:8000/api/v1/cart/add/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "quantity": 2
  }'
```

### 4.2 Xem giỏ hàng
```bash
curl -X GET http://127.0.0.1:8000/api/v1/cart/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4.3 Cập nhật số lượng sản phẩm trong giỏ hàng
```bash
curl -X PUT http://127.0.0.1:8000/api/v1/cart/update/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "quantity": 3
  }'
```

### 4.4 Xóa sản phẩm khỏi giỏ hàng
```bash
curl -X DELETE http://127.0.0.1:8000/api/v1/cart/remove/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4.5 Xóa toàn bộ giỏ hàng
```bash
curl -X DELETE http://127.0.0.1:8000/api/v1/cart/clear/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 5. TEST API ORDERS

### 5.1 Tạo đơn hàng mới (checkout)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/orders/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "shipping_address": "123 Đường ABC, Quận 1, TP.HCM",
    "phone": "0123456789"
  }'
```

### 5.2 Xem danh sách đơn hàng của user
```bash
curl -X GET http://127.0.0.1:8000/api/v1/orders/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5.3 Xem chi tiết đơn hàng
```bash
curl -X GET http://127.0.0.1:8000/api/v1/orders/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5.4 Admin: Xem tất cả đơn hàng
```bash
curl -X GET http://127.0.0.1:8000/api/v1/orders/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

### 5.5 Admin: Cập nhật trạng thái đơn hàng
```bash
curl -X PATCH http://127.0.0.1:8000/api/v1/orders/1/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "shipped"
  }'
```

### 5.6 Admin: Xóa đơn hàng
```bash
curl -X DELETE http://127.0.0.1:8000/api/v1/orders/1/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

## 6. SCRIPT TEST TỰ ĐỘNG

### Tạo file test script
```bash
# Tạo file test_api.py
```

### Nội dung script test:
```python
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"
access_token = None
admin_token = None

def test_authentication():
    global access_token, admin_token
    
    # Test đăng ký
    print("=== TEST ĐĂNG KÝ ===")
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "User"
    }
    response = requests.post(f"{BASE_URL}/users/register/", json=register_data)
    print(f"Đăng ký: {response.status_code}")
    print(response.json())
    
    # Test đăng nhập
    print("\n=== TEST ĐĂNG NHẬP ===")
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    response = requests.post(f"{BASE_URL}/users/login/", json=login_data)
    print(f"Đăng nhập: {response.status_code}")
    if response.status_code == 200:
        access_token = response.json()["access"]
        print("Token nhận được!")
    
    # Test đăng nhập admin
    admin_login = {
        "username": "admin",
        "password": "admin123"
    }
    response = requests.post(f"{BASE_URL}/users/login/", json=admin_login)
    if response.status_code == 200:
        admin_token = response.json()["access"]
        print("Admin token nhận được!")

def test_products():
    print("\n=== TEST PRODUCTS ===")
    
    # Lấy danh sách sản phẩm
    response = requests.get(f"{BASE_URL}/products/")
    print(f"Lấy danh sách sản phẩm: {response.status_code}")
    
    # Tìm kiếm sản phẩm
    response = requests.get(f"{BASE_URL}/products/?search=laptop")
    print(f"Tìm kiếm sản phẩm: {response.status_code}")

def test_cart():
    global access_token
    if not access_token:
        print("Cần đăng nhập trước!")
        return
    
    print("\n=== TEST CART ===")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Thêm vào giỏ hàng
    cart_data = {"product_id": 1, "quantity": 2}
    response = requests.post(f"{BASE_URL}/cart/add/", json=cart_data, headers=headers)
    print(f"Thêm vào giỏ hàng: {response.status_code}")
    
    # Xem giỏ hàng
    response = requests.get(f"{BASE_URL}/cart/", headers=headers)
    print(f"Xem giỏ hàng: {response.status_code}")
    if response.status_code == 200:
        print(response.json())

def test_orders():
    global access_token, admin_token
    if not access_token:
        print("Cần đăng nhập trước!")
        return
    
    print("\n=== TEST ORDERS ===")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Tạo đơn hàng
    order_data = {
        "shipping_address": "123 Đường ABC, Quận 1, TP.HCM",
        "phone": "0123456789"
    }
    response = requests.post(f"{BASE_URL}/orders/", json=order_data, headers=headers)
    print(f"Tạo đơn hàng: {response.status_code}")
    
    # Xem đơn hàng
    response = requests.get(f"{BASE_URL}/orders/", headers=headers)
    print(f"Xem đơn hàng: {response.status_code}")
    
    # Admin cập nhật trạng thái
    if admin_token:
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {"status": "shipped"}
        response = requests.patch(f"{BASE_URL}/orders/1/", json=update_data, headers=admin_headers)
        print(f"Admin cập nhật trạng thái: {response.status_code}")

if __name__ == "__main__":
    test_authentication()
    test_products()
    test_cart()
    test_orders()
```

## 7. TEST VỚI POSTMAN

### Import Collection
1. Tạo collection mới trong Postman
2. Import các request sau:

#### Environment Variables
```
BASE_URL: http://127.0.0.1:8000/api/v1
ACCESS_TOKEN: (sẽ được set sau khi login)
ADMIN_TOKEN: (sẽ được set sau khi admin login)
```

#### Pre-request Script cho Login
```javascript
// Sau khi login thành công
pm.environment.set("ACCESS_TOKEN", pm.response.json().access);
```

## 8. KIỂM TRA LỖI THƯỜNG GẶP

### 8.1 Lỗi Authentication
- Kiểm tra token có hợp lệ không
- Token có hết hạn không
- Format Authorization header đúng không

### 8.2 Lỗi Permission
- User có quyền thực hiện action không
- Admin endpoints cần admin token

### 8.3 Lỗi Validation
- Kiểm tra format dữ liệu gửi lên
- Required fields có đầy đủ không
- Data types có đúng không

### 8.4 Lỗi Database
- Kiểm tra sản phẩm có tồn tại không
- Giỏ hàng có sản phẩm không
- Đơn hàng có hợp lệ không

## 9. MONITORING VÀ LOGGING

### Kiểm tra logs Django
```bash
# Xem logs trong terminal khi chạy server
python manage.py runserver --verbosity=2
```

### Debug mode
```python
# Trong settings.py
DEBUG = True
```

## 10. PERFORMANCE TESTING

### Test với nhiều request
```bash
# Sử dụng Apache Bench hoặc wrk
ab -n 100 -c 10 http://127.0.0.1:8000/api/v1/products/
```

### Test database queries
```python
# Trong Django shell
python manage.py shell
from django.db import connection
from django.db import reset_queries
import time

reset_queries()
# Thực hiện API call
print(len(connection.queries))
```

---

## LƯU Ý QUAN TRỌNG

1. **Luôn test với dữ liệu thật** trước khi deploy
2. **Backup database** trước khi test
3. **Kiểm tra permissions** cho từng endpoint
4. **Validate input data** kỹ lưỡng
5. **Test error cases** không chỉ success cases
6. **Monitor performance** khi có nhiều user
7. **Log đầy đủ** để debug khi cần

## HỖ TRỢ

Nếu gặp lỗi, kiểm tra:
- Server có đang chạy không
- Database có kết nối được không
- Token có hợp lệ không
- URL có đúng không
- Data format có đúng không 