from django.urls import re_path

from .consumers import Consumer

websocket_urlpatterns = [
    re_path('^ws/orders/', Consumer.as_asgi())
]