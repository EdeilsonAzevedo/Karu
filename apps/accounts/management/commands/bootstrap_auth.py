from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from apps.accounts.models import User


class Command(BaseCommand):
    help = "Cria grupos e permissão base"

    def handle(self, *args, **kwargs):
        gestores, _ = Group.objects.get_or_create(name="gestores")
        Group.objects.get_or_create(name="profissionais_saude")
        Group.objects.get_or_create(name="pais")

        ct = ContentType.objects.get_for_model(User)
        perm, _ = Permission.objects.get_or_create(
            codename="can_manage_all_users",
            name="Can manage all users",
            content_type=ct,
        )
        gestores.permissions.add(perm)
        self.stdout.write(self.style.SUCCESS("Roles OK"))
