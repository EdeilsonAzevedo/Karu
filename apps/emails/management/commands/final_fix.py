import glob
import os

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Correção final do sistema de alertas"

    def handle(self, *args, **options):
        self.stdout.write("🔧 CORREÇÃO FINAL DO SISTEMA")

        # 1. Remove migrações do emails
        migrations = glob.glob("apps/emails/migrations/0*.py")
        for mig in migrations:
            os.remove(mig)
            self.stdout.write(f"🗑️  Removido: {mig}")

        # 2. Cria novas migrações
        self.stdout.write("📦 Criando migrações...")
        call_command("makemigrations", "emails")

        # 3. Aplica migrações
        self.stdout.write("🚀 Aplicando migrações...")
        call_command("migrate", "emails")

        self.stdout.write(self.style.SUCCESS("✅ CORREÇÃO CONCLUÍDA!"))
