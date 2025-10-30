from datetime import date

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from apps.email.models import EmailAlert
from apps.patients.models import Patient


class Command(BaseCommand):
    help = "Testa o design do template de email"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🎨 TESTANDO DESIGN DO EMAIL"))
        self.stdout.write("=" * 50)

        # Buscar um alerta recente ou criar dados de exemplo
        try:
            alerta = (
                EmailAlert.objects.filter(alert_type="weight_loss")
                .select_related("patient")
                .first()
            )

            if not alerta:
                self.stdout.write(
                    self.style.WARNING("⚠️  Nenhum alerta encontrado. Criando exemplo...")
                )
                alerta = self.criar_exemplo_alerta()

            # Renderizar template
            html_content = render_to_string(
                "email/alert_template.html",
                {
                    "alert": alerta,
                    "patient": alerta.patient,
                },
            )

            # Salvar para visualização
            with open("email_preview.html", "w", encoding="utf-8") as f:
                f.write(html_content)

            self.stdout.write(self.style.SUCCESS("✅ Template renderizado com sucesso!"))
            self.stdout.write("📁 Arquivo salvo: email_preview.html")
            self.stdout.write("🌐 Abra este arquivo no navegador para visualizar o design")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro: {e}"))

    def criar_exemplo_alerta(self):
        """Cria um alerta de exemplo para teste"""
        paciente, _ = Patient.objects.get_or_create(
            first_name="Maria",
            last_name="Silva Teste",
            defaults={
                "date_of_birth": date(2024, 1, 15),
                "sex": "F",
                "gestational_age_weeks": 32,
                "birth_weight": 2800,
                "guardian_name": "Ana Silva",
                "contact_phone": "(11) 99999-9999",
                "is_active": True,
            },
        )

        alerta = EmailAlert(
            patient=paciente,
            alert_type="weight_loss",
            title="⚠️ ALERTA: Perda de Peso Significativa - Maria Silva Teste",
            message="""O paciente apresentou perda de peso significativa em consultas consecutivas:

📊 HISTÓRICO:
• 01/03/2024: 3200g
• 08/03/2024: 3150g (-50g, -1.56%)
• 15/03/2024: 3100g (-50g, -1.59%)

🚨 CRITÉRIOS ATINGIDOS:
- 2 eventos de perda consecutiva
- Perdas superiores a 30g
- Percentual acima de 1.0%

Recomenda-se contato imediato com a família.""",
            recipient_email="tjesuinodasilva@gmail.com",
        )

        return alerta
