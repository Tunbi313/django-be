from django.core.mail import send_mail
from django.conf import settings

def send_payment_email(user, order):
    # Lấy thông tin từ userinfo (profile)
    profile = getattr(user, 'profile', None)
    username = profile.first_name if profile and profile.first_name else user.username
    email = profile.email if profile and profile.email else user.email

    subject_user = f"Thanh toán đơn hàng #{order.id} thành công"
    message_user = f"""
Chào {username},

Cảm ơn bạn đã thanh toán đơn hàng #{order.id}!

Thông tin đơn hàng:
- Tổng tiền: {order.total_price} VND
- Trạng thái: {order.status}

Chúng tôi sẽ sớm xử lý đơn hàng của bạn.

Trân trọng,
Đội ngũ hỗ trợ
"""

    subject_admin = f"Khách hàng {username} đã thanh toán đơn hàng #{order.id}"
    message_admin = f"""
Khách hàng: {username}
Email: {email}
Mã đơn hàng: {order.id}
Tổng tiền: {order.total_price} VND
Trạng thái: {order.status}
"""

    # Gửi email cho user
    send_mail(
        subject_user,
        message_user,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )

    # Gửi email cho admin
    admin_emails = [email for name, email in settings.ADMINS]
    send_mail(
        subject_admin,
        message_admin,
        settings.DEFAULT_FROM_EMAIL,
        admin_emails,
        fail_silently=False,
    )