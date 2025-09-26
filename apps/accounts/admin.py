from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Filho, GestorProfile, PaisProfile, ProfissionalSaudeProfile, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        *DjangoUserAdmin.fieldsets,
        ("Tipo de Usuário", {"fields": ("user_type",)}),
    )

    add_fieldsets = (
        *DjangoUserAdmin.add_fieldsets,
        ("Tipo de Usuário", {"fields": ("user_type",)}),
    )

    list_display = ("username", "email", "user_type", "is_staff", "is_superuser")
    list_filter = ("user_type", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")


admin.site.register(GestorProfile)
admin.site.register(ProfissionalSaudeProfile)
admin.site.register(PaisProfile)
admin.site.register(Filho)
