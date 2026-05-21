from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import BookViewSet, CategoryViewSet, OrderViewSet, CartViewSet

router = DefaultRouter()
router.register(r"books", BookViewSet, basename="book")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"cart", CartViewSet, basename="cart")

urlpatterns = [
    path("", include(router.urls)),
]
