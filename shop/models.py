from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    slug = models.SlugField(max_length=120, unique=True, blank=True, verbose_name="Slug")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Если slug пустой - создаем автоматически из name
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Book(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="books",
        verbose_name="Категория"
    )
    title = models.CharField(max_length=255, verbose_name="Название")
    author = models.CharField(max_length=255, verbose_name="Автор")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Цена"
    )
    description = models.TextField(blank=True, verbose_name="Описание")
    stock = models.PositiveIntegerField(default=0, verbose_name="Остаток")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Книга"
        verbose_name_plural = "Книги"
        ordering = ["title"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["author"]),
            models.Index(fields=["price"]),
        ]

    def __str__(self):
        return f"{self.title} — {self.author}"