import logging
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.views import LoginView
from django.db import DatabaseError, transaction
from django.shortcuts import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, RedirectView

from .forms import UserRegistrationForm, UserAddressForm

logger = logging.getLogger(__name__)

User = get_user_model()


class UserRegistrationView(TemplateView):
    model = User
    form_class = UserRegistrationForm
    template_name = "accounts/user_registration.html"

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse_lazy("transactions:transaction_report"))
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        registration_form = UserRegistrationForm(self.request.POST)
        address_form = UserAddressForm(self.request.POST)

        try:
            if registration_form.is_valid() and address_form.is_valid():
                with transaction.atomic():
                    user = registration_form.save()
                    address = address_form.save(commit=False)
                    address.user = user
                    address.save()

                    login(self.request, user)
                    logger.info(
                        f"New user registered: {user.email}",
                        extra={
                            "user": user.email,
                            "account_no": user.account.account_no,
                        },
                    )
                    messages.success(
                        self.request,
                        (
                            f"Thank You For Creating A Bank Account. "
                            f"Your Account Number is {user.account.account_no}. "
                        ),
                    )
                    return HttpResponseRedirect(
                        reverse_lazy("transactions:deposit_money")
                    )
        except DatabaseError as e:
            logger.error(
                f"Database error during registration: {str(e)}",
                extra={
                    "user": request.user.email
                    if request.user.is_authenticated
                    else "anonymous"
                },
            )
            messages.error(
                self.request,
                "An error occurred while creating your account. Please try again.",
            )
        except Exception as e:
            logger.error(
                f"Unexpected error during registration: {str(e)}",
                extra={
                    "user": request.user.email
                    if request.user.is_authenticated
                    else "anonymous"
                },
            )
            messages.error(
                self.request, "An unexpected error occurred. Please try again."
            )

        return self.render_to_response(
            self.get_context_data(
                registration_form=registration_form, address_form=address_form
            )
        )

    def get_context_data(self, **kwargs):
        if "registration_form" not in kwargs:
            kwargs["registration_form"] = UserRegistrationForm()
        if "address_form" not in kwargs:
            kwargs["address_form"] = UserAddressForm()

        return super().get_context_data(**kwargs)


class UserLoginView(LoginView):
    template_name = "accounts/user_login.html"
    redirect_authenticated_user = True


class LogoutView(RedirectView):
    pattern_name = "home"

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            try:
                user_email = self.request.user.email
                logout(self.request)
                logger.info(
                    f"User logged out: {user_email}", extra={"user": user_email}
                )
            except Exception as e:
                logger.error(f"Error during logout: {str(e)}")
        return super().get_redirect_url(*args, **kwargs)
