import uuid

from django.db import models


class BaseModel(models.Model):
    """
    Modelo base para todas as tabelas do sistema.
    Define campos comuns e comportamentos padrão.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Data/hora em que o registro foi criado"
    )

    updated_at = models.DateTimeField(
        auto_now_add=True, help_text="Data/hora da ultima atualização"
    )
    is_activate = models.BooleanField(default=True, help_text="Indica se o registro está ativo")

    class Meta:
        abstract = True
        ordering = ["-created_at"]
