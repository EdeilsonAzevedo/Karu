from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Filho, GestorProfile, PaisProfile, ProfissionalSaudeProfile, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (("Tipo de Usuário", {"fields": ("user_type",)}),)
    list_display = ("username", "email", "user_type", "is_staff", "is_superuser")


admin.site.register(GestorProfile)
admin.site.register(ProfissionalSaudeProfile)
admin.site.register(PaisProfile)
admin.site.register(Filho)
