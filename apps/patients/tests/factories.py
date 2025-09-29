# apps/patients/tests/factories.py
from decimal import Decimal

import factory

# Importar usando caminho absoluto em vez de relativo
from apps.patients.models import (
    ClinicalEvaluation,
    DischargeRecord,
    Exam,
    FollowUp,
    InterdisciplinaryEvaluation,
    Patient,
    Record,
    Vaccine,
)


class PatientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Patient

    first_name = "João"
    last_name = "Silva"
    sex = "M"
    date_of_birth = "2023-01-15"
    cpf = factory.Sequence(lambda n: f"{12345678900 + n}")  # type: ignore
    birth_certificate_number = factory.Sequence(lambda n: f"CERT{n:06d}")  # type: ignore
    gestational_age_weeks = 38
    gestational_age_days = 3
    birth_weight = Decimal("3.50")
    birth_length = Decimal("50.0")
    head_circumference = Decimal("35.0")


class RecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Record

    patient = factory.SubFactory(PatientFactory)  # type: ignore
    record_type = "discharge"
    date = "2023-02-01"
    notes = "Observações do teste"


class DischargeRecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DischargeRecord

    record = factory.SubFactory(RecordFactory)  # type: ignore
    chronological_age_days = 30
    corrected_age_weeks = 40
    weight = Decimal("4.20")
    length = Decimal("52.0")
    head_circumference = Decimal("36.0")
    feeding_type = "breastfeeding"


class ClinicalEvaluationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ClinicalEvaluation

    record = factory.SubFactory(RecordFactory)  # type: ignore
    type = "pediatric"
    status = "normal"


class InterdisciplinaryEvaluationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InterdisciplinaryEvaluation

    record = factory.SubFactory(RecordFactory)  # type: ignore
    area = "nursing"
    notes = "Avaliação teste"


class ExamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Exam

    record = factory.SubFactory(RecordFactory)  # type: ignore
    type = "Hemograma"
    result = "Normal"
    date = "2023-02-05"
    observations = "Sem observações"


class VaccineFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Vaccine

    record = factory.SubFactory(RecordFactory)  # type: ignore
    name = "BCG"
    date = "2023-02-02"
    lot = "LOT123"


class FollowUpFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FollowUp

    record = factory.SubFactory(RecordFactory)  # type: ignore
    date = "2023-03-01"
    specialty = "Pediatria"
    professional = "Dr. João"
