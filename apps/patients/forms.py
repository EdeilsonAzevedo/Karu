from django import forms

from .models import (
    ClinicalEvaluation,
    ClinicalWarningSign,
    ConsultationRecord,
    DischargeRecord,
    InterdisciplinaryEvaluation,
    Patient,
    Record,
)


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            "first_name",
            "last_name",
            "date_of_birth",
            "sex",
            "cpf",
            "birth_certificate_number",
            "guardian_name",
            "contact_phone",
            "address_street",
            "address_number",
            "address_complement",
            "address_neighborhood",
            "address_city",
            "address_state",
            "address_zip_code",
            "gestational_age_weeks",
            "gestational_age_days",
            "birth_weight",
            "birth_length",
            "head_circumference",
        ]

        # 1. Definindo os rótulos (labels) em português
        labels = {
            "first_name": "Nome",
            "last_name": "Sobrenome",
            "date_of_birth": "Data de Nascimento",
            "sex": "Sexo",
            "cpf": "CPF",
            "birth_certificate_number": "Nº da Certidão de Nascimento",
            "guardian_name": "Nome do Responsável",
            "contact_phone": "Telefone de Contato",
            "address_street": "Logradouro",
            "address_number": "Número",
            "address_complement": "Complemento",
            "address_neighborhood": "Bairro",
            "address_city": "Cidade",
            "address_state": "Estado",
            "address_zip_code": "CEP",
            "gestational_age_weeks": "IG (semanas)",
            "gestational_age_days": "IG (dias)",
            "birth_weight": "Peso ao nascer (g)",
            "birth_length": "Comprimento ao nascer (cm)",
            "head_circumference": "PC ao nascer (cm)",
        }

        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_cpf(self):
        cpf = self.cleaned_data.get("cpf") or ""
        only_digits = "".join(ch for ch in cpf if ch.isdigit())
        if only_digits == "":
            return None
        if len(only_digits) != 11:
            raise forms.ValidationError("CPF deve conter 11 dígitos numéricos.")
        return only_digits

    def __init__(self, *args, **kwargs):
        super(PatientForm, self).__init__(*args, **kwargs)

        # Classes padrão para a maioria dos inputs
        input_classes = (
            "input input-bordered w-full transition-all duration-300 focus:input-primary"
        )
        select_classes = (
            "select select-bordered w-full transition-all duration-300 focus:select-primary"
        )

        for field_name, field in self.fields.items():
            # Verifica se o widget é um tipo de select
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({"class": select_classes})
            # Para todos os outros, usamos as classes de input
            else:
                field.widget.attrs.update({"class": input_classes})


class RecordForm(forms.ModelForm):
    class Meta:
        model = Record
        fields = ["date", "location", "professional", "notes"]  # 'notes' é opcional mas bom ter
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "date": "Data da consulta",
            "location": "Local do atendimento",
            "professional": "Profissional/Cargo",
            "notes": "Observações da alta",
        }

    def __init__(self, *args, **kwargs):
        super(RecordForm, self).__init__(*args, **kwargs)
        input_classes = (
            "input input-bordered w-full transition-all duration-300 focus:input-primary"
        )
        textarea_classes = (
            "textarea textarea-bordered w-full transition-all duration-300 focus:textarea-primary"
        )
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({"class": textarea_classes})
            else:
                field.widget.attrs.update({"class": input_classes})


class DischargeRecordForm(forms.ModelForm):
    class Meta:
        model = DischargeRecord
        fields = [
            "chronological_age_days",
            "corrected_age_weeks",
            "weight",
            "length",
            "head_circumference",
            "feeding_type",
        ]
        labels = {
            "chronological_age_days": "Idade cronológica (dias)",
            "corrected_age_weeks": "Idade corrigida (semanas)",
            "weight": "Peso na alta (g)",
            "length": "Comprimento na alta (cm)",
            "head_circumference": "PC na alta (cm)",
            "feeding_type": "Tipo de alimentação",
        }
        widgets = {
            "feeding_type": forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super(DischargeRecordForm, self).__init__(*args, **kwargs)
        input_classes = (
            "input input-bordered w-full transition-all duration-300 focus:input-primary"
        )
        select_classes = (
            "select select-bordered w-full transition-all duration-300 focus:select-primary"
        )
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({"class": select_classes})
            else:
                field.widget.attrs.update({"class": input_classes})


# formulário para as avaliações clínicas
class ClinicalEvaluationForm(forms.ModelForm):
    class Meta:
        model = ClinicalEvaluation
        fields = ["type", "status"]
        # Usamos um widget escondido para o tipo, pois vamos criá-los separadamente
        widgets = {
            "type": forms.HiddenInput(),
        }
        labels = {"status": ""}

    def __init__(self, *args, **kwargs):
        super(ClinicalEvaluationForm, self).__init__(*args, **kwargs)
        self.fields["type"].required = False
        self.fields["status"].required = False
        status_choices = self.fields["status"].choices[1:]  # type: ignore
        self.fields["status"].choices = [("", "Não informado")] + status_choices
        self.fields["status"].widget.attrs.update({"class": "select select-bordered w-full"})


# formulário para as avaliações da equipe
class InterdisciplinaryEvaluationForm(forms.ModelForm):
    class Meta:
        model = InterdisciplinaryEvaluation
        fields = ["area", "notes"]
        widgets = {
            "area": forms.HiddenInput(),
            "notes": forms.Textarea(
                attrs={"rows": 2, "class": "textarea textarea-bordered w-full"}
            ),
        }
        labels = {"notes": ""}


class ConsultationRecordForm(forms.ModelForm):
    class Meta:
        model = ConsultationRecord
        exclude = ["record"]

        labels = {
            "weight": "Peso atual (gramas)",
            "weighed_without_diaper": "Pesado sem fralda",
            "length": "Comprimento (cm)",
            "head_circumference": "Perímetro cefálico (cm)",
            "feeding_type": "Tipo alimentar",
            "feeding_interval": "Intervalo entre mamadas",
            "diapers_in_24h": "Número de fraldas em 24h",
            "breastfeeding_observation": "Observação da mamada",
            "uses_pacifier": "Uso de mamadeira/chupeta",
            "kangaroo_hours_per_day": "Horas em contato pele a pele no dia",
            "kangaroo_difficulties": "Dificuldades ou interrupções",
            "warning_signs_observations": "Observações adicionais sobre sinais de alerta",
            "family_arrival_notes": "Como foi a chegada em casa?",
            "family_support_notes": "Quem está ajudando e de que forma?",
            "guidance_given": "Orientações dadas",
            "return_plan": "Plano de retorno agendado",
            "next_appointment_date": "Data do próximo retorno",
        }

        widgets = {
            "next_appointment_date": forms.DateInput(attrs={"type": "date"}),
            "uses_pacifier": forms.RadioSelect(choices=[(True, "Sim"), (False, "Não")]),
            "breastfeeding_observation": forms.RadioSelect,
            "warning_signs_observations": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Descreva qualquer sinal observado..."}
            ),
            "kangaroo_difficulties": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Comentários sobre dificuldades"}
            ),
            "family_arrival_notes": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Dificuldades ou intercorrências"}
            ),
            "family_support_notes": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Rede de apoio familiar e comunitária"}
            ),
            "guidance_given": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Resumo das orientações: posição canguru, mamadas, etc.",
                }
            ),
        }


class ClinicalWarningSignForm(forms.ModelForm):
    class Meta:
        model = ClinicalWarningSign
        fields = ["type", "is_present"]
        widgets = {
            "type": forms.HiddenInput(),
            "is_present": forms.CheckboxInput(attrs={"class": "checkbox checkbox-error"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove o label do lado do checkbox, pois o texto já está no HTML
        self.fields["is_present"].label = ""
