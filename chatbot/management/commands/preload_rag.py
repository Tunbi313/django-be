# chat_api/management/commands/preload_rag.py

import os
from django.core.management.base import BaseCommand
from chatbot.chat_utils import prepare_knowledge_base_sync
import threading # Để chạy preload trong luồng riêng

class Command(BaseCommand):
    help = 'Preloads the RAG knowledge base for the chatbot when Django starts up.'

    def handle(self, *args, **options):
        # Đảm bảo thư mục 'data' tồn tại
        data_dir = os.path.join(os.getcwd(), 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            self.stdout.write(self.style.WARNING(f"Đã tạo thư mục 'data' tại: {data_dir}. Vui lòng đặt tài liệu của bạn vào đó."))

        # Chạy việc tải cơ sở tri thức trong một luồng riêng
        # Điều này giúp server Django khởi động nhanh chóng mà không bị chặn
        self.stdout.write(self.style.SUCCESS('Đang bắt đầu tải cơ sở tri thức RAG trong nền...'))
        thread = threading.Thread(target=prepare_knowledge_base_sync, args=(data_dir,))
        thread.daemon = True # Đặt luồng là daemon để nó tự động kết thúc khi chương trình chính kết thúc
        thread.start()
        # Không cần join thread ở đây, nó sẽ chạy song song
        self.stdout.write(self.style.SUCCESS('Cơ sở tri thức RAG đang được tải. Chatbot sẽ sẵn sàng sau khi quá trình hoàn tất.'))