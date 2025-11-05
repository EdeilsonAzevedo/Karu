import json
from typing import TYPE_CHECKING

from auditlog.models import LogEntry
from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group
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

    def __init__(self, *args, **kwargs):
        self.actor = None
        super().__init__(*args, **kwargs)

    def set_actor(self, actor):
        """Define o usuário que está realizando a ação para o auditlog"""
        self.actor = actor

    def get_actor(self, request=None):
        """Obtém o usuário que está realizando a ação"""
        if hasattr(self, "actor"):
            return self.actor
        elif request and hasattr(request, "user") and request.user.is_authenticated:
            return request.user
        return None

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
    def save(self, request=None):
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
            user_type=User.UserType.GESTOR,
        )
        user.set_password(raw_pw)
        user.save()

        g, _ = Group.objects.get_or_create(name="gestores")
        user.groups.add(g)

        perfil = GestorProfile.objects.create(
            user=user,
            cpf=cpf,
            telefone=phone,
            unidade=unit,
            cargo=cargo,
        )

        # REGISTRO NO AUDITLOG - Usuário
        actor = self.get_actor(request)

        LogEntry.objects.log_create(
            instance=user,
            action=LogEntry.Action.CREATE,
            changes=json.dumps(
                [
                    {
                        "username": ["", user.username],
                        "first_name": ["", user.first_name],
                        "email": ["", user.email],
                        "user_type": ["", user.user_type],
                        "is_active": ["", user.is_active],
                    }
                ]
            ),
            actor=actor,
        )

        # REGISTRO NO AUDITLOG - Perfil
        LogEntry.objects.log_create(
            instance=perfil,
            action=LogEntry.Action.CREATE,
            changes=json.dumps(
                [
                    {
                        "cpf": ["", perfil.cpf],
                        "unidade": ["", perfil.unidade],
                        "cargo": ["", perfil.cargo],
                        "telefone": ["", perfil.telefone],
                    }
                ]
            ),
            actor=actor,
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

    def __init__(self, *args, **kwargs):
        self.actor = None
        super().__init__(*args, **kwargs)

    def set_actor(self, actor):
        """Define o usuário que está realizando a ação para o auditlog"""
        self.actor = actor

    def get_actor(self, request=None):
        """Obtém o usuário que está realizando a ação"""
        if hasattr(self, "actor"):
            return self.actor
        elif request and hasattr(request, "user") and request.user.is_authenticated:
            return request.user
        return None

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
    def save(self, request=None):
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
            user_type=User.UserType.PROFISSIONAL_SAUDE,
        )
        user.set_password(raw_pw)
        user.save()

        grp, _ = Group.objects.get_or_create(name="profissionais_saude")
        user.groups.add(grp)

        perfil = ProfissionalSaudeProfile.objects.create(
            user=user,
            cpf=cpf,
            categoria=self.cleaned_data["category"],
            especialidade=(self.cleaned_data.get("specialty") or "").strip(),
            conselho=(self.cleaned_data.get("council") or None) or None,
            numero_registro=(self.cleaned_data.get("reg_number") or None) or None,
            unidade=unit,
            telefone=phone,
        )

        # REGISTRO NO AUDITLOG - Usuário
        actor = self.get_actor(request)

        LogEntry.objects.log_create(
            instance=user,
            action=LogEntry.Action.CREATE,
            changes=json.dumps(
                [
                    {
                        "username": ["", user.username],
                        "first_name": ["", user.first_name],
                        "email": ["", user.email],
                        "user_type": ["", user.user_type],
                        "is_active": ["", user.is_active],
                    }
                ]
            ),
            actor=actor,
        )

        # REGISTRO NO AUDITLOG - Perfil
        LogEntry.objects.log_create(
            instance=perfil,
            action=LogEntry.Action.CREATE,
            changes=json.dumps(
                [
                    {
                        "cpf": ["", perfil.cpf],
                        "categoria": ["", perfil.categoria],
                        "especialidade": ["", perfil.especialidade],
                        "conselho": ["", perfil.conselho or ""],
                        "numero_registro": ["", perfil.numero_registro or ""],
                        "unidade": ["", perfil.unidade],
                        "telefone": ["", perfil.telefone],
                    }
                ]
            ),
            actor=actor,
        )

        return user


class PaisSignupForm(forms.Form):
    name = forms.CharField(label="Nome completo", required=True)
    cpf = forms.CharField(label="CPF", required=True)
    email = forms.EmailField(label="E-mail", required=True)
    phone = forms.CharField(label="Telefone", required=False, validators=[phone_br_validator])
    temp_password = forms.CharField(label="Senha temporária", required=False)
    status = forms.ChoiceField(
        label="Status", choices=[("Ativo", "Ativo"), ("Inativo", "Inativo")], required=False
    )

    def __init__(self, *args, **kwargs):
        self.actor = None
        super().__init__(*args, **kwargs)

        input_classes = (
            "input input-bordered w-full transition-all duration-300 focus:input-primary"
        )

        self.fields["name"].widget.attrs.update({"class": input_classes})
        self.fields["email"].widget.attrs.update({"class": input_classes})
        self.fields["cpf"].widget.attrs.update(
            {"class": input_classes, "placeholder": "000.000.000-00"}
        )
        self.fields["phone"].widget.attrs.update(
            {"class": input_classes, "placeholder": "(00) 00000-0000"}
        )
        self.fields["temp_password"].widget.attrs.update({"class": input_classes})

        # Oculta o campo 'status' no formulário de cadastro de recém-nascido,
        # pois o usuário deve ser sempre 'Ativo' nesse contexto.
        self.fields["status"].widget = forms.HiddenInput()
        self.fields["status"].initial = "Ativo"

    def set_actor(self, actor):
        """Define o usuário que está realizando a ação para o auditlog"""
        self.actor = actor

    def get_actor(self, request=None):
        """Obtém o usuário que está realizando a ação"""
        if hasattr(self, "actor"):
            return self.actor
        elif request and hasattr(request, "user") and request.user.is_authenticated:
            return request.user
        return None

    def clean_email(self):
        return normalize_email(self.cleaned_data["email"])

    def clean_cpf(self):
        cpf_raw = self.cleaned_data.get("cpf") or ""
        cpf_digits = "".join(filter(str.isdigit, cpf_raw))

        if len(cpf_digits) != 11:
            raise ValidationError("CPF deve conter 11 dígitos (somente números).")

        if User.objects.filter(username=cpf_digits).exists():
            raise ValidationError("Já existe um usuário com este CPF.")
        if PaisProfile.objects.filter(cpf=cpf_digits).exists():
            raise ValidationError("Já existe um responsável com este CPF.")

        return cpf_digits

    def clean_temp_password(self):
        pwd = self.cleaned_data.get("temp_password") or ""
        if not pwd:
            return pwd
        try:
            password_validation.validate_password(pwd)
        except exceptions.ValidationError as e:
            raise e
        return pwd

    def clean_phone(self):
        v = (self.cleaned_data.get("phone") or "").strip()
        if not v:
            return ""
        phone_br_validator(v)
        return v

    @transaction.atomic
    def save(self, request=None):
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
            user_type=User.UserType.PAIS,
        )
        user.set_password(raw_pw)
        user.save()

        grp, _ = Group.objects.get_or_create(name="pais")
        user.groups.add(grp)

        perfil = PaisProfile.objects.create(
            user=user,
            cpf=cpf,
            telefone=phone,
        )

        # REGISTRO NO AUDITLOG - Usuário
        actor = self.get_actor(request)

        LogEntry.objects.log_create(
            instance=user,
            action=LogEntry.Action.CREATE,
            # CORREÇÃO: Use valores reais, não strings formatadas
            changes=json.dumps(
                [
                    {
                        "username": ["", user.username],
                        "first_name": ["", user.first_name],
                        "email": ["", user.email],
                        "user_type": ["", user.user_type],
                        "is_active": ["", user.is_active],  # Booleano real
                    }
                ]
            ),
            actor=actor,
        )

        # REGISTRO NO AUDITLOG - Perfil
        LogEntry.objects.log_create(
            instance=perfil,
            action=LogEntry.Action.CREATE,
            changes=json.dumps([{"cpf": ["", perfil.cpf], "telefone": ["", perfil.telefone]}]),
            actor=actor,
        )

        return user


class PaisProfileUpdateForm(forms.ModelForm):
    """
    Formulário para ATUALIZAR um PaisProfile e os dados do User associado,
    incluindo a redefinição de senha.
    """

    # Campos do User (first_name é usado para o nome completo)
    name = forms.CharField(label="Nome completo", required=True)
    email = forms.EmailField(label="E-mail", required=True)

    # Campo do PaisSignupForm (para consistência) que mapeia para PaisProfile.telefone
    phone = forms.CharField(label="Telefone", required=False, validators=[phone_br_validator])

    # Campo para Redefinição de Senha (conforme solicitado)
    new_password = forms.CharField(
        label="Redefinir Senha (Opcional)",
        required=False,
        widget=forms.PasswordInput(render_value=False, attrs={"autocomplete": "new-password"}),
        help_text="Deixe em branco para não alterar a senha.",
    )

    class Meta:
        model = PaisProfile
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance:
            if self.instance.user:
                self.fields["name"].initial = self.instance.user.first_name
                self.fields["email"].initial = self.instance.user.email
            self.fields["phone"].initial = self.instance.telefone

        input_classes = (
            "input input-bordered w-full transition-all duration-300 focus:input-primary"
        )
        self.fields["name"].widget.attrs.update({"class": input_classes})
        self.fields["email"].widget.attrs.update({"class": input_classes})
        self.fields["phone"].widget.attrs.update(
            {"class": input_classes, "placeholder": "(00) 00000-0000"}
        )
        self.fields["new_password"].widget.attrs.update({"class": input_classes})

    def clean_phone(self):
        v = (self.cleaned_data.get("phone") or "").strip()
        if not v:
            return ""
        phone_br_validator(v)
        return v

    def clean_new_password(self):
        pwd = self.cleaned_data.get("new_password") or ""
        if not pwd:
            return ""
        try:
            password_validation.validate_password(pwd)
        except exceptions.ValidationError as e:
            raise e
        return pwd

    @transaction.atomic
    def save(self, commit=True):
        profile = self.instance
        user = profile.user

        user.first_name = self.cleaned_data["name"]
        user.email = self.cleaned_data["email"]

        profile.telefone = self.cleaned_data["phone"]

        new_password = self.cleaned_data.get("new_password")
        if new_password:
            user.set_password(new_password)

        if commit:
            user.save()
            profile.save()

        return profile
