from django.contrib.auth.hashers import make_password
from factory.declarations import LazyAttribute, LazyFunction, Sequence, SubFactory
from factory.django import DjangoModelFactory
from factory.faker import Faker
from factory.fuzzy import FuzzyChoice
from faker import Faker as PyFaker

from .models import GestorProfile, PaisProfile, ProfissionalSaudeProfile, User

Faker._DEFAULT_LOCALE = "pt_BR"

_pf = PyFaker("pt_BR")


def cpf_digits(n: int) -> str:
    return f"{n:011d}"


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = Sequence(lambda n: f"user{n}")
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    email = LazyAttribute(lambda o: f"{o.username}@exemplo.com")
    password = LazyFunction(lambda: make_password("123456"))


class GestorProfileFactory(DjangoModelFactory):
    class Meta:
        model = GestorProfile

    user = SubFactory(UserFactory, user_type=User.UserType.GESTOR)
    cpf = Sequence(lambda n: cpf_digits(n + 10_000))
    telefone = Faker("phone_number")
    unidade = Faker("company")
    cargo = FuzzyChoice(["Coordenador", "Supervisor", "Gerente", "Analista"])
    departamento = FuzzyChoice(["Pediatria", "Neonatologia", "Ambulatório", "Administração"])


class ProfissionalSaudeProfileFactory(DjangoModelFactory):
    class Meta:
        model = ProfissionalSaudeProfile

    user = SubFactory(UserFactory, user_type=User.UserType.PROFISSIONAL_SAUDE)
    cpf = Sequence(lambda n: cpf_digits(n + 20_000))
    categoria = FuzzyChoice([c[0] for c in ProfissionalSaudeProfile.Categoria.choices])
    especialidade = FuzzyChoice(
        [
            "Neonatologia",
            "Pediatria",
            "Fisioterapia",
            "Fonoaudiologia",
            "Nutrição",
            "Psicologia",
            "",
        ]
    )
    conselho = FuzzyChoice(["CRM", "COREN", "CREFITO", "CRFa", "CRN", "CRP", None])
    numero_registro = LazyAttribute(
        lambda obj: _pf.bothify("######") if getattr(obj, "conselho", None) else None
    )
    unidade = Faker("company")
    telefone = Faker("phone_number")


class PaisProfileFactory(DjangoModelFactory):
    class Meta:
        model = PaisProfile

    user = SubFactory(UserFactory, user_type=User.UserType.PAIS)
    cpf = Sequence(lambda n: cpf_digits(n + 30_000))
    telefone = Faker("phone_number")
