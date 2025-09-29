from typing import TYPE_CHECKING

from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import AbstractUser, Group
from django.core import exceptions
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import transaction

from .models import GestorProfile, PaisProfile, ProfissionalSaudeProfile

User = get_user_model()

if TYPE_CHECKING:
    pass

cpf_validator = RegexValidator(r"^\d{11}$", "CPF deve conter 11 dígitos (somente números).")
phone_br_validator = RegexValidator(
    r"^(?:\+55\s?)?\(?\d{2}\)?\s?9\d{4}[- ]?\d{4}$",
    "Telefone inválido. Use DDD + celular (ex.: 11 9XXXX-XXXX).",
)


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def ensure_password(temp_password: str | None) -> str:
    """Gera/valida a senha conforme as regras do Django."""
    pwd = (temp_password or "").strip()
    if not pwd:
        import secrets
        import string

        alphabet = string.ascii_letters + string.digits + "@#-_"
        pwd = "".join(secrets.choice(alphabet) for _ in range(12))
    try:
        password_validation.validate_password(pwd)
    except exceptions.ValidationError as e:
        raise ValidationError({"temp_password": list(e.messages)})
    return pwd


class LoginForm(AuthenticationForm):
    """Mantido caso você queira customizar depois."""

    pass


class GestorSignupForm(forms.Form):
    name = forms.CharField(label="Nome completo", required=True)
    cpf = forms.CharField(label="CPF", required=True, validators=[cpf_validator])
    email = forms.EmailField(label="E-mail", required=True)
    phone = forms.CharField(label="Telefone", required=False, validators=[phone_br_validator])
    unit = forms.CharField(label="Unidade (UBS)", required=True)
    role_title = forms.CharField(label="Cargo", required=False)
    temp_password = forms.CharField(label="Senha temporária", required=False)
    status = forms.ChoiceField(
        label="Status", choices=[("Ativo", "Ativo"), ("Inativo", "Inativo")], required=False
    )

    def clean_email(self):
        return normalize_email(self.cleaned_data["email"])

    def clean_cpf(self):
        cpf = self.cleaned_data["cpf"]
        if User.objects.filter(username=cpf).exists():
            raise ValidationError("Já existe um usuário com este CPF.")
        if GestorProfile.objects.filter(cpf=cpf).exists():
            raise ValidationError("Já existe um gestor com este CPF.")
        return cpf

    def clean_phone(self):
        v = (self.cleaned_data.get("phone") or "").strip()
        if not v:
            return ""
        phone_br_validator(v)
        return v

    @transaction.atomic
    def save(self) -> AbstractUser:
        name = self.cleaned_data["name"].strip()
        cpf = self.cleaned_data["cpf"]
        email = self.cleaned_data["email"]
        phone = (self.cleaned_data.get("phone") or "").strip()
        unit = self.cleaned_data["unit"].strip()
        cargo = (self.cleaned_data.get("role_title") or "Gestor Local").strip()
        active = (self.cleaned_data.get("status") or "Ativo") == "Ativo"
        raw_pw = ensure_password(self.cleaned_data.get("temp_password"))

        user = User(
            username=cpf,
            first_name=name,
            last_name="",
            email=email,
            is_active=active,
        )
        user.set_password(raw_pw)
        user.save()

        g, _ = Group.objects.get_or_create(name="gestores")
        user.groups.add(g)

        GestorProfile.objects.create(
            user=user,
            cpf=cpf,
            telefone=phone,
            unidade=unit,
            cargo=cargo,
        )
        return user


class ProfissionalSignupForm(forms.Form):
    name = forms.CharField(label="Nome completo", required=True)
    cpf = forms.CharField(label="CPF", required=True, validators=[cpf_validator])
    category = forms.ChoiceField(
        label="Categoria", choices=ProfissionalSaudeProfile.Categoria.choices, required=True
    )
    specialty = forms.CharField(label="Especialidade", required=False)
    council = forms.CharField(label="Conselho (CRM/COREN/CRP...)", required=False)
    reg_number = forms.CharField(label="Nº de registro", required=False)
    unit = forms.CharField(label="Unidade (UBS)", required=True)
    email = forms.EmailField(label="E-mail", required=True)
    phone = forms.CharField(label="Telefone", required=False, validators=[phone_br_validator])
    temp_password = forms.CharField(label="Senha temporária", required=False)
    status = forms.ChoiceField(
        label="Status", choices=[("Ativo", "Ativo"), ("Inativo", "Inativo")], required=False
    )

    def clean_email(self):
        return normalize_email(self.cleaned_data["email"])

    def clean_cpf(self):
        cpf = self.cleaned_data["cpf"]
        if User.objects.filter(username=cpf).exists():
            raise ValidationError("Já existe um usuário com este CPF.")
        if ProfissionalSaudeProfile.objects.filter(cpf=cpf).exists():
            raise ValidationError("Já existe um profissional com este CPF.")
        return cpf

    def clean_phone(self):
        v = (self.cleaned_data.get("phone") or "").strip()
        if not v:
            return ""
        phone_br_validator(v)
        return v

    def clean(self):
        cleaned = super().clean()
        council = (cleaned.get("council") or "").strip()
        reg = (cleaned.get("reg_number") or "").strip()
        if council and not reg:
            self.add_error("reg_number", "Informe o número de registro.")
        if reg and not council:
            self.add_error("council", "Informe o conselho (CRM/COREN/CRP...).")
        if council and reg:
            if ProfissionalSaudeProfile.objects.filter(
                conselho=council, numero_registro=reg
            ).exists():
                self.add_error(
                    "reg_number", "Já existe um profissional com este conselho + registro."
                )
        return cleaned

    @transaction.atomic
    def save(self) -> AbstractUser:
        name = self.cleaned_data["name"].strip()
        cpf = self.cleaned_data["cpf"]
        email = self.cleaned_data["email"]
        phone = (self.cleaned_data.get("phone") or "").strip()
        unit = self.cleaned_data["unit"].strip()
        active = (self.cleaned_data.get("status") or "Ativo") == "Ativo"
        raw_pw = ensure_password(self.cleaned_data.get("temp_password"))

        user = User(
            username=cpf,
            first_name=name,
            last_name="",
            email=email,
            is_active=active,
        )
        user.set_password(raw_pw)
        user.save()

        grp, _ = Group.objects.get_or_create(name="profissionais_saude")
        user.groups.add(grp)

        ProfissionalSaudeProfile.objects.create(
            user=user,
            cpf=cpf,
            categoria=self.cleaned_data["category"],
            especialidade=(self.cleaned_data.get("specialty") or "").strip(),
            conselho=(self.cleaned_data.get("council") or None) or None,
            numero_registro=(self.cleaned_data.get("reg_number") or None) or None,
            unidade=unit,
            telefone=phone,
        )
        return user


class PaisSignupForm(forms.Form):
    name = forms.CharField(label="Nome completo", required=True)
    cpf = forms.CharField(label="CPF", required=True, validators=[cpf_validator])
    email = forms.EmailField(label="E-mail", required=True)
    phone = forms.CharField(label="Telefone", required=False, validators=[phone_br_validator])
    temp_password = forms.CharField(label="Senha temporária", required=False)
    status = forms.ChoiceField(
        label="Status", choices=[("Ativo", "Ativo"), ("Inativo", "Inativo")], required=False
    )

    def clean_email(self):
        return normalize_email(self.cleaned_data["email"])

    def clean_cpf(self):
        cpf = self.cleaned_data["cpf"]
        if User.objects.filter(username=cpf).exists():
            raise ValidationError("Já existe um usuário com este CPF.")
        if PaisProfile.objects.filter(cpf=cpf).exists():
            raise ValidationError("Já existe um responsável com este CPF.")
        return cpf

    def clean_phone(self):
        v = (self.cleaned_data.get("phone") or "").strip()
        if not v:
            return ""
        phone_br_validator(v)
        return v

    @transaction.atomic
    def save(self) -> AbstractUser:
        name = self.cleaned_data["name"].strip()
        cpf = self.cleaned_data["cpf"]
        email = self.cleaned_data["email"]
        phone = (self.cleaned_data.get("phone") or "").strip()
        active = (self.cleaned_data.get("status") or "Ativo") == "Ativo"
        raw_pw = ensure_password(self.cleaned_data.get("temp_password"))

        user = User(
            username=cpf,
            first_name=name,
            last_name="",
            email=email,
            is_active=active,
        )
        user.set_password(raw_pw)
        user.save()

        grp, _ = Group.objects.get_or_create(name="pais")
        user.groups.add(grp)

        PaisProfile.objects.create(
            user=user,
            cpf=cpf,
            telefone=phone,
        )
        return user
