# your_project/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/live-prices/$', consumers.LivePriceConsumer.as_asgi()),
]