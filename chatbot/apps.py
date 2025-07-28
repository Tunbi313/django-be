from django.apps import AppConfig
import sys


class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'

    def ready(self):
        # Chỉ preload khi chạy runserver
        if 'runserver' in sys.argv:
            from .chat_utils import prepare_knowledge_base_sync, fetch_data_from_database
            prepare_knowledge_base_sync()
            fetch_data_from_database()
