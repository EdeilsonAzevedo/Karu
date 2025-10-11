from django.core.management.base import BaseCommand

from apps.emails.tasks import send_test_alert


class Command(BaseCommand):
    help = "Envia alerta de teste para verificar configuração do sistema"

    def handle(self, *args, **options):
        send_test_alert.delay()
        self.stdout.write(self.style.SUCCESS("Alerta de teste enviado para a fila!"))
