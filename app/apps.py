# from django.apps import AppConfig


# class AppConfig(AppConfig):
#     default_auto_field = "django.db.models.BigAutoField"
#     name = "app"


#     def ready(self):
#         import app.signals


# data/apps.py
from django.apps import AppConfig

class DataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        import threading
        from .redis_listener import start_redis_listener
        
        # Start Redis listener in background thread
        threading.Thread(target=start_redis_listener, daemon=True).start()