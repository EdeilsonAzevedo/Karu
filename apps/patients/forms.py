from django import forms
import datetime 

from .models import (
    ClinicalEvaluation,
    ClinicalWarningSign,
    ConsultationRecord,
    DischargeRecord,
    InterdisciplinaryEvaluation,
    Patient,
    Record,
)


# Em seu arquivo forms.py
from django import forms
import datetime
from .models import Patient # Certifique-se de que a importação está correta

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            "first_name", "last_name", "date_of_birth", "sex", "cpf",
            "birth_certificate_number", "guardian_name", "contact_phone",
            "address_street", "address_number", "address_complement",
            "address_neighborhood", "address_city", "address_state",
            "address_zip_code", "gestational_age_weeks", "gestational_age_days",
            "birth_weight", "birth_length", "head_circumference",
        ]
        labels = {
            "first_name": "Nome", "last_name": "Sobrenome", "date_of_birth": "Data de Nascimento",
            "sex": "Sexo", "cpf": "CPF", "birth_certificate_number": "Nº da Certidão de Nascimento",
            "guardian_name": "Nome do Responsável", "contact_phone": "Telefone de Contato",
            "address_street": "Logradouro", "address_number": "Número", "address_complement": "Complemento",
            "address_neighborhood": "Bairro", "address_city": "Cidade", "address_state": "Estado",
            "address_zip_code": "CEP", "gestational_age_weeks": "IG (semanas)",
            "gestational_age_days": "IG (dias)", "birth_weight": "Peso ao nascer (g)",
            "birth_length": "Comprimento ao nascer (cm)", "head_circumference": "PC ao nascer (cm)",
        }
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "cpf": forms.TextInput(attrs={"placeholder": "000.000.000-00"}),
            "contact_phone": forms.TextInput(attrs={"placeholder": "(00) 00000-0000"}),
            "address_zip_code": forms.TextInput(attrs={"placeholder": "00000-000"}),
            "birth_weight": forms.NumberInput(attrs={"placeholder": "Ex: 3100"}),
            "birth_length": forms.NumberInput(attrs={"placeholder": "Ex: 49.5"}),
        }

    def clean_cpf(self):
        cpf = self.cleaned_data.get("cpf") or ""
        only_digits = "".join(ch for ch in cpf if ch.isdigit())
        if only_digits == "":
            return None
        if len(only_digits) != 11:
            raise forms.ValidationError("CPF deve conter 11 dígitos numéricos.")
        return only_digits

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data.get('date_of_birth')
        if date_of_birth and date_of_birth > datetime.date.today():
            raise forms.ValidationError("A data de nascimento não pode ser no futuro.")
        return date_of_birth

    def __init__(self, *args, **kwargs):
        super(PatientForm, self).__init__(*args, **kwargs)

        self.label_suffix = " *" # Adiciona o asterisco aos campos obrigatórios

        optional_fields = ['address_complement']

        input_classes = "input input-bordered w-full transition-all duration-300 focus:input-primary"
        select_classes = "select select-bordered w-full transition-all duration-300 focus:select-primary"

        for field_name, field in self.fields.items():
            # Define campos como não-obrigatórios e remove o asterisco do label
            if field_name in optional_fields:
                field.required = False
                field.label_suffix = ""

            # Adiciona as classes de estilo padrão
            is_select = isinstance(field.widget, forms.Select)
            current_class = select_classes if is_select else input_classes
            field.widget.attrs.update({"class": current_class})

            # Adiciona a classe de erro se o formulário for submetido com erros
            if field_name in self.errors:
                error_class = " select-error" if is_select else " input-error"
                field.widget.attrs["class"] += f" {error_class}"


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
        self.label_suffix = " *" 
        optional_fields = ['notes']

        input_classes = "input input-bordered w-full transition-all duration-300 focus:input-primary"
        textarea_classes = "textarea textarea-bordered w-full transition-all duration-300 focus:textarea-primary"
        for field_name, field in self.fields.items():
            if field_name in optional_fields:
                field.required = False
                field.label_suffix = ""
                
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
        self.label_suffix = " *"
        
        self.fields['chronological_age_days'].required = False
        self.fields['corrected_age_weeks'].required = False
        
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
        
    def clean(self):
        cleaned_data = super().clean()
        
        status = cleaned_data.get("status")
        
        # Se o campo de conteúdo (status) não foi preenchido, removemos o erro 'required'
        # que o Django pode ter gerado no nível do modelo, tornando-o sempre válido.
        if not status:
            # Não fazemos nada, o formulário é considerado válido, mas vazio
            # e a view vai ignorá-lo na hora de salvar.
            pass

        return cleaned_data

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
        
    def clean(self):
        cleaned_data = super().clean()
        
        notes = cleaned_data.get("notes")
        
        # Se o campo de conteúdo (notes) não foi preenchido, o form é válido, mas vazio.
        if not notes:
            pass
            
        return cleaned_data
    
    def __init__(self, *args, **kwargs):
        super(InterdisciplinaryEvaluationForm, self).__init__(*args, **kwargs)
        self.fields['area'].required = False
        self.fields['notes'].required = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Torna ambos os campos opcionais para a validação do formulário
        self.fields["area"].required = False
        self.fields["notes"].required = False


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
