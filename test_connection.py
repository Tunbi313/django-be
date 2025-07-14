#!/usr/bin/env python3
"""
Script test kết nối giữa Angular và Django
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://127.0.0.1:8000/api/v1"
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def test_api_connection():
    """Test kết nối cơ bản với API"""
    print("=== TEST KẾT NỐI API ===")
    
    try:
        # Test 1: Kiểm tra server có hoạt động không
        response = requests.get(f"{BASE_URL}/products/", headers=HEADERS)
        print(f"✅ Server hoạt động: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📦 Số sản phẩm: {data.get('count', 0)}")
        else:
            print(f"❌ Lỗi: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Không thể kết nối đến server")
        print("Hãy đảm bảo Django server đang chạy: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False
    
    return True

def test_authentication():
    """Test authentication"""
    print("\n=== TEST AUTHENTICATION ===")
    
    # Test đăng ký
    register_data = {
        "username": "testuser_connection",
        "email": "test@connection.com",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "Connection"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/users/register/", 
                               json=register_data, headers=HEADERS)
        print(f"📝 Đăng ký: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ Đăng ký thành công")
        else:
            print(f"❌ Lỗi đăng ký: {response.text}")
            
    except Exception as e:
        print(f"❌ Lỗi đăng ký: {e}")
    
    # Test đăng nhập
    login_data = {
        "username": "testuser_connection",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/users/login/", 
                               json=login_data, headers=HEADERS)
        print(f"🔐 Đăng nhập: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access')
            print("✅ Đăng nhập thành công")
            print(f"🔑 Token nhận được: {token[:20]}...")
            return token
        else:
            print(f"❌ Lỗi đăng nhập: {response.text}")
            
    except Exception as e:
        print(f"❌ Lỗi đăng nhập: {e}")
    
    return None

def test_authenticated_endpoints(token):
    """Test các endpoint cần authentication"""
    if not token:
        print("❌ Không có token để test")
        return
    
    print("\n=== TEST AUTHENTICATED ENDPOINTS ===")
    
    auth_headers = HEADERS.copy()
    auth_headers['Authorization'] = f'Bearer {token}'
    
    # Test lấy thông tin user
    try:
        response = requests.get(f"{BASE_URL}/users/me/", headers=auth_headers)
        print(f"👤 User info: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ User: {user_data.get('username')}")
        else:
            print(f"❌ Lỗi: {response.text}")
            
    except Exception as e:
        print(f"❌ Lỗi user info: {e}")
    
    # Test giỏ hàng
    try:
        response = requests.get(f"{BASE_URL}/cart/", headers=auth_headers)
        print(f"🛒 Cart: {response.status_code}")
        
        if response.status_code == 200:
            cart_data = response.json()
            print(f"✅ Cart items: {cart_data.get('total_items', 0)}")
        else:
            print(f"❌ Lỗi cart: {response.text}")
            
    except Exception as e:
        print(f"❌ Lỗi cart: {e}")
    
    # Test đơn hàng
    try:
        response = requests.get(f"{BASE_URL}/orders/", headers=auth_headers)
        print(f"📋 Orders: {response.status_code}")
        
        if response.status_code == 200:
            orders_data = response.json()
            print(f"✅ Orders count: {orders_data.get('count', 0)}")
        else:
            print(f"❌ Lỗi orders: {response.text}")
            
    except Exception as e:
        print(f"❌ Lỗi orders: {e}")

def test_cors():
    """Test CORS headers"""
    print("\n=== TEST CORS ===")
    
    try:
        response = requests.options(f"{BASE_URL}/products/", headers=HEADERS)
        print(f"🌐 CORS preflight: {response.status_code}")
        
        # Kiểm tra CORS headers
        cors_headers = [
            'Access-Control-Allow-Origin',
            'Access-Control-Allow-Methods',
            'Access-Control-Allow-Headers'
        ]
        
        for header in cors_headers:
            if header in response.headers:
                print(f"✅ {header}: {response.headers[header]}")
            else:
                print(f"❌ Thiếu header: {header}")
                
    except Exception as e:
        print(f"❌ Lỗi CORS test: {e}")

def test_angular_connection():
    """Test kết nối từ Angular perspective"""
    print("\n=== TEST ANGULAR CONNECTION ===")
    
    # Simulate Angular request
    angular_headers = HEADERS.copy()
    angular_headers['Origin'] = 'http://localhost:4200'
    angular_headers['Referer'] = 'http://localhost:4200/'
    
    try:
        response = requests.get(f"{BASE_URL}/products/", headers=angular_headers)
        print(f"🔄 Angular request: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Angular có thể kết nối với Django API")
        else:
            print(f"❌ Angular không thể kết nối: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Lỗi Angular connection: {e}")

def main():
    """Main test function"""
    print("🚀 BẮT ĐẦU TEST KẾT NỐI ANGULAR - DJANGO")
    print("=" * 50)
    
    # Test 1: Kết nối cơ bản
    if not test_api_connection():
        print("\n❌ Không thể kết nối đến Django server")
        print("Hãy khởi động server: python manage.py runserver")
        return
    
    # Test 2: CORS
    test_cors()
    
    # Test 3: Authentication
    token = test_authentication()
    
    # Test 4: Authenticated endpoints
    if token:
        test_authenticated_endpoints(token)
    
    # Test 5: Angular connection
    test_angular_connection()
    
    print("\n" + "=" * 50)
    print("✅ HOÀN THÀNH TEST KẾT NỐI")
    print("\n📋 HƯỚNG DẪN TIẾP THEO:")
    print("1. Khởi động Angular: cd ../fe && ng serve")
    print("2. Mở browser: http://localhost:4200")
    print("3. Test các chức năng trong Angular app")
    print("4. Kiểm tra Network tab trong DevTools")

if __name__ == "__main__":
    main() 