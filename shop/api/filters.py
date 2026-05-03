import django_filters
from shop.models import Book, Order


class BookFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    author = django_filters.CharFilter(field_name='author', lookup_expr='icontains')
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')

    class Meta:
        model = Book
        fields = ['category', 'author', 'title', 'min_price', 'max_price', 'in_stock']

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)
        return queryset.filter(stock=0)


class OrderFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Order.STATUS_CHOICES)
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Order
        fields = ['status', 'created_after', 'created_before']
