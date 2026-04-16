from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Name"))
    slug = models.SlugField(max_length=120, unique=True, blank=True, verbose_name=_("Slug"))

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Book(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="books",
        verbose_name=_("Category"),
    )
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    author = models.CharField(max_length=255, verbose_name=_("Author"))
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Price"),
    )
    description = models.TextField(blank=True, verbose_name=_("Description"))
    stock = models.PositiveIntegerField(default=0, verbose_name=_("Stock"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))

    class Meta:
        verbose_name = _("Book")
        verbose_name_plural = _("Books")
        ordering = ["title"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["author"]),
            models.Index(fields=["price"]),
        ]

    def __str__(self):
        return f"{self.title} — {self.author}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',   _('Pending')),
        ('paid',      _('Paid')),
        ('cancelled', _('Cancelled')),
    ]
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='orders', verbose_name=_('User')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated at'))
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name=_('Status')
    )
    stripe_session_id = models.CharField(
        max_length=255, blank=True, verbose_name=_('Stripe Session ID')
    )

    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.id} — {self.user}'

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items', verbose_name=_('Order')
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name=_('Book'))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_('Quantity'))
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_('Price')
    )

    class Meta:
        verbose_name = _('Order item')
        verbose_name_plural = _('Order items')

    def __str__(self):
        return f'{self.book.title} x {self.quantity}'

    def get_total_price(self):
        return self.price * self.quantity
