from django import forms
from .models import Book

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['category', 'title', 'author', 'price', 'description', 'stock']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter book title'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter author name'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
        }
