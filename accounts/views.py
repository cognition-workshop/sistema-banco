from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import HttpResponseRedirect, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, RedirectView
from datetime import date

from .forms import UserRegistrationForm, UserAddressForm
from .ir_reports import generate_ir_report, export_ir_report_pdf


User = get_user_model()


class UserRegistrationView(TemplateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/user_registration.html'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(
                reverse_lazy('transactions:transaction_report')
            )
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        registration_form = UserRegistrationForm(self.request.POST)
        address_form = UserAddressForm(self.request.POST)

        if registration_form.is_valid() and address_form.is_valid():
            user = registration_form.save()
            address = address_form.save(commit=False)
            address.user = user
            address.save()

            login(self.request, user)
            messages.success(
                self.request,
                (
                    f'Thank You For Creating A Bank Account. '
                    f'Your Account Number is {user.account.account_no}. '
                )
            )
            return HttpResponseRedirect(
                reverse_lazy('transactions:deposit_money')
            )

        return self.render_to_response(
            self.get_context_data(
                registration_form=registration_form,
                address_form=address_form
            )
        )

    def get_context_data(self, **kwargs):
        if 'registration_form' not in kwargs:
            kwargs['registration_form'] = UserRegistrationForm()
        if 'address_form' not in kwargs:
            kwargs['address_form'] = UserAddressForm()

        return super().get_context_data(**kwargs)


class UserLoginView(LoginView):
    template_name='accounts/user_login.html'
    redirect_authenticated_user = True


class LogoutView(RedirectView):
    pattern_name = 'home'

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            logout(self.request)
        return super().get_redirect_url(*args, **kwargs)


@login_required
def ir_report_view(request):
    current_year = date.today().year
    year = int(request.GET.get('year', current_year - 1))
    
    account = request.user.account
    
    if request.GET.get('export') == 'pdf':
        return export_ir_report_pdf(account, year)
    
    report_data = generate_ir_report(account, year)
    
    available_years = range(current_year - 5, current_year + 1)
    
    context = {
        'report_data': report_data,
        'year': year,
        'available_years': available_years,
    }
    
    return render(request, 'accounts/ir_report.html', context)
