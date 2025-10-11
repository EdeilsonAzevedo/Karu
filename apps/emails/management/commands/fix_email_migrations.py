import glob
import os

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Corrige completamente as migrações do app emails"

    def handle(self, *args, **options):
        self.stdout.write("🛠️  CORRIGINDO MIGRAÇÕES DO APP EMAILS...")

        # 1. Remove TODAS as migrações existentes
        migrations_dir = "apps/emails/migrations"
        migration_files = glob.glob(os.path.join(migrations_dir, "*.py"))

        for file in migration_files:
            if "__init__.py" not in file:
                try:
                    os.remove(file)
                    self.stdout.write(f"🗑️  Removido: {file}")
                except OSError as e:
                    self.stdout.write(f"⚠️  Não pude remover {file}: {e}")

        # 2. Garante que existe __init__.py
        init_file = os.path.join(migrations_dir, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("")
            self.stdout.write("📁 Criado __init__.py")

        # 3. Cria novas migrações
        self.stdout.write("📦 Criando novas migrações...")
        try:
            call_command("makemigrations", "emails")
            self.stdout.write(self.style.SUCCESS("✅ Migrações criadas com sucesso"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro ao criar migrações: {e}"))
            return

        # 4. Aplica migrações
        self.stdout.write("🚀 Aplicando migrações...")
        try:
            call_command("migrate", "emails")
            self.stdout.write(self.style.SUCCESS("✅ Migrações aplicadas com sucesso"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro ao aplicar migrações: {e}"))
