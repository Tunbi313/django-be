# chat_api/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .chat_utils import get_chatbot_response # Import hàm chat từ chat_utils
from rest_framework.permissions import AllowAny

class ChatbotView(APIView):
    permission_classes = [AllowAny]
    """
    API View để xử lý các yêu cầu chat từ frontend.
    """
    def post(self, request, *args, **kwargs):
        print("request.body:", request.body)
        print("request.content_type:", request.content_type)
        print("request.data:", request.data)
        user_message = request.data.get('message')
        # Lấy lịch sử chat từ request, mặc định là rỗng nếu không có
        chat_history = request.data.get('history', [])

        if not user_message:
            return Response({"error": "Tin nhắn là bắt buộc."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Gọi hàm chatbot logic của bạn
            ai_response = get_chatbot_response(user_message, chat_history)
            return Response({"response": ai_response}, status=status.HTTP_200_OK)
        except Exception as e:
            # Ghi log lỗi để debug
            print(f"Lỗi khi xử lý yêu cầu chat: {e}")
            return Response({"error": "Xin lỗi, đã có lỗi xảy ra ở phía máy chủ. Vui lòng thử lại sau."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)