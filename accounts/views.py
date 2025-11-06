from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, RedirectView
from django.db import IntegrityError, DatabaseError
import logging

from .forms import UserRegistrationForm, UserAddressForm

logger = logging.getLogger(__name__)


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
            try:
                email = registration_form.cleaned_data.get('email')
                if User.objects.filter(email=email).exists():
                    logger.warning(f'Tentativa de registro com email duplicado: {email}')
                    messages.error(
                        self.request,
                        'Já existe uma conta com este email. Por favor, faça login ou use outro email.'
                    )
                    return self.render_to_response(
                        self.get_context_data(
                            registration_form=registration_form,
                            address_form=address_form
                        )
                    )

                user = registration_form.save()
                address = address_form.save(commit=False)
                address.user = user
                address.save()

                login(self.request, user)
                
                logger.info(
                    f'Novo usuário registrado com sucesso. '
                    f'Email: {user.email}, '
                    f'Conta: {user.account.account_no}'
                )
                
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
            
            except (IntegrityError, DatabaseError) as e:
                logger.error(
                    f'Erro ao criar conta. Email: {registration_form.cleaned_data.get("email")}, '
                    f'Erro: {str(e)}',
                    exc_info=True
                )
                messages.error(
                    self.request,
                    'Erro ao criar conta. Por favor, tente novamente ou contate o suporte.'
                )
                return self.render_to_response(
                    self.get_context_data(
                        registration_form=registration_form,
                        address_form=address_form
                    )
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
