from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.email.models import EmailAlert
from apps.patients.models import ConsultationRecord, Patient, Record


class Command(BaseCommand):
    help = "Testa o sistema de alertas de email com dados fictícios"

    def add_arguments(self, parser):
        parser.add_argument(
            "--tipo",
            type=str,
            choices=["peso", "consulta", "todos"],
            default="todos",
            help="Tipo de alerta a testar: peso, consulta ou todos",
        )

    def handle(self, *args, **options):
        tipo = options["tipo"]

        self.stdout.write(self.style.SUCCESS("🚀 INICIANDO TESTE DO SISTEMA DE ALERTAS"))
        self.stdout.write("=" * 60)

        # Criar paciente de teste
        paciente = self.criar_paciente_teste()

        if tipo in ["peso", "todos"]:
            self.testar_alerta_peso(paciente)

        if tipo in ["consulta", "todos"]:
            self.testar_alerta_consulta(paciente)

        self.mostrar_resultados()

    def criar_paciente_teste(self):
        """Cria um paciente para testes"""
        paciente, created = Patient.objects.get_or_create(
            first_name="Maria",
            last_name="Teste Alerta",
            defaults={
                "date_of_birth": date(2024, 1, 15),
                "sex": "F",
                "gestational_age_weeks": 32,
                "birth_weight": 2800,
                "guardian_name": "Ana Silva Teste",
                "contact_phone": "(11) 99999-9999",
                "is_active": True,
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS("✅ Paciente de teste criado: Maria Teste Alerta"))
        else:
            self.stdout.write(self.style.WARNING("⚠️  Paciente de teste já existe"))

        return paciente

    def testar_alerta_peso(self, paciente):
        """Testa alerta de perda de peso"""
        self.stdout.write("\n📉 TESTANDO ALERTA DE PERDA DE PESO")
        self.stdout.write("-" * 40)

        # Criar consultas com perda de peso significativa
        datas_peso = [
            (date(2024, 3, 1), 3200),  # Base
            (date(2024, 3, 8), 3150),  # -50g (-1.56%)
            (date(2024, 3, 15), 3100),  # -50g (-1.59%) - ATINGE CRITÉRIO
            (date(2024, 3, 22), 3050),  # -50g (-1.61%) - ATINGE CRITÉRIO
        ]

        for i, (data, peso) in enumerate(datas_peso):
            record, _ = Record.objects.get_or_create(
                patient=paciente,
                date=data,
                defaults={
                    "record_type": "consultation",
                    "professional": "Enfermeiro Teste",
                    "location": "UBS Teste",
                },
            )

            ConsultationRecord.objects.get_or_create(
                record=record, defaults={"weight": peso, "length": 48 + i, "head_circumference": 34}
            )

            self.stdout.write(f"   📅 {data.strftime('%d/%m')}: {peso}g")

        self.stdout.write(self.style.SUCCESS("   ✅ Consultas de teste criadas"))

        # Executar verificação de alertas
        try:
            from apps.email.tasks import check_weight_loss_alerts

            check_weight_loss_alerts.delay()
            self.stdout.write(self.style.SUCCESS("   ✅ Task de verificação de peso agendada"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Erro na task: {e}"))

    def testar_alerta_consulta(self, paciente):
        """Testa alerta de consulta atrasada"""
        self.stdout.write("\n📅 TESTANDO ALERTA DE CONSULTA ATRASADA")
        self.stdout.write("-" * 40)

        # Criar consulta com data passada
        data_passada = timezone.now().date() - timedelta(days=5)

        record, _ = Record.objects.get_or_create(
            patient=paciente,
            date=data_passada - timedelta(days=30),  # Consulta anterior
            defaults={
                "record_type": "consultation",
                "professional": "Médico Teste",
                "location": "Hospital Teste",
            },
        )

        ConsultationRecord.objects.get_or_create(
            record=record,
            defaults={
                "weight": 3100,
                "length": 49,
                "head_circumference": 35,
                "next_appointment_date": data_passada,  # Data já passou
            },
        )

        self.stdout.write(f"   📅 Consulta marcada para: {data_passada.strftime('%d/%m/%Y')}")
        self.stdout.write(
            f"   ⏰ Dias de atraso: {(timezone.now().date() - data_passada).days} dias"
        )
        self.stdout.write(self.style.SUCCESS("   ✅ Consulta atrasada criada"))

        # Executar verificação
        try:
            from apps.email.tasks import check_missed_appointments

            check_missed_appointments.delay()
            self.stdout.write(self.style.SUCCESS("   ✅ Task de consultas atrasadas agendada"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Erro na task: {e}"))

    def mostrar_resultados(self):
        """Mostra resultados dos testes"""
        self.stdout.write("\n📊 RESULTADOS DOS TESTES")
        self.stdout.write("-" * 40)

        # Verificar alertas criados
        alertas = EmailAlert.objects.all().order_by("-created_at")[:5]

        if alertas:
            self.stdout.write(self.style.SUCCESS(f"   📨 Alertas criados: {alertas.count()}"))
            for alerta in alertas:
                self.stdout.write(f"      • {alerta.title}")
                self.stdout.write(f"        Status: {alerta.get_status_display()}")
                self.stdout.write(f"        Paciente: {alerta.patient}")
        else:
            self.stdout.write(self.style.WARNING("   ⚠️  Nenhum alerta criado ainda"))

        self.stdout.write("\n🔍 PRÓXIMOS PASSOS:")
        self.stdout.write("   1. Verifique o terminal do Celery Worker")
        self.stdout.write("   2. Verifique o terminal do Celery Beat")
        self.stdout.write("   3. Verifique sua caixa de email")
        self.stdout.write("   4. Verifique o admin em /admin/email/emailalert/")

        self.stdout.write(self.style.SUCCESS("\n🎯 TESTE CONCLUÍDO!"))
