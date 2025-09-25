from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.


class User(AbstractUser):
    class UserType(models.TextChoices):
        GESTOR = "gestor", _("Gestor")
        PROFISSIONAL_SAUDE = "profissional_saude", _("Profissional de Saúde")
        PAIS = "pais", _("Pais/Responsáveis")

    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.PAIS,
    )


class GestorProfile(models.Model):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="gestor")
    departamento = models.CharField(max_length=100, blank=True)
    cargo = models.CharField(max_length=100, blank=True)


class ProfissionalSaudeProfile(models.Model):
    user = models.OneToOneField(
        "accounts.User", on_delete=models.CASCADE, related_name="profissional"
    )
    especialidade = models.CharField(max_length=100)
    crm = models.CharField(max_length=30, unique=True)


class PaisProfile(models.Model):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="pais")
    telefone = models.CharField(max_length=20, blank=True)


class Filho(models.Model):
    pais = models.ForeignKey(PaisProfile, on_delete=models.CASCADE, related_name="filhos")
    nome = models.CharField(max_length=100)
    data_nascimento = models.DateField()
