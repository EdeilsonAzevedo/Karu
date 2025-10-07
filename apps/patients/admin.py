from auditlog.registry import auditlog
from django.contrib import admin

# Importe todos os modelos que você deseja auditar
from .models import (
    ClinicalEvaluation,
    ClinicalWarningSign,
    ConsultationRecord,
    DischargeRecord,
    Exam,
    FollowUp,
    InterdisciplinaryEvaluation,
    Patient,
    Record,
    Vaccine,
)

# --- Registro na Interface de Admin (Opcional, mas recomendado) ---
admin.site.register(Patient)
admin.site.register(Record)
admin.site.register(ConsultationRecord)

# --- Registro no Sistema de Auditoria (Essencial) ---
# Informa ao django-auditlog para monitorar as alterações nestes modelos.
auditlog.register(Patient)
auditlog.register(Record)
auditlog.register(DischargeRecord)
auditlog.register(ConsultationRecord)
auditlog.register(ClinicalEvaluation)
auditlog.register(InterdisciplinaryEvaluation)
auditlog.register(ClinicalWarningSign)
auditlog.register(Exam)
auditlog.register(Vaccine)
auditlog.register(FollowUp)
