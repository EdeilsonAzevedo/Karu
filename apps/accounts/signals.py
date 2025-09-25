from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import GestorProfile, PaisProfile, ProfissionalSaudeProfile, User


def ensure_default_groups():
    for name in ["gestores", "profissionais_saude", "pais"]:
        Group.objects.get_or_create(name=name)

    gestores = Group.objects.get(name="gestores")
    ct = ContentType.objects.get_for_model(User)
    perm, _ = Permission.objects.get_or_create(
        codename="can_manage_all_users",
        name="Can manage all users",
        content_type=ct,
    )
    gestores.permissions.add(perm)


@receiver(post_save, sender=User)
def create_profile_and_group(sender, instance: User, created, **kwargs):
    if not created:
        return
    ensure_default_groups()

    if instance.user_type == User.UserType.GESTOR:
        GestorProfile.objects.create(user=instance)
        group = Group.objects.get(name="gestores")
    elif instance.user_type == User.UserType.PROFISSIONAL_SAUDE:
        ProfissionalSaudeProfile.objects.create(user=instance)
        group = Group.objects.get(name="profissionais_saude")
    else:
        PaisProfile.objects.create(user=instance)
        group = Group.objects.get(name="pais")

    instance.groups.add(group)
