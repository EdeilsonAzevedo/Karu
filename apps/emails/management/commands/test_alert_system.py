from django.core.management.base import BaseCommand
from apps.emails.tasks import send_test_alert, check_critical_warning_signs

class Command(BaseCommand):
    help = 'Testa o sistema de alertas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['email', 'check', 'all'],
            default='all',
            help='Tipo de teste: email (teste de email), check (verificação de sinais), all (ambos)'
        )
    
    def handle(self, *args, **options):
        test_type = options['type']
        
        if test_type in ['email', 'all']:
            self.stdout.write("Enviando email de teste...")
            result = send_test_alert.delay()
            self.stdout.write(
                self.style.SUCCESS('Email de teste enviado para a fila!')
            )
        
        if test_type in ['check', 'all']:
            self.stdout.write("Verificando sinais críticos...")
            result = check_critical_warning_signs.delay()
            self.stdout.write(
                self.style.SUCCESS('Verificação de sinais enviada para a fila!')
            )