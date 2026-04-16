from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Book


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['category', 'title', 'author', 'price', 'description', 'stock']
        widgets = {
            'category':    forms.Select(attrs={'class': 'form-select'}),
            'title':       forms.TextInput(attrs={
                               'class': 'form-control',
                               'placeholder': _('Enter book title'),
                           }),
            'author':      forms.TextInput(attrs={
                               'class': 'form-control',
                               'placeholder': _('Enter author name'),
                           }),
            'price':       forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'stock':       forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'category':    _('Category'),
            'title':       _('Title'),
            'author':      _('Author'),
            'price':       _('Price'),
            'description': _('Description'),
            'stock':       _('Stock'),
        }
        error_messages = {
            'title':  {'required': _('Title is required.')},
            'author': {'required': _('Author is required.')},
            'price':  {'required': _('Price is required.')},
        }
