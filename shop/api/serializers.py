from rest_framework import serializers
from shop.models import Book, Category, Order, OrderItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class BookSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        write_only=True,
    )

    class Meta:
        model = Book
        fields = [
            "id",
            "category",
            "category_id",
            "title",
            "author",
            "price",
            "description",
            "stock",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class OrderItemSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(),
        source="book",
        write_only=True,
    )
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "book", "book_id", "quantity", "price", "total_price"]

    def get_total_price(self, obj):
        return obj.get_total_price()


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "status",
            "items",
            "total_price",
            "created_at",
            "updated_at",
            "stripe_session_id",
        ]
        read_only_fields = ["created_at", "updated_at", "stripe_session_id"]

    def get_total_price(self, obj):
        return obj.get_total_price()


class OrderCreateSerializer(serializers.ModelSerializer):
    """Used for creating orders with items."""

    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ["id", "status", "items"]

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            book = item_data["book"]
            OrderItem.objects.create(
                order=order,
                book=book,
                quantity=item_data["quantity"],
                price=item_data.get("price", book.price),
            )
        return order


# ── Cart serializers (session-based cart) ────────────────────────────────────


class CartItemSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()
    title = serializers.CharField()
    quantity = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)


class CartSerializer(serializers.Serializer):
    items = CartItemSerializer(many=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_items = serializers.IntegerField()


class CartAddSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate_book_id(self, value):
        if not Book.objects.filter(id=value).exists():
            raise serializers.ValidationError("Book not found.")
        return value
