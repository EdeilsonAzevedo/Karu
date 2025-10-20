from auditlog.models import AuditlogHistoryField
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    history = AuditlogHistoryField()
    class UserType(models.TextChoices):
        GESTOR = "gestor", _("Gestor")
        PROFISSIONAL_SAUDE = "profissional_saude", _("Profissional de Saúde")
        PAIS = "pais", _("Pais/Responsáveis")

    user_type = models.CharField(
        max_length=32,
        choices=UserType.choices,
        default=UserType.PAIS,
    )


class GestorProfile(models.Model):
    history = AuditlogHistoryField()
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="gestor"
    )
    cpf = models.CharField(max_length=11, unique=True)
    telefone = models.CharField(max_length=20, blank=True)
    unidade = models.CharField(max_length=120)
    cargo = models.CharField(max_length=100, blank=True)
    departamento = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} · CPF {self.cpf} · {self.unidade}"


class ProfissionalSaudeProfile(models.Model):
    history = AuditlogHistoryField()
    class Categoria(models.TextChoices):
        MEDICO = "Médico", _("Médico")
        ENFERMEIRO = "Enfermeiro", _("Enfermeiro")
        FONOAUDIOLOGO = "Fonoaudiólogo", _("Fonoaudiólogo")
        FISIOTERAPEUTA = "Fisioterapeuta", _("Fisioterapeuta")
        NUTRICIONISTA = "Nutricionista", _("Nutricionista")
        PSICOLOGO = "Psicólogo", _("Psicólogo")
        OUTRO = "Outro", _("Outro")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profissional"
    )
    cpf = models.CharField(max_length=11, unique=True)
    categoria = models.CharField(max_length=20, choices=Categoria.choices)
    especialidade = models.CharField(max_length=120, blank=True)
    conselho = models.CharField(max_length=20, blank=True, null=True)
    numero_registro = models.CharField(max_length=30, blank=True, null=True)
    unidade = models.CharField(max_length=120)
    telefone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["conselho", "numero_registro"],
                name="unique_conselho_registro_when_present",
                condition=Q(conselho__isnull=False, numero_registro__isnull=False),
            )
        ]

    def __str__(self):
        reg = (
            f"{self.conselho}-{self.numero_registro}"
            if self.conselho and self.numero_registro
            else "s/ reg."
        )
        return f"{self.user.username} · {self.categoria} · {reg} · {self.unidade}"


class PaisProfile(models.Model):
    history = AuditlogHistoryField()
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pais"
    )
    cpf = models.CharField(max_length=11, unique=True)
    telefone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} · CPF {self.cpf}"


class Filho(models.Model):
    pais = models.ForeignKey(PaisProfile, on_delete=models.CASCADE, related_name="filhos")
    nome = models.CharField(max_length=100)
    data_nascimento = models.DateField()

    def __str__(self) -> str:
        return f"{self.nome} ({self.pais.user.username})"
