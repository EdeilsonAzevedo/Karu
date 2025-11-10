# populate_db.py
import random
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import GestorProfile, PaisProfile, ProfissionalSaudeProfile
from apps.patients.models import (
    ClinicalEvaluation,
    ClinicalEvaluationType,
    ClinicalWarningSign,
    ConsultationRecord,
    DischargeRecord,
    Exam,
    InterdisciplinaryEvaluation,
    InterdisciplinaryEvaluationArea,
    Patient,
    Record,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Popula o banco com dados realistas para demonstração - Foco Maceió/AL"

    def add_arguments(self, parser):
        parser.add_argument("--patients", type=int, default=25)
        parser.add_argument("--records", type=int, default=60)
        parser.add_argument("--seed", type=int, default=42)

    @transaction.atomic
    def handle(self, *args, **opts):
        import sys

        if "test" in sys.argv:
            self.stdout.write("Ambiente de teste detectado. Pulando população...")
            return

        random.seed(opts["seed"])

        self.stdout.write("Iniciando população do banco com dados realistas de Maceió/AL...")

        # 1. Criar usuários administrativos (gestores e profissionais)
        self.create_admin_users()

        # 2. Criar pacientes realistas CADA UM COM SEU PRÓPRIO RESPONSÁVEL
        patients = self.create_patients_with_unique_guardians(opts["patients"])

        # 3. Criar registros médicos
        self.create_medical_records(patients, opts["records"])

        self.stdout.write(
            self.style.SUCCESS(
                f"População concluída: {opts['patients']} pacientes, {opts['records']} registros criados."
            )
        )

    def create_admin_users(self):
        """Cria apenas usuários administrativos (gestores e profissionais)"""

        # Grupos
        gestores_group, _ = Group.objects.get_or_create(name="gestores")
        profissionais_group, _ = Group.objects.get_or_create(name="profissionais_saude")

        # Gestor de exemplo - Maceió
        if not User.objects.filter(username="12345678901").exists():
            gestor_user = User.objects.create_user(
                username="12345678901",
                first_name="Maria Silva Santos",
                email="maria.silva@hospitalmaceio.org",
                user_type=User.UserType.GESTOR,
                is_active=True,
            )
            gestor_user.set_password("senha123")
            gestor_user.save()
            gestor_user.groups.add(gestores_group)

            GestorProfile.objects.create(
                user=gestor_user,
                cpf="12345678901",
                telefone="(82) 99999-9999",
                unidade="UBS Benedito Bentes",
                cargo="Coordenadora de Enfermagem",
                departamento="Pediatria",
            )

        # Profissional de saúde de exemplo - Maceió
        if not User.objects.filter(username="98765432100").exists():
            profissional_user = User.objects.create_user(
                username="98765432100",
                first_name="Dr. João Carlos Oliveira",
                email="joao.oliveira@hospitalmaceio.org",
                user_type=User.UserType.PROFISSIONAL_SAUDE,
                is_active=True,
            )
            profissional_user.set_password("senha123")
            profissional_user.save()
            profissional_user.groups.add(profissionais_group)

            ProfissionalSaudeProfile.objects.create(
                user=profissional_user,
                cpf="98765432100",
                categoria="Médico",
                especialidade="Pediatria",
                conselho="CRM",
                numero_registro="AL-123456",
                unidade="UBS Benedito Bentes",
                telefone="(82) 98888-7777",
            )

    def create_unique_guardian(self, patient_index, patient_name):
        """Cria um responsável ÚNICO para cada criança"""

        # Lista extensa de nomes de responsáveis para evitar repetição
        guardian_first_names = [
            "Ana",
            "Carlos",
            "Fernanda",
            "Roberto",
            "Patrícia",
            "Marcos",
            "Juliana",
            "Ricardo",
            "Amanda",
            "Bruno",
            "Carla",
            "Daniel",
            "Elaine",
            "Fábio",
            "Gabriela",
            "Hugo",
            "Isabela",
            "João",
            "Larissa",
            "Maurício",
            "Natália",
            "Otávio",
            "Paula",
            "Rafael",
            "Sandra",
            "Thiago",
            "Vanessa",
            "Wagner",
            "Yasmin",
            "Zélia",
        ]

        guardian_last_names = [
            "Rodrigues",
            "Lima",
            "Souza",
            "Santos",
            "Almeida",
            "Costa",
            "Pereira",
            "Alves",
            "Gomes",
            "Ferreira",
            "Silva",
            "Oliveira",
            "Martins",
            "Rocha",
            "Barbosa",
            "Nunes",
            "Cavalcanti",
            "Dias",
            "Monteiro",
            "Carvalho",
            "Teixeira",
            "Mendes",
            "Brandão",
            "Xavier",
        ]

        # Gerar nome único combinando primeiro e último nome
        first_name = random.choice(guardian_first_names)
        last_name = random.choice(guardian_last_names)
        guardian_name = f"{first_name} {last_name}"

        # Criar email único baseado no nome e índice
        email_first = first_name.lower()
        email_last = last_name.lower()
        email = f"{email_first}.{email_last}{patient_index}@exemplo.com"

        # Criar CPF único para o responsável
        base_cpf = 70000000000 + patient_index
        cpf = f"{base_cpf:011d}"

        # Telefone realista de Alagoas
        phone = f"(82) 9{random.randint(8000, 9999)}-{random.randint(1000, 9999)}"

        # Usar a mesma lógica do PaisSignupForm para criar o usuário e perfil
        with transaction.atomic():
            # Criar User
            user = User.objects.create_user(
                username=cpf,
                first_name=guardian_name,
                email=email,
                user_type=User.UserType.PAIS,
                is_active=True,
            )
            user.set_password("senha123")
            user.save()

            # Adicionar ao grupo pais
            pais_group, _ = Group.objects.get_or_create(name="pais")
            user.groups.add(pais_group)

            # Criar PaisProfile
            guardian_profile = PaisProfile.objects.create(user=user, cpf=cpf, telefone=phone)

            return guardian_profile

    def create_patients_with_unique_guardians(self, num_patients):
        """Cria pacientes realistas, CADA UM COM SEU PRÓPRIO RESPONSÁVEL ÚNICO"""
        patients = []

        # Dados realistas para nomes de crianças
        male_names = [
            "Miguel",
            "Arthur",
            "Gael",
            "Heitor",
            "Theo",
            "Davi",
            "Gabriel",
            "Pedro",
            "Samuel",
            "João",
            "Lucas",
            "Enzo",
            "Bernardo",
            "Rafael",
        ]
        female_names = [
            "Alice",
            "Sophia",
            "Helena",
            "Valentina",
            "Laura",
            "Isabella",
            "Maria",
            "Júlia",
            "Heloísa",
            "Ana",
            "Lara",
            "Manuela",
            "Cecília",
            "Elisa",
        ]
        last_names = [
            "Silva",
            "Santos",
            "Oliveira",
            "Souza",
            "Rodrigues",
            "Ferreira",
            "Alves",
            "Lima",
            "Gomes",
            "Costa",
            "Martins",
            "Rocha",
            "Barbosa",
        ]

        # Cidades de Alagoas
        cidades_al = [
            "Maceió",
            "Arapiraca",
            "Rio Largo",
            "Marechal Deodoro",
            "São Miguel dos Campos",
            "Palmeira dos Índios",
            "União dos Palmares",
            "Santana do Ipanema",
            "Penedo",
            "Coruripe",
        ]

        # Bairros de Maceió
        bairros_maceio = [
            "Benedito Bentes",
            "Jacintinho",
            "Tabuleiro do Martins",
            "Feitosa",
            "Ponta Verde",
            "Jatiúca",
            "Mangabeiras",
            "Cruz das Almas",
            "Farol",
            "Pajuçara",
            "Garça Torta",
            "Jardim Petrópolis",
            "Clima Bom",
            "Santos Dumont",
            "Poço",
        ]

        self.stdout.write(
            f"Criando {num_patients} pacientes, cada um com seu próprio responsável único..."
        )

        for i in range(num_patients):
            is_male = random.choice([True, False])
            first_name = random.choice(male_names if is_male else female_names)
            last_name = random.choice(last_names)
            patient_full_name = f"{first_name} {last_name}"

            # Data de nascimento - maioria nos últimos 6 meses, alguns prematuros mais antigos
            if random.random() < 0.8:  # 80% nascidos nos últimos 6 meses
                days_ago = random.randint(1, 180)
            else:  # 20% prematuros mais antigos (até 2 anos)
                days_ago = random.randint(181, 730)

            birth_date = date.today() - timedelta(days=days_ago)

            # Idade gestacional - maioria a termo, alguns prematuros
            if random.random() < 0.7:  # 70% a termo
                gestational_weeks = random.randint(37, 42)
                gestational_days = random.randint(0, 6)
            else:  # 30% prematuros
                gestational_weeks = random.randint(28, 36)
                gestational_days = random.randint(0, 6)

            # Peso ao nascer baseado na idade gestacional
            if gestational_weeks >= 37:
                birth_weight = random.randint(2500, 4200)  # A termo
            elif gestational_weeks >= 34:
                birth_weight = random.randint(2000, 2900)  # Prematuro moderado
            else:
                birth_weight = random.randint(800, 1999)  # Prematuro extremo

            # Escolher cidade - 60% em Maceió, 40% em outras cidades de AL
            if random.random() < 0.6:
                city = "Maceió"
                neighborhood = random.choice(bairros_maceio)
            else:
                city = random.choice([c for c in cidades_al if c != "Maceió"])
                neighborhood = "Centro"

            # Criar responsável ÚNICO para este paciente
            guardian = self.create_unique_guardian(i, patient_full_name)

            # Criar paciente vinculado ao seu responsável único
            patient = Patient.objects.create(
                first_name=first_name,
                last_name=last_name,
                sex="M" if is_male else "F",
                date_of_birth=birth_date,
                cpf=f"{30000000000 + i:011d}",  # CPF único para o paciente
                birth_certificate_number=f"BC{i + 1000:06d}",
                gestational_age_weeks=gestational_weeks,
                gestational_age_days=gestational_days,
                birth_weight=birth_weight,
                birth_length=round(random.uniform(35.0, 52.0), 1),
                head_circumference=round(random.uniform(28.0, 38.0), 1),
                # Endereço - Maceió/AL
                address_street=f"Rua {random.choice(['das Flores', 'Amazonas', 'São João', 'Brasil', 'Alagoas', 'Marechal Deodoro'])}",
                address_number=random.randint(10, 2000),
                address_complement=random.choice(["", "Ap 101", "Casa 2", "Fundos", "Bloco B"]),
                address_neighborhood=neighborhood,
                address_city=city,
                address_state="AL",
                address_zip_code=f"57{random.randint(100, 999)}-{random.randint(100, 999)}",
                # Vincular ao responsável único criado
                guardian=guardian,
            )

            patients.append(patient)
            self.stdout.write(
                f"✅ Paciente {i + 1:2d}: {first_name} {last_name} -> Responsável: {guardian.user.first_name} ({city})"
            )

        return patients

    def create_medical_records(self, patients, num_records):
        """Cria registros médicos realistas"""

        feeding_types = ["breastfeeding", "mixed", "formula"]
        # Unidades de saúde de Maceió e região
        locations = [
            "Hospital Universitário",
            "UBS Benedito Bentes",
            "UBS Jacintinho",
            "UBS Feitosa",
            "Hospital do Pilar",
            "UBS Arapiraca Centro",
            "Hospital Geral",
            "Domicílio",
            "Teleatendimento",
        ]
        professionals = [
            "Enfermeiro(a)",
            "Médico(a)",
            "Fisioterapeuta",
            "Fonoaudiólogo(a)",
            "Nutricionista",
        ]

        for i in range(num_records):
            patient = random.choice(patients)

            # Data do registro - após o nascimento
            min_days_after_birth = 1
            max_days_after_birth = min(180, (date.today() - patient.date_of_birth).days)
            days_after_birth = random.randint(min_days_after_birth, max_days_after_birth)
            record_date = patient.date_of_birth + timedelta(days=days_after_birth)

            # Tipo de registro - maioria consultas, algumas altas
            if random.random() < 0.8:  # 80% consultas
                record_type = "consultation"
            else:  # 20% altas
                record_type = "discharge"

            # Criar registro base
            record = Record.objects.create(
                patient=patient,
                record_type=record_type,
                date=record_date,
                notes=self.generate_medical_notes(patient, record_type),
                location=random.choice(locations),
                professional=random.choice(professionals),
            )

            if record_type == "discharge":
                self.create_discharge_record(record, patient)
            else:
                self.create_consultation_record(record, patient)

            # Avaliações clínicas
            self.create_clinical_evaluations(record)

            # Avaliações interdisciplinares
            self.create_interdisciplinary_evaluations(record)

            # Exames (ocasionais)
            if random.random() < 0.4:  # 40% dos registros têm exames
                self.create_exams(patient, record_date)

            # Sinais de alerta (ocasionais)
            if random.random() < 0.25:  # 25% dos registros têm sinais de alerta
                self.create_warning_signs(record)

    def create_discharge_record(self, record, patient):
        """Cria registro de alta realista"""

        # Calcular idade cronológica e corrigida
        chronological_days = (record.date - patient.date_of_birth).days
        gestational_days_total = (patient.gestational_age_weeks * 7) + patient.gestational_age_days
        prematurity_days = max(0, 280 - gestational_days_total)  # 280 dias = 40 semanas
        corrected_days = max(0, chronological_days - prematurity_days)
        corrected_weeks = corrected_days // 7

        # Peso na alta - baseado no peso ao nascer e idade
        if patient.birth_weight < 1500:  # Muito baixo peso
            weight_gain_per_day = random.uniform(15, 25)
        elif patient.birth_weight < 2500:  # Baixo peso
            weight_gain_per_day = random.uniform(20, 30)
        else:  # Peso normal
            weight_gain_per_day = random.uniform(25, 35)

        discharge_weight = patient.birth_weight + (weight_gain_per_day * chronological_days)

        DischargeRecord.objects.create(
            record=record,
            chronological_age_days=chronological_days,
            corrected_age_weeks=corrected_weeks,
            weight=round(discharge_weight, 2),
            length=round(
                patient.birth_length + (random.uniform(0.1, 0.3) * chronological_days / 30), 1
            ),
            head_circumference=round(
                patient.head_circumference + (random.uniform(0.1, 0.2) * chronological_days / 30), 1
            ),
            feeding_type=random.choice(["breastfeeding", "mixed", "formula"]),
        )

    def create_consultation_record(self, record, patient):
        """Cria registro de consulta realista"""

        chronological_days = (record.date - patient.date_of_birth).days

        # Peso na consulta
        if patient.birth_weight < 1500:
            weight_gain_per_day = random.uniform(15, 25)
        elif patient.birth_weight < 2500:
            weight_gain_per_day = random.uniform(20, 30)
        else:
            weight_gain_per_day = random.uniform(25, 35)

        current_weight = patient.birth_weight + (weight_gain_per_day * chronological_days)

        ConsultationRecord.objects.create(
            record=record,
            weight=round(current_weight, 2),
            weighed_without_diaper=random.choice([True, False]),
            length=round(
                patient.birth_length + (random.uniform(0.1, 0.3) * chronological_days / 30), 1
            ),
            head_circumference=round(
                patient.head_circumference + (random.uniform(0.1, 0.2) * chronological_days / 30), 1
            ),
            feeding_type=random.choice(["exclusive", "mixed", "formula", None]),
            feeding_interval=random.choice(["a cada 2h", "a cada 3h", "sob demanda", None]),
            diapers_in_24h=random.randint(4, 8),
            breastfeeding_observation=random.choice(["ok", "correction", None]),
            uses_pacifier=random.choice([True, False, None]),
            kangaroo_hours_per_day=random.randint(0, 6),
            kangaroo_difficulties=random.choice(
                ["", "Choro excessivo", "Posicionamento difícil", "Nenhuma"]
            ),
            warning_signs_observations=random.choice(
                ["", "Nenhum sinal de alerta", "Leve irritabilidade"]
            ),
            family_arrival_notes=random.choice(
                ["Familiares presentes", "Acompanhante ausente", "Mãe presente"]
            ),
            family_support_notes=random.choice(
                ["Bom suporte familiar", "Família participativa", "Necessita orientação"]
            ),
            guidance_given=random.choice(
                [
                    "Orientações sobre amamentação",
                    "Cuidados com higiene",
                    "Sinais de alerta para retorno",
                    "Posição canguru",
                ]
            ),
            return_plan=random.choice(["7 dias", "15 dias", "30 dias", None]),
            next_appointment_date=record.date + timedelta(days=random.randint(7, 30)),
        )

    def create_clinical_evaluations(self, record):
        """Cria avaliações clínicas realistas"""

        evaluation_types = [t.value for t in ClinicalEvaluationType]

        for eval_type in evaluation_types:
            # Nem todos os tipos são avaliados em todos os registros
            if random.random() < 0.7:  # 70% chance de ter cada avaliação
                status = "normal" if random.random() < 0.8 else "altered"  # 80% normais

                ClinicalEvaluation.objects.create(record=record, type=eval_type, status=status)

    def create_interdisciplinary_evaluations(self, record):
        """Cria avaliações interdisciplinares realistas"""

        areas = [a.value for a in InterdisciplinaryEvaluationArea]

        for area in areas:
            if random.random() < 0.6:  # 60% chance de ter cada área
                notes_options = {
                    "nursing": [
                        "Evolução satisfatória",
                        "Necessita monitoramento",
                        "Boa adaptação",
                    ],
                    "physiotherapy": [
                        "Tônus muscular adequado",
                        "Exercícios passivos realizados",
                        "Posicionamento correto",
                    ],
                    "speech_therapy": [
                        "Sucção eficaz",
                        "Necessita estimulação",
                        "Reflexos presentes",
                    ],
                    "psychology": [
                        "Vínculo mãe-bebê adequado",
                        "Família adaptada",
                        "Necessita acompanhamento",
                    ],
                    "nutrition": [
                        "Ganho ponderal adequado",
                        "Aceitação alimentar boa",
                        "Necessita ajuste dietético",
                    ],
                    "social_service": [
                        "Suporte social adequado",
                        "Encaminhamentos realizados",
                        "Família orientada",
                    ],
                }

                InterdisciplinaryEvaluation.objects.create(
                    record=record,
                    area=area,
                    notes=random.choice(notes_options.get(area, ["Avaliação realizada"])),
                )

    def create_exams(self, patient, exam_date):
        """Cria exames realistas - vinculados ao paciente"""

        exam_types = [
            ("Hemograma", "Dentro da normalidade"),
            ("Bilirrubina total", f"{random.randint(5, 15)} mg/dL"),
            ("Raio-X de tórax", "Pulmões sem alterações"),
            ("US Craniano", "Ecodoppler normal"),
            ("Glicemia", f"{random.randint(70, 110)} mg/dL"),
            ("Teste do pezinho", "Resultados pendentes"),
        ]

        for exam_type, default_result in random.sample(exam_types, random.randint(1, 3)):
            try:
                # Tenta criar exame vinculado ao paciente
                Exam.objects.create(
                    patient=patient,
                    type=exam_type,
                    result=default_result,
                    date=exam_date - timedelta(days=random.randint(0, 2)),
                    observations=random.choice(["", "Repetir em 7 dias", "Dentro da normalidade"]),
                )
            except TypeError:
                # Se não tiver campo patient, cria sem vínculo
                Exam.objects.create(
                    type=exam_type,
                    result=default_result,
                    date=exam_date - timedelta(days=random.randint(0, 2)),
                    observations=random.choice(["", "Repetir em 7 dias", "Dentro da normalidade"]),
                )

    def create_warning_signs(self, record):
        """Cria sinais de alerta realistas"""

        warning_types = [
            "fever",
            "hypothermia",
            "feeding_difficulty",
            "respiratory_distress",
            "cyanosis",
            "lethargy",
            "irritability",
            "vomiting",
        ]

        for warning_type in random.sample(warning_types, random.randint(1, 2)):
            ClinicalWarningSign.objects.create(
                record=record, type=warning_type, is_present=random.choice([True, False])
            )

    def generate_medical_notes(self, patient, record_type):
        """Gera notas médicas realistas com contexto local"""

        if record_type == "discharge":
            notes = [
                f"Paciente em condições para alta. {patient.first_name} apresenta evolução satisfatória.",
                f"Alta hospitalar autorizada. {patient.first_name} com ganho ponderal adequado.",
                "Condições clínicas estáveis. Alta para acompanhamento ambulatorial em Maceió.",
                f"Paciente recebe alta com orientações para seguimento na UBS {random.choice(['Benedito Bentes', 'Jacintinho', 'Feitosa'])}.",
            ]
        else:
            notes = [
                f"Consulta de acompanhamento. {patient.first_name} em boa evolução.",
                "Retorno ambulatorial. Paciente estável, orientações reforçadas.",
                f"Avaliação de rotina. {patient.first_name} com desenvolvimento adequado para a idade.",
                f"Paciente de {patient.address_city} em acompanhamento regular.",
            ]

        return random.choice(notes)
