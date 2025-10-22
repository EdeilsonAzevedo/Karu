import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()


@pytest.fixture
def ensure_groups(db):
    """Cria os grupos necessários e retorna dict com instâncias."""
    groups = {}
    for name in ["gestores", "profissionais_saude", "pais"]:
        groups[name], _ = Group.objects.get_or_create(name=name)
    return groups


@pytest.fixture
def superuser(db):
    """Superuser (pode tudo). Username = CPF."""
    u = User.objects.create_user(
        username="99999999999",
        first_name="Admin",
        email="admin@example.com",
        password="Admin@1234",
        is_superuser=True,
        is_staff=True,
        is_active=True,
    )
    return u


@pytest.fixture
def gestor_user(db, ensure_groups):
    """Usuário no grupo gestores (pode criar prof/pais)."""
    u = User.objects.create_user(
        username="11111111111",
        first_name="Gestor",
        email="gestor@example.com",
        password="Gestor@1234",
        is_active=True,
    )
    u.groups.add(ensure_groups["gestores"])
    return u


@pytest.fixture
def client_logged_superuser(client, superuser):
    client.login(username=superuser.username, password="Admin@1234")
    return client


@pytest.fixture
def client_logged_gestor(client, gestor_user):
    client.login(username=gestor_user.username, password="Gestor@1234")
    return client
