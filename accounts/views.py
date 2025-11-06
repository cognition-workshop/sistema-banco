from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.views import LoginView
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import HttpResponseRedirect, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, RedirectView
from django.db import connection
from django.db.models import Sum, Count

from .forms import UserRegistrationForm, UserAddressForm
from .models import UserBankAccount
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST


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


@staff_member_required
def system_health_dashboard(request):
    User = get_user_model()
    
    total_users = User.objects.count()
    users_with_accounts = User.objects.filter(account__isnull=False).count()
    
    total_accounts = UserBankAccount.objects.count()
    total_balance = UserBankAccount.objects.aggregate(
        total=Sum('balance')
    )['total'] or 0
    
    total_transactions = Transaction.objects.count()
    recent_transactions = Transaction.objects.select_related(
        'account', 'account__user'
    ).order_by('-timestamp')[:10]
    
    deposits_count = Transaction.objects.filter(transaction_type=DEPOSIT).count()
    withdrawals_count = Transaction.objects.filter(transaction_type=WITHDRAWAL).count()
    interest_count = Transaction.objects.filter(transaction_type=INTEREST).count()
    
    try:
        connection.ensure_connection()
        db_status = 'Connected'
    except Exception as e:
        db_status = f'Error: {str(e)}'
    
    context = {
        'total_users': total_users,
        'users_with_accounts': users_with_accounts,
        'total_accounts': total_accounts,
        'total_balance': total_balance,
        'total_transactions': total_transactions,
        'recent_transactions': recent_transactions,
        'deposits_count': deposits_count,
        'withdrawals_count': withdrawals_count,
        'interest_count': interest_count,
        'db_status': db_status,
        'title': 'System Health Dashboard',
    }
    
    return render(request, 'admin/system_health_dashboard.html', context)
