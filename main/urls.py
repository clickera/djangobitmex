from django.urls import re_path
from rest_framework.routers import DefaultRouter

from .views import OrderView, Index

router = DefaultRouter()
router.register(r'orders/(?P<account_name>.[^/]+)', OrderView, basename="orders")

urlpatterns = [
    re_path("^$", Index.as_view())
]

urlpatterns += router.urls