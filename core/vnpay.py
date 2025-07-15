import hashlib
import hmac
from urllib.parse import urlencode

def generate_vnpay_url(order, amount, config, user):
    vnp_params = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": config["vnp_TmnCode"],
        "vnp_Amount": str(int(amount * 100)),  # VNPay yêu cầu số tiền * 100
        "vnp_CurrCode": "VND",
        "vnp_TxnRef": str(order.id),
        "vnp_OrderInfo": f"Thanh toan don hang {order.id}",
        "vnp_OrderType": "other",
        "vnp_Locale": "vn",
        "vnp_ReturnUrl": config["vnp_ReturnUrl"],
        "vnp_IpAddr": config["vnp_IpAddr"],
        "vnp_CreateDate": order.created_at.strftime("%Y%m%d%H%M%S"),
    }
    # Sắp xếp tham số theo thứ tự alphabet
    sorted_params = sorted(vnp_params.items())
    query_string = urlencode(sorted_params)
    # Tạo chuỗi dữ liệu để ký
    hash_data = '&'.join([f"{k}={v}" for k, v in sorted_params])
    # Ký HMAC SHA512
    secure_hash = hmac.new(
        config["vnp_HashSecret"].encode('utf-8'),
        hash_data.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()
    # Thêm secure hash vào URL
    payment_url = f"{config['vnp_Url']}?{query_string}&vnp_SecureHash={secure_hash}"
    print("VNPay hash_data:", hash_data)
    print("VNPay secure_hash:", secure_hash)
    print("VNPay payment_url:", payment_url)
    return payment_url 