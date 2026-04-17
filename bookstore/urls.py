from django.contrib import admin
from django.urls import path, include
from django.views.i18n import set_language

urlpatterns = [
    path('admin/', admin.site.urls),
    path('set-language/', set_language, name='set_language'),
    path('', include('shop.urls')),
]