import random

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.factories import (
    FilhoFactory,
    GestorProfileFactory,
    PaisProfileFactory,
    ProfissionalSaudeProfileFactory,
)
from apps.patients.factories import (
    ClinicalEvaluationFactory,
    ClinicalWarningSignFactory,
    ConsultationRecordFactory,
    DischargeRecordFactory,
    ExamFactory,
    FollowUpFactory,
    InterdisciplinaryEvaluationFactory,
    PatientFactory,
    RecordFactory,
    VaccineFactory,
)


class Command(BaseCommand):
    help = "Popula o banco com dados fake"

    def add_arguments(self, parser):
        parser.add_argument("--patients", type=int, default=30)
        parser.add_argument("--records", type=int, default=80)
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument("--reset", action="store_true")
        parser.add_argument("--yes", action="store_true")

    @transaction.atomic
    def handle(self, *args, **opts):
        random.seed(opts["seed"])

        _gestor = GestorProfileFactory()
        _prof = ProfissionalSaudeProfileFactory()
        _pais = PaisProfileFactory()

        for _ in range(2):
            _ = FilhoFactory(pais=_pais)

        patients = PatientFactory.create_batch(opts["patients"])

        for _ in range(opts["records"]):
            kind = random.choice(["discharge", "consultation", "followup"])
            if kind == "discharge":
                d = DischargeRecordFactory(record__patient=random.choice(patients))
                record = d.record
            elif kind == "consultation":
                c = ConsultationRecordFactory(record__patient=random.choice(patients))
                record = c.record
            else:
                record = RecordFactory(record_type="followup", patient=random.choice(patients))

            ClinicalEvaluationFactory.create_batch(random.randint(0, 2), record=record)

            InterdisciplinaryEvaluationFactory.create_batch(random.randint(0, 2), record=record)

            ExamFactory.create_batch(random.randint(0, 2), record=record)

            if random.random() < 0.5:
                VaccineFactory(record=record)
            if random.random() < 0.3:
                FollowUpFactory(record=record)

            ClinicalWarningSignFactory.create_batch(random.randint(0, 3), record=record)

        self.stdout.write(self.style.SUCCESS("População concluída."))
