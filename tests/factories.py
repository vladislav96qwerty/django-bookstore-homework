import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User
from shop.models import Category, Book, Order, OrderItem


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "password123")


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.LazyAttribute(lambda o: o.name.lower().replace(" ", "-"))


class BookFactory(DjangoModelFactory):
    class Meta:
        model = Book

    category = factory.SubFactory(CategoryFactory)
    title = factory.Sequence(lambda n: f"Book Title {n}")
    author = factory.Sequence(lambda n: f"Author {n}")
    price = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    stock = factory.Faker("random_int", min=0, max=100)
    description = factory.Faker("paragraph")


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    status = "pending"
    stripe_session_id = factory.Faker("uuid4")


class OrderItemFactory(DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    book = factory.SubFactory(BookFactory)
    quantity = factory.Faker("random_int", min=1, max=5)
    price = factory.LazyAttribute(lambda o: o.book.price)
