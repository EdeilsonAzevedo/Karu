from django import forms

from .models import DischargeRecord, Patient, Record


class PatientForm(forms.ModelForm):
    # Aceita CPF com pontuação e normaliza para 11 dígitos
    cpf = forms.CharField(
        required=False, max_length=14, help_text="Pode digitar com pontos e traço."
    )

    class Meta:
        model = Patient
        fields = [
            "first_name",
            "last_name",
            "sex",
            "date_of_birth",
            "cpf",
            "birth_certificate_number",
            "gestational_age_weeks",
            "gestational_age_days",
            "birth_weight",
            "birth_length",
            "head_circumference",
        ]
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


class RecordForm(forms.ModelForm):
    """Usado apenas para (data, notas). O tipo será forçado para 'discharge' na view."""

    class Meta:
        model = Record
        fields = ["date", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


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
        widgets = {
            "feeding_type": forms.Select(),
        }
