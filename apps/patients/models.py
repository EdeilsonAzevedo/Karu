from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

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

    guardian_name = models.CharField("Nome do Responsável", max_length=200, blank=True)
    contact_phone = models.CharField("Telefone de Contato", max_length=20, blank=True)

    address_street = models.CharField("Logradouro", max_length=255, blank=True)
    address_number = models.CharField("Número", max_length=20, blank=True)
    address_complement = models.CharField("Complemento", max_length=100, blank=True)
    address_neighborhood = models.CharField("Bairro", max_length=100, blank=True)
    address_city = models.CharField("Cidade", max_length=100, blank=True)
    address_state = models.CharField("UF", max_length=2, blank=True)
    address_zip_code = models.CharField("CEP", max_length=9, blank=True)

    def __str__(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name


class Record(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="records")
    record_type = models.CharField(
        max_length=20,
        choices=[("discharge", "Alta"), ("consultation", "Consulta"), ("followup", "Seguimento")],
    )
    date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    location = models.CharField(_("Local do Atendimento"), max_length=50, blank=True, null=True)
    professional = models.CharField(_("Profissional/Cargo"), max_length=150, blank=True, null=True)


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
    record = models.ForeignKey(
        Record, on_delete=models.CASCADE, related_name="clinical_evaluations"
    )
    type = models.CharField(max_length=20, choices=ClinicalEvaluationType.choices)
    status = models.CharField(
        max_length=10, choices=[("normal", "Normal"), ("altered", "Alterada")]
    )


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


class ConsultationRecord(BaseModel):
    record = models.OneToOneField(
        Record, on_delete=models.CASCADE, related_name="consultation_details"
    )

    # --- Seção 2: Medidas Antropométricas ---
    weight = models.DecimalField(
        _("Peso (g)"), max_digits=7, decimal_places=2, null=True, blank=True
    )
    weighed_without_diaper = models.BooleanField(_("Pesado sem fralda"), default=True)
    length = models.DecimalField(
        _("Comprimento (cm)"), max_digits=5, decimal_places=2, null=True, blank=True
    )
    head_circumference = models.DecimalField(
        _("Perímetro Cefálico (cm)"), max_digits=5, decimal_places=2, null=True, blank=True
    )

    # --- Seção 3: Aleitamento e Amamentação ---
    class FeedingType(models.TextChoices):
        EXCLUSIVE_BREASTFEEDING = "exclusive", _("Aleitamento materno exclusivo")
        MIXED = "mixed", _("Aleitamento misto")
        FORMULA = "formula", _("Fórmula")

    class BreastfeedingObservation(models.TextChoices):
        OK = "ok", _("Pega/posição OK")
        CORRECTION_NEEDED = "correction", _("Necessita correção")

    feeding_type = models.CharField(
        _("Tipo alimentar"), max_length=20, choices=FeedingType.choices, blank=True, null=True
    )
    feeding_interval = models.CharField(
        _("Intervalo entre mamadas"), max_length=100, blank=True, null=True
    )
    diapers_in_24h = models.PositiveSmallIntegerField(
        _("Número de fraldas em 24h"), null=True, blank=True
    )
    breastfeeding_observation = models.CharField(
        _("Observação da mamada"),
        max_length=20,
        choices=BreastfeedingObservation.choices,
        blank=True,
        null=True,
    )
    uses_pacifier = models.BooleanField(_("Uso de mamadeira/chupeta"), null=True, blank=True)

    # --- Seção 4: Posição Canguru ---
    kangaroo_hours_per_day = models.PositiveSmallIntegerField(
        _("Horas em contato pele a pele no dia"), null=True, blank=True
    )
    kangaroo_difficulties = models.TextField(
        _("Dificuldades ou interrupções"), blank=True, null=True
    )

    # --- Seção 5: Sinais Clínicos de Alerta ---
    warning_signs_observations = models.TextField(
        _("Observações adicionais sobre sinais de alerta"), blank=True, null=True
    )

    # --- Seção 6: Percurso da Família e Rede de Apoio ---
    family_arrival_notes = models.TextField(_("Como foi a chegada em casa?"), blank=True, null=True)
    family_support_notes = models.TextField(
        _("Quem está ajudando e de que forma?"), blank=True, null=True
    )

    # --- Seção 7: Orientações e Conduta ---
    guidance_given = models.TextField(_("Orientações dadas"), blank=True, null=True)
    return_plan = models.CharField(
        _("Plano de retorno agendado"), max_length=100, blank=True, null=True
    )
    next_appointment_date = models.DateField(_("Data do próximo retorno"), null=True, blank=True)


# ADICIONE ESTE NOVO MODELO para os checkboxes dos sinais de alerta
class ClinicalWarningSign(BaseModel):
    class WarningSignType(models.TextChoices):
        HYPOTHERMIA = "hypothermia", "Temperatura ≤ 36,5°C (hipotermia)"
        RESPIRATORY_PAUSE = "respiratory_pause", "Pausas respiratórias ≥ 20 seg ou cianose"
        SKIN_PERFUSION = "skin_perfusion", "Perfusão da pele: cianose, palidez, marmórea"
        REGURGITATION = "regurgitation", "Regurgitação ou vômitos frequentes"
        HYPOACTIVITY = "hypoactivity", "Sinais de hipoatividade ou irritabilidade"
        JAUNDICE = "jaundice", "Icterícia visível ou persistente"
        ABNORMALITIES = "abnormalities", "Sopro, hérnia abdominal ou fontanela abaulada"

    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name="warning_signs")
    type = models.CharField(_("Tipo de Sinal"), max_length=30, choices=WarningSignType.choices)
    is_present = models.BooleanField(_("Presente"), default=False)
