import os
import django
import random

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore.settings')
django.setup()

from shop.models import Category, Book

def populate():
    # Create Categories
    categories = ['Fiction', 'Technology', 'Science', 'History', 'Biography', 'Art']
    category_objs = []
    for cat_name in categories:
        obj, created = Category.objects.get_or_create(name=cat_name)
        category_objs.append(obj)
        print(f"Category '{cat_name}' {'created' if created else 'already exists'}")

    # Create Books
    book_titles = [
        "The Great Gatsby", "Clean Code", "Sapiens", "Steve Jobs", "Thinking, Fast and Slow",
        "Dune", "1984", "The Hobbit", "Python Crash Course", "Deep Learning",
        "The Art of War", "Guns, Germs, and Steel", "The Selfish Gene", "The Innovators",
        "Educated", "Becoming", "Zero to One", "Hooked", "Blink", "Outliers",
        "The Alchemist", "Foundation", "Neuromancer", "Ready Player One", "Snow Crash"
    ]
    authors = ["F. Scott Fitzgerald", "Robert C. Martin", "Yuval Noah Harari", "Walter Isaacson", "Daniel Kahneman", "Frank Herbert", "George Orwell", "J.R.R. Tolkien", "Eric Matthes", "Ian Goodfellow", "Sun Tzu", "Jared Diamond", "Richard Dawkins", "Tara Westover", "Michelle Obama", "Peter Thiel", "Nir Eyal", "Malcolm Gladwell", "Paulo Coelho", "Isaac Asimov", "William Gibson", "Ernest Cline", "Neal Stephenson"]

    for i, title in enumerate(book_titles):
        author = authors[i % len(authors)]
        category = random.choice(category_objs)
        price = round(random.uniform(10.0, 100.0), 2)
        stock = random.randint(1, 50)
        
        book, created = Book.objects.get_or_create(
            title=title,
            author=author,
            defaults={
                'category': category,
                'price': price,
                'stock': stock,
                'description': f"This is a sample description for '{title}' by {author}."
            }
        )
        if created:
            print(f"Book '{title}' created")
        else:
            print(f"Book '{title}' already exists")

if __name__ == '__main__':
    print("Starting population script...")
    populate()
    print("Population complete!")
