from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from shop.models import Book, Category, Order
from shop.cart import Cart
from .serializers import (
    BookSerializer,
    CategorySerializer,
    OrderSerializer,
    OrderCreateSerializer,
    CartSerializer,
    CartAddSerializer,
)
from .permissions import IsOwnerOrReadOnly
from .filters import BookFilter, OrderFilter


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Category model.
    - List/Retrieve: any user
    - Create/Update/Delete: admin only
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "slug"]
    ordering_fields = ["name"]
    ordering = ["name"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAdminUser()]


class BookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Book model.
    - List/Retrieve: any user
    - Create/Update/Delete: admin only
    Supports filtering, searching, ordering.
    """

    queryset = Book.objects.select_related("category").all()
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BookFilter
    search_fields = ["title", "author", "description"]
    ordering_fields = ["title", "price", "created_at", "stock"]
    ordering = ["title"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAdminUser()]


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Order model.
    - List/Retrieve: authenticated owner or admin
    - Create: authenticated user
    - Update/Delete: owner or admin
    """

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = OrderFilter
    ordering_fields = ["created_at", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.prefetch_related("items__book").all()
        return Order.objects.prefetch_related("items__book").filter(user=user)

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsOwnerOrReadOnly()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CartViewSet(viewsets.ViewSet):
    """
    ViewSet for session-based Cart.
    - GET /api/cart/ — get cart contents
    - POST /api/cart/add/ — add item
    - POST /api/cart/remove/ — remove item
    - POST /api/cart/clear/ — clear cart
    """

    permission_classes = [IsAuthenticated]

    def _get_cart_data(self, cart):
        items = []
        for item in cart:
            items.append(
                {
                    "book_id": item["book"].id,
                    "title": item["title"],
                    "quantity": item["quantity"],
                    "price": item["price"],
                    "total_price": item["total_price"],
                }
            )
        return {
            "items": items,
            "total_price": cart.get_total_price(),
            "total_items": len(cart),
        }

    def list(self, request):
        cart = Cart(request)
        serializer = CartSerializer(self._get_cart_data(cart))
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def add(self, request):
        serializer = CartAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from shop.models import Book

        book = Book.objects.get(id=serializer.validated_data["book_id"])
        cart = Cart(request)
        cart.add(book=book, quantity=serializer.validated_data["quantity"])
        return Response(self._get_cart_data(cart), status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def remove(self, request):
        book_id = request.data.get("book_id")
        if not book_id:
            return Response({"error": "book_id required"}, status=status.HTTP_400_BAD_REQUEST)
        from shop.models import Book

        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)
        cart = Cart(request)
        cart.remove(book)
        return Response(self._get_cart_data(cart))

    @action(detail=False, methods=["post"])
    def clear(self, request):
        cart = Cart(request)
        cart.clear()
        return Response({"message": "Cart cleared"}, status=status.HTTP_200_OK)
