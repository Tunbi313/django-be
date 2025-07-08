# Hướng dẫn test API với phân quyền

## 1. Tạo Admin User (chỉ dùng để test)

```bash
POST http://localhost:8000/api/create-admin/
Content-Type: application/json

{
    "username": "admin",
    "password": "admin123",
    "email": "admin@example.com"
}
```

Response:
```json
{
    "message": "Tạo admin thành công",
    "token": "your_admin_token_here",
    "user": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "is_staff": true
    }
}
```

## 2. Tạo User thường

```bash
POST http://localhost:8000/api/register/
Content-Type: application/json

{
    "username": "user1",
    "password": "user123",
    "email": "user1@example.com"
}
```

## 3. Đăng nhập User thường

```bash
POST http://localhost:8000/api/login/
Content-Type: application/json

{
    "username": "user1",
    "password": "user123"
}
```

## 4. Test phân quyền Product API

### 4.1. User thường - Chỉ có thể GET (xem sản phẩm)

```bash
# Xem danh sách sản phẩm - OK
GET http://localhost:8000/api/products/
Authorization: Token your_user_token_here

# Xem chi tiết sản phẩm - OK
GET http://localhost:8000/api/products/1/
Authorization: Token your_user_token_here

# Tạo sản phẩm mới - FORBIDDEN (403)
POST http://localhost:8000/api/products/
Authorization: Token your_user_token_here
Content-Type: application/json

{
    "name": "Sản phẩm mới",
    "description": "Mô tả sản phẩm",
    "price": "100.00",
    "image": "https://example.com/image.jpg",
    "quantity": 10
}

# Cập nhật sản phẩm - FORBIDDEN (403)
PUT http://localhost:8000/api/products/1/
Authorization: Token your_user_token_here
Content-Type: application/json

{
    "name": "Sản phẩm đã cập nhật",
    "description": "Mô tả mới",
    "price": "150.00",
    "image": "https://example.com/new-image.jpg",
    "quantity": 15
}

# Xóa sản phẩm - FORBIDDEN (403)
DELETE http://localhost:8000/api/products/1/
Authorization: Token your_user_token_here
```

### 4.2. Admin - Có thể thực hiện tất cả thao tác

```bash
# Xem danh sách sản phẩm - OK
GET http://localhost:8000/api/products/
Authorization: Token your_admin_token_here

# Tạo sản phẩm mới - OK
POST http://localhost:8000/api/products/
Authorization: Token your_admin_token_here
Content-Type: application/json

{
    "name": "Sản phẩm mới",
    "description": "Mô tả sản phẩm",
    "price": "100.00",
    "image": "https://example.com/image.jpg",
    "quantity": 10
}

# Cập nhật sản phẩm - OK
PUT http://localhost:8000/api/products/1/
Authorization: Token your_admin_token_here
Content-Type: application/json

{
    "name": "Sản phẩm đã cập nhật",
    "description": "Mô tả mới",
    "price": "150.00",
    "image": "https://example.com/new-image.jpg",
    "quantity": 15
}

# Xóa sản phẩm - OK
DELETE http://localhost:8000/api/products/1/
Authorization: Token your_admin_token_here
```

## 5. Các API khác

### 5.1. Orders API (yêu cầu đăng nhập)

```bash
# Tạo đơn hàng
POST http://localhost:8000/api/orders/create/
Authorization: Token your_token_here
Content-Type: application/json

{
    "status": "pending",
    "items": [
        {
            "product": 1,
            "quantity": 2
        }
    ]
}

# Xem danh sách đơn hàng
GET http://localhost:8000/api/orders/
Authorization: Token your_token_here

# Xem chi tiết đơn hàng
GET http://localhost:8000/api/orders/1/
Authorization: Token your_token_here
```

## Lưu ý:

1. **Admin** (`is_staff=True`): Có thể thực hiện tất cả thao tác CRUD trên Product
2. **User thường**: Chỉ có thể xem (GET) sản phẩm
3. **Không đăng nhập**: Không thể truy cập bất kỳ API nào (trừ register, login, create-admin)
4. Tất cả API đều yêu cầu token authentication (trừ register, login, create-admin)

## Cách kiểm tra quyền:

- Response 200: Thành công
- Response 403: Không có quyền
- Response 401: Chưa đăng nhập hoặc token không hợp lệ 