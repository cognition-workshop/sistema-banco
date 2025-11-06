from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, RedirectView
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta

from .forms import UserRegistrationForm, UserAddressForm
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST


User = get_user_model()


class DashboardView(TemplateView):
    template_name = 'accounts/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if demo_user and hasattr(demo_user, 'account'):
            account = demo_user.account
            now = timezone.now()
            thirty_days_ago = now - timedelta(days=30)
            
            recent_transactions = Transaction.objects.filter(
                account=account,
                timestamp__gte=thirty_days_ago
            ).order_by('-timestamp')[:10]
            
            deposits_total = Transaction.objects.filter(
                account=account,
                timestamp__month=now.month,
                timestamp__year=now.year,
                transaction_type=DEPOSIT
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            withdrawals_total = Transaction.objects.filter(
                account=account,
                timestamp__month=now.month,
                timestamp__year=now.year,
                transaction_type=WITHDRAWAL
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            interest_total = Transaction.objects.filter(
                account=account,
                transaction_type=INTEREST
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            daily_data = []
            for i in range(30, -1, -1):
                date = (now - timedelta(days=i)).date()
                balance = Transaction.objects.filter(
                    account=account,
                    timestamp__date__lte=date
                ).order_by('-timestamp').first()
                daily_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'balance': float(balance.balance_after_transaction) if balance else 0
                })
            
            context.update({
                'account': account,
                'recent_transactions': recent_transactions,
                'deposits_total': deposits_total,
                'withdrawals_total': withdrawals_total,
                'interest_total': interest_total,
                'daily_data': daily_data,
            })
        
        return context


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
