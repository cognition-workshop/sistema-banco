from django import forms
from django.db.models import Min, Max
from transactions.models import Transaction


class IRPFYearFilterForm(forms.Form):
    year = forms.ChoiceField(required=False, label='Ano Fiscal')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        year_range = Transaction.objects.aggregate(
            min_year=Min('timestamp__year'),
            max_year=Max('timestamp__year')
        )
        
        if year_range['min_year'] and year_range['max_year']:
            years = range(year_range['max_year'], year_range['min_year'] - 1, -1)
            choices = [('', 'Selecione o ano')] + [(str(year), str(year)) for year in years]
            self.fields['year'].choices = choices
        else:
            self.fields['year'].choices = [('', 'Nenhum dado disponível')]
