from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, RedirectView

from .forms import UserRegistrationForm, UserAddressForm, OAuthAccountTypeForm


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


class OAuthAccountSetupView(TemplateView):
    template_name = 'accounts/oauth_account_setup.html'
    form_class = OAuthAccountTypeForm
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse_lazy('accounts:user_login'))
        
        if hasattr(request.user, 'account'):
            return HttpResponseRedirect(reverse_lazy('home'))
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        if 'form' not in kwargs:
            kwargs['form'] = self.form_class()
        return super().get_context_data(**kwargs)
    
    def post(self, request, *args, **kwargs):
        from django.conf import settings
        from .models import UserBankAccount
        
        form = self.form_class(request.POST)
        if form.is_valid():
            account_type = form.cleaned_data['account_type']
            user = request.user
            
            UserBankAccount.objects.create(
                user=user,
                account_type=account_type,
                account_no=user.id + settings.ACCOUNT_NUMBER_START_FROM,
            )
            
            messages.success(
                request,
                f'Account created successfully! Your account number is {user.account.account_no}.'
            )
            return HttpResponseRedirect(reverse_lazy('home'))
        
        return self.render_to_response(self.get_context_data(form=form))
