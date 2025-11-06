from django import forms
from .models import FraudRule, FraudAlert, STATUS_CHOICES, SEVERITY_CHOICES


class FraudRuleForm(forms.ModelForm):
    class Meta:
        model = FraudRule
        fields = [
            'name', 'description', 'rule_type', 'threshold_amount',
            'time_window_minutes', 'max_transactions', 'is_active', 'severity'
        ]

    def clean(self):
        cleaned_data = super().clean()
        rule_type = cleaned_data.get('rule_type')
        threshold_amount = cleaned_data.get('threshold_amount')
        time_window_minutes = cleaned_data.get('time_window_minutes')
        max_transactions = cleaned_data.get('max_transactions')

        if rule_type == 'high_amount':
            if not threshold_amount:
                raise forms.ValidationError(
                    "Threshold amount is required for high_amount rules"
                )

        elif rule_type == 'frequency':
            if not time_window_minutes or not max_transactions:
                raise forms.ValidationError(
                    "Time window and max transactions are required for frequency rules"
                )

        elif rule_type == 'velocity':
            if not time_window_minutes or not threshold_amount:
                raise forms.ValidationError(
                    "Time window and threshold amount are required for velocity rules"
                )

        return cleaned_data


class FraudAlertFilterForm(forms.Form):
    status = forms.ChoiceField(
        choices=[('', 'All')] + list(STATUS_CHOICES),
        required=False
    )
    severity = forms.ChoiceField(
        choices=[('', 'All')] + list(SEVERITY_CHOICES),
        required=False
    )
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
