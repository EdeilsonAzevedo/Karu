from django.core.validators import RegexValidator
from django.db import models

from ..core.models import BaseModel

cpf_validator = RegexValidator(regex=r"^\d{11}$", message="CPF deve ter 11 dígitos numéricos.")


class Patient(BaseModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    sex = models.CharField(max_length=1, choices=[("M", "Masculino"), ("F", "Feminino")])
    date_of_birth = models.DateField()
    cpf = models.CharField(
        max_length=11,
        validators=[cpf_validator],
        blank=True,
        null=True,
        unique=True,
        help_text="Somente números, sem pontos ou traços.",
    )
    birth_certificate_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
        help_text="Número da certidão de nascimento (se disponível).",
    )
    # dados básicos de nascimento
    gestational_age_weeks = models.PositiveSmallIntegerField()
    gestational_age_days = models.PositiveSmallIntegerField(blank=True, null=True)
    birth_weight = models.DecimalField(max_digits=6, decimal_places=2)
    birth_length = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    head_circumference = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)


class Record(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="records")
    record_type = models.CharField(
        max_length=20,
        choices=[("discharge", "Alta"), ("consultation", "Consulta"), ("followup", "Seguimento")],
    )
    date = models.DateField()
    notes = models.TextField(blank=True, null=True)


class DischargeRecord(BaseModel):
    record = models.OneToOneField(Record, on_delete=models.CASCADE, related_name="discharge")
    chronological_age_days = models.PositiveIntegerField(blank=True, null=True)
    corrected_age_weeks = models.PositiveIntegerField(blank=True, null=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2)
    length = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    head_circumference = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    feeding_type = models.CharField(
        max_length=20,
        choices=[("breastfeeding", "SME"), ("mixed", "SM+Fórmula"), ("formula", "Fórmula")],
    )


class ClinicalEvaluationType(models.TextChoices):
    PEDIATRIC = "pediatric", "Pediátrica"
    NEUROLOGIC = "neurologic", "Neurológica"
    CARDIAC = "cardiac", "Cardiológica"
    VISUAL = "visual", "Visual"
    AUDITORY = "auditory", "Auditiva"

class InterdisciplinaryEvaluationArea(models.TextChoices):
    NURSING = "nursing", "Enfermagem"
    PHYSIOTHERAPY = "physiotherapy", "Fisioterapia"
    SPEECH = "speech", "Fonoaudiologia"
    PSYCHOLOGY = "psychology", "Psicologia"
    SOCIAL_WORK = "social_work", "Serviço Social"
    OCCUPATIONAL_THERAPY = "occupational_therapy", "Terapia Ocupacional"


class ClinicalEvaluation(BaseModel):
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name="clinical_evaluations")
    type = models.CharField(max_length=20, choices=ClinicalEvaluationType.choices)
    status = models.CharField(max_length=10, choices=[("normal", "Normal"), ("altered", "Alterada")])


class InterdisciplinaryEvaluation(BaseModel):
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name="team_evaluations")
    area = models.CharField(max_length=30, choices=InterdisciplinaryEvaluationArea.choices)
    notes = models.TextField(blank=True, null=True)


class Exam(BaseModel):
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name="exams")
    type = models.CharField(max_length=50)
    result = models.TextField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    observations = models.TextField(blank=True, null=True)


class Vaccine(BaseModel):
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name="vaccines")
    name = models.CharField(max_length=50)
    date = models.DateField()
    lot = models.CharField(max_length=50, blank=True, null=True)


class FollowUp(BaseModel):
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name="followups")
    date = models.DateField()
    time = models.TimeField(blank=True, null=True)
    specialty = models.CharField(max_length=50, blank=True, null=True)
    professional = models.CharField(max_length=100, blank=True, null=True)
