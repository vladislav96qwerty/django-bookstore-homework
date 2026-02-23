from django.contrib import admin
from django.db.models import Count
from .models import Book, Category


class BookInline(admin.TabularInline):
    model = Book
    extra = 1
    fields = ("title", "author", "price", "stock")
    show_change_link = True


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "books_count")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [BookInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_books_count=Count("books"))

    @admin.display(description="Количество книг", ordering="_books_count")
    def books_count(self, obj):
        return obj._books_count


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "price", "stock", "created_at")
    list_filter = ("category", "author", "created_at")
    search_fields = ("title", "author", "description")
    list_editable = ("price", "stock")
    autocomplete_fields = ("category",)