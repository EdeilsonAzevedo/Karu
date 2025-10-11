import logging

from django.core.management.base import BaseCommand

from apps.emails.tasks import create_warning_alert
from apps.patients.models import ClinicalWarningSign

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Dispara alertas para sinais críticos existentes"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=2, help="Número de alertas para disparar")

    def handle(self, *args, **options):
        count = options["count"]

        # Busca os sinais mais recentes
        warning_signs = ClinicalWarningSign.objects.filter(is_present=True).order_by("-created_at")[
            :count
        ]

        self.stdout.write(f"Disparando {warning_signs.count()} alertas...")

        for warning_sign in warning_signs:
            self.stdout.write(
                f"→ {warning_sign.record.patient.first_name}: {warning_sign.get_type_display()}"
            )

            # Dispara o alerta
            create_warning_alert.delay(warning_sign.id)

        self.stdout.write(
            self.style.SUCCESS(f"✅ {warning_signs.count()} alertas enviados para a fila!")
        )
        self.stdout.write("Verifique o terminal do Celery para ver o processamento.")
