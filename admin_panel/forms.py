from django import forms
from accounts.models import User


class UserSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 leading-tight focus:outline-none focus:bg-white focus:border-gray-500',
            'placeholder': 'Buscar por email, nome ou número da conta...'
        })
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos'), ('active', 'Ativos'), ('inactive', 'Inativos')],
        widget=forms.Select(attrs={
            'class': 'appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 leading-tight focus:outline-none focus:bg-white focus:border-gray-500'
        })
    )


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'is_active']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 leading-tight focus:outline-none focus:bg-white focus:border-gray-500'
            })


class UserSuspendForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 leading-tight focus:outline-none focus:bg-white focus:border-gray-500',
            'rows': 4,
            'placeholder': 'Motivo da suspensão...'
        })
    )
