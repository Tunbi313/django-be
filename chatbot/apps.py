from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'

    def ready(self):
        from .chat_utils import prepare_knowledge_base_sync, fetch_data_from_database
        prepare_knowledge_base_sync()
        fetch_data_from_database()
