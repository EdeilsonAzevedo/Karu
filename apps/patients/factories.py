import random
from datetime import date, timedelta

from factory.declarations import LazyFunction, Sequence, SubFactory
from factory.django import DjangoModelFactory
from factory.faker import Faker
from factory.fuzzy import FuzzyChoice, FuzzyDecimal, FuzzyInteger

from apps.accounts.factories import PaisProfileFactory

from .models import (
    ClinicalEvaluation,
    ClinicalEvaluationType,
    ClinicalWarningSign,
    ConsultationRecord,
    DischargeRecord,
    Exam,
    FollowUp,
    InterdisciplinaryEvaluation,
    InterdisciplinaryEvaluationArea,
    Patient,
    Record,
    Vaccine,
)

Faker._DEFAULT_LOCALE = "pt_BR"


def cpf_digits(n: int) -> str:
    return f"{n:011d}"


class PatientFactory(DjangoModelFactory):
    class Meta:
        model = Patient

    first_name = Faker("first_name")
    last_name = Faker("last_name")
    sex = FuzzyChoice(["M", "F"])

    date_of_birth = LazyFunction(lambda: date.today() - timedelta(days=random.randint(0, 730)))
    cpf = Sequence(lambda n: cpf_digits(n))
    birth_certificate_number = Sequence(lambda n: f"BCN{n:07d}")
    gestational_age_weeks = FuzzyInteger(28, 42)
    gestational_age_days = FuzzyInteger(0, 6)
    birth_weight = FuzzyDecimal(800.00, 4500.00, 2)
    birth_length = FuzzyDecimal(35.0, 60.0, 1)
    head_circumference = FuzzyDecimal(25.0, 42.0, 1)

    guardian = SubFactory(PaisProfileFactory)

    address_street = Faker("street_name")
    address_number = FuzzyInteger(1, 9999)
    address_complement = FuzzyChoice(["", "Ap 101", "Casa", "Fundos"])
    address_neighborhood = Faker("bairro")
    address_city = Faker("city")
    address_state = FuzzyChoice(
        [
            "AL",
            "BA",
            "PE",
            "SE",
            "PB",
            "RN",
            "CE",
            "PI",
            "MA",
            "SP",
            "RJ",
            "MG",
            "RS",
            "SC",
            "PR",
            "DF",
            "GO",
            "MS",
            "MT",
            "PA",
            "AM",
            "AC",
            "RO",
            "RR",
            "AP",
            "ES",
        ]
    )
    address_zip_code = Faker("postcode")


class RecordFactory(DjangoModelFactory):
    class Meta:
        model = Record

    patient = SubFactory(PatientFactory)
    record_type = FuzzyChoice(["discharge", "consultation", "followup"])
    date = LazyFunction(lambda: date.today() - timedelta(days=random.randint(0, 60)))
    notes = Faker("paragraph", nb_sentences=3)
    location = FuzzyChoice(["Ambulatório", "UBS", "Hospital", "Domicílio", "Teleatendimento"])
    professional = FuzzyChoice(
        [
            "Enfermeiro(a)",
            "Médico(a)",
            "Fisioterapeuta",
            "Fonoaudiólogo(a)",
            "Nutricionista",
            "Psicólogo(a)",
        ]
    )


class DischargeRecordFactory(DjangoModelFactory):
    class Meta:
        model = DischargeRecord

    # Cria o Record correspondente (tipo "discharge")
    record = SubFactory(RecordFactory, record_type="discharge")
    chronological_age_days = FuzzyInteger(0, 120)
    corrected_age_weeks = FuzzyInteger(30, 48)
    weight = FuzzyDecimal(1500.00, 5000.00, 2)
    length = FuzzyDecimal(35.0, 65.0, 1)
    head_circumference = FuzzyDecimal(25.0, 44.0, 1)
    feeding_type = FuzzyChoice(["breastfeeding", "mixed", "formula"])


class ConsultationRecordFactory(DjangoModelFactory):
    class Meta:
        model = ConsultationRecord

    record = SubFactory(RecordFactory, record_type="consultation")
    weight = FuzzyDecimal(1500.00, 5000.00, 2)
    weighed_without_diaper = FuzzyChoice([True, False])
    length = FuzzyDecimal(35.0, 65.0, 1)

    head_circumference = FuzzyDecimal(25.0, 44.0, 1)

    feeding_type = FuzzyChoice(["exclusive", "mixed", "formula", None])
    feeding_interval = FuzzyChoice(["a cada 2h", "a cada 3h", "sob demanda", None])
    diapers_in_24h = FuzzyInteger(4, 12)
    breastfeeding_observation = FuzzyChoice(["ok", "correction", None])

    uses_pacifier = FuzzyChoice([True, False, None])

    kangaroo_hours_per_day = FuzzyInteger(0, 8)
    kangaroo_difficulties = Faker("sentence")

    warning_signs_observations = Faker("sentence")
    family_arrival_notes = Faker("sentence")
    family_support_notes = Faker("sentence")

    guidance_given = Faker("sentence")
    return_plan = FuzzyChoice(["7 dias", "15 dias", "30 dias", None])
    next_appointment_date = LazyFunction(
        lambda: date.today() + timedelta(days=random.randint(7, 45))
    )


class ClinicalEvaluationFactory(DjangoModelFactory):
    class Meta:
        model = ClinicalEvaluation

    record = SubFactory(RecordFactory)
    type = FuzzyChoice([t.value for t in ClinicalEvaluationType])
    status = FuzzyChoice(["normal", "altered"])


class InterdisciplinaryEvaluationFactory(DjangoModelFactory):
    class Meta:
        model = InterdisciplinaryEvaluation

    record = SubFactory(RecordFactory)
    area = FuzzyChoice([a.value for a in InterdisciplinaryEvaluationArea])
    notes = Faker("paragraph", nb_sentences=2)


class ExamFactory(DjangoModelFactory):
    class Meta:
        model = Exam

    record = SubFactory(RecordFactory)
    type = FuzzyChoice(["Hemograma", "Bilirrubina", "Raio-X", "US Craniano", "ECG"])
    result = Faker("paragraph", nb_sentences=2)
    date = LazyFunction(lambda: date.today() - timedelta(days=random.randint(0, 30)))
    observations = FuzzyChoice(["", "Repetir em 7 dias", "Dentro da normalidade", None])


class VaccineFactory(DjangoModelFactory):
    class Meta:
        model = Vaccine

    record = SubFactory(RecordFactory)
    name = FuzzyChoice(["BCG", "Hepatite B", "Penta", "VIP", "Rotavírus", "Pneumocócica 10"])
    date = LazyFunction(lambda: date.today() - timedelta(days=random.randint(0, 60)))
    lot = Sequence(lambda n: f"LOTE{n:05d}")


class FollowUpFactory(DjangoModelFactory):
    class Meta:
        model = FollowUp

    record = SubFactory(RecordFactory, record_type="followup")
    date = LazyFunction(lambda: date.today() + timedelta(days=random.randint(7, 60)))
    time = Faker("time_object")
    specialty = FuzzyChoice(
        ["Pediatria", "Fisioterapia", "Fonoaudiologia", "Nutrição", "Neurologia", None]
    )
    professional = FuzzyChoice(
        ["Médico(a)", "Enfermeiro(a)", "Fisioterapeuta", "Fonoaudiólogo(a)", None]
    )


class ClinicalWarningSignFactory(DjangoModelFactory):
    class Meta:
        model = ClinicalWarningSign

    record = SubFactory(RecordFactory)
    type = FuzzyChoice([t[0] for t in ClinicalWarningSign.WarningSignType.choices])
    is_present = FuzzyChoice([True, False])
