# Django E-commerce Backend

Backend API cho hệ thống bán hàng trực tuyến được xây dựng bằng Django và Django REST Framework.

## Cấu trúc dự án

```
be/
├── apps/                    # Các Django apps
│   ├── users/              # Quản lý user và profile
│   ├── products/           # Quản lý sản phẩm
│   ├── cart/               # Quản lý giỏ hàng
│   └── orders/             # Quản lý đơn hàng
├── core/                   # Core functionality
├── api/                    # API endpoints
│   └── v1/                # API version 1
├── store/                  # Project settings
│   └── settings/          # Settings cho các môi trường
└── scripts/               # Management scripts
```

## Cài đặt

1. Clone repository:
```bash
git clone <repository-url>
cd be
```

2. Tạo virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows
```

3. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

4. Chạy migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Tạo superuser:
```bash
python manage.py createsuperuser
```

6. Chạy server:
```bash
python manage.py runserver
```

## API Endpoints

### Authentication
- `POST /api/v1/users/register/` - Đăng ký
- `POST /api/v1/users/login/` - Đăng nhập
- `POST /api/v1/users/logout/` - Đăng xuất

### Products
- `GET /api/v1/products/` - Danh sách sản phẩm
- `GET /api/v1/products/all/` - Tất cả sản phẩm (không phân trang)
- `GET /api/v1/products/<id>/` - Chi tiết sản phẩm

### Cart
- `GET /api/v1/cart/` - Xem giỏ hàng
- `POST /api/v1/cart/add/` - Thêm vào giỏ hàng
- `PUT /api/v1/cart/item/<id>/update/` - Cập nhật số lượng
- `DELETE /api/v1/cart/item/<id>/remove/` - Xóa khỏi giỏ hàng

### Orders
- `POST /api/v1/orders/checkout/` - Tạo đơn hàng
- `GET /api/v1/orders/` - Danh sách đơn hàng
- `GET /api/v1/orders/<id>/` - Chi tiết đơn hàng
- `POST /api/v1/orders/<id>/pay/` - Thanh toán

### Admin
- `GET /api/v1/users/admin/users/` - Tất cả users
- `GET /api/v1/users/admin/userprofiles/` - Tất cả user profiles

## Môi trường

- Development: `python manage.py runserver --settings=store.settings.development`
- Production: `python manage.py runserver --settings=store.settings.production`

## Đóng góp

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Tạo Pull Request 