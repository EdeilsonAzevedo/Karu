import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.models import (
    GestorProfile,
    PaisProfile,
    ProfissionalSaudeProfile,
)

User = get_user_model()


def payload_gestor():
    return {
        "name": "Gestor Municipal",
        "cpf": "22222222222",
        "email": "gestor.novo@example.com",
        "phone": "(11) 98888-7777",
        "unit": "UBS Centro",
        "role_title": "Gestor Local",
        "temp_password": "Senha@1234",
        "temp_password2": "Senha@1234",
        "status": "Ativo",
    }


def payload_profissional():
    return {
        "name": "Dra Ana Maria",
        "cpf": "33333333333",
        "category": "Médico",
        "specialty": "Pediatria",
        "council": "CRM",
        "reg_number": "123456",
        "unit": "UBS Centro",
        "email": "ana.crm@example.com",
        "phone": "(11) 97777-6666",
        "temp_password": "Senha@1234",
        "temp_password2": "Senha@1234",
        "status": "Ativo",
    }


def payload_pais():
    return {
        "name": "Carlos Responsável",
        "cpf": "44444444444",
        "email": "carlos.pais@example.com",
        "phone": "(11) 96666-5555",
        "temp_password": "Senha@1234",
        "temp_password2": "Senha@1234",
        "status": "Ativo",
    }


@pytest.mark.django_db
def test_signup_gestor_get_200_para_superuser(client_logged_superuser):
    url = reverse("accounts:signup_gestor")
    resp = client_logged_superuser.get(url)
    assert resp.status_code == 200


@pytest.mark.django_db
def test_signup_gestor_get_302_para_nao_superuser(client):
    url = reverse("accounts:signup_gestor")
    resp = client.get(url)
    assert resp.status_code == 302
    assert reverse("login") in resp.url


@pytest.mark.django_db
def test_signup_gestor_post_sucesso_cria_user_profile_e_redirect(
    client_logged_superuser, ensure_groups
):
    url = reverse("accounts:signup_gestor")
    data = payload_gestor()
    resp = client_logged_superuser.post(url, data)
    assert resp.status_code == 302
    assert resp.url == reverse("home")

    u = User.objects.get(username=data["cpf"])
    assert u.first_name == data["name"]
    assert u.is_active is True

    assert u.groups.filter(name="gestores").exists()

    gp = GestorProfile.objects.get(user=u)
    assert gp.cpf == data["cpf"]
    assert gp.unidade == data["unit"]


@pytest.mark.django_db
def test_signup_gestor_post_invalido_mostra_erros(client_logged_superuser):
    url = reverse("accounts:signup_gestor")
    data = payload_gestor()
    data["cpf"] = "123"
    data["temp_password2"] = "xyz"
    resp = client_logged_superuser.post(url, data)
    assert resp.status_code == 200
    assert User.objects.filter(username="123").count() == 0


@pytest.mark.django_db
def test_signup_profissional_get_200_para_gestor(client_logged_gestor):
    url = reverse("accounts:signup_profissional")
    resp = client_logged_gestor.get(url)
    assert resp.status_code == 200


@pytest.mark.django_db
def test_signup_profissional_get_302_para_nao_gestor(client):
    url = reverse("accounts:signup_profissional")
    resp = client.get(url)
    assert resp.status_code == 302
    assert reverse("login") in resp.url


@pytest.mark.django_db
def test_signup_profissional_post_sucesso_cria_user_profile_e_redirect(
    client_logged_gestor, ensure_groups
):
    url = reverse("accounts:signup_profissional")
    data = payload_profissional()
    resp = client_logged_gestor.post(url, data)
    assert resp.status_code == 302
    assert resp.url == reverse("home")

    u = User.objects.get(username=data["cpf"])
    assert u.first_name == data["name"]
    assert u.is_active is True

    assert u.groups.filter(name="profissionais_saude").exists()

    pp = ProfissionalSaudeProfile.objects.get(user=u)
    assert pp.cpf == data["cpf"]
    assert pp.categoria == data["category"]
    assert pp.conselho == data["council"]
    assert pp.numero_registro == data["reg_number"]


@pytest.mark.django_db
def test_signup_profissional_post_invalido_mostra_erros(client_logged_gestor):
    url = reverse("accounts:signup_profissional")
    data = payload_profissional()
    data["cpf"] = "abc"
    data["temp_password2"] = "Senha@999"
    resp = client_logged_gestor.post(url, data)
    assert resp.status_code == 200
    assert not User.objects.filter(username="abc").exists()


@pytest.mark.django_db
def test_signup_pais_get_200_para_gestor(client_logged_gestor):
    url = reverse("accounts:signup_pais")
    resp = client_logged_gestor.get(url)
    assert resp.status_code == 200


@pytest.mark.django_db
def test_signup_pais_get_302_para_nao_gestor(client):
    url = reverse("accounts:signup_pais")
    resp = client.get(url)
    assert resp.status_code == 302
    assert reverse("login") in resp.url


@pytest.mark.django_db
def test_signup_pais_post_sucesso_cria_user_profile_e_redirect(client_logged_gestor, ensure_groups):
    url = reverse("accounts:signup_pais")
    data = payload_pais()
    resp = client_logged_gestor.post(url, data)
    assert resp.status_code == 302
    assert resp.url == reverse("home")

    u = User.objects.get(username=data["cpf"])
    assert u.first_name == data["name"]
    assert u.is_active is True
    assert u.groups.filter(name="pais").exists()
    pr = PaisProfile.objects.get(user=u)
    assert pr.cpf == data["cpf"]


@pytest.mark.django_db
def test_signup_pais_post_invalido_mostra_erros(client_logged_gestor):
    url = reverse("accounts:signup_pais")
    data = payload_pais()
    data["cpf"] = "999"
    data["temp_password2"] = "noop"
    resp = client_logged_gestor.post(url, data)
    assert resp.status_code == 200
    assert not User.objects.filter(username="999").exists()
