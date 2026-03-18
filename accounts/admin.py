from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "created_at", "updated_at")
    search_fields = ("user__username", "user__email", "phone_number")
    list_select_related = ("user",)

