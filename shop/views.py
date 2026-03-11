from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from .models import Book
from .forms import BookForm

class BookListView(ListView):
    model = Book
    template_name = 'shop/book_list.html'
    context_object_name = 'books'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | 
                Q(author__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context

class BookDetailView(DetailView):
    model = Book
    template_name = 'shop/book_detail.html'
    context_object_name = 'book'

class BookCreateView(CreateView):
    model = Book
    form_class = BookForm
    template_name = 'shop/book_form.html'
    success_url = reverse_lazy('shop:book_list')

class BookUpdateView(UpdateView):
    model = Book
    form_class = BookForm
    template_name = 'shop/book_form.html'
    
    def get_success_url(self):
        return reverse_lazy('shop:book_detail', kwargs={'pk': self.object.pk})

class BookDeleteView(DeleteView):
    model = Book
    template_name = 'shop/book_confirm_delete.html'
    success_url = reverse_lazy('shop:book_list')
