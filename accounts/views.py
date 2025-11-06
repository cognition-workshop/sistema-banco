from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, RedirectView
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .forms import UserRegistrationForm, UserAddressForm
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


class DashboardView(TemplateView):
    template_name = 'accounts/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        demo_user = User.objects.filter(email='demo@example.com').first()
        account = demo_user.account if demo_user and hasattr(demo_user, 'account') else None
        
        if not account:
            context.update({
                'account': None,
                'current_balance': 0,
                'monthly_deposits': 0,
                'monthly_withdrawals': 0,
                'accumulated_interest': 0,
                'recent_transactions': [],
                'chart_labels': [],
                'chart_data': [],
            })
            return context
        
        current_balance = account.balance
        
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        monthly_deposits = account.transactions.filter(
            transaction_type=DEPOSIT,
            timestamp__gte=month_start
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        monthly_withdrawals = account.transactions.filter(
            transaction_type=WITHDRAWAL,
            timestamp__gte=month_start
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        accumulated_interest = account.transactions.filter(
            transaction_type=INTEREST
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        recent_transactions = account.transactions.all().order_by('-timestamp')[:10]
        
        chart_labels, chart_data = self._generate_balance_evolution(account)
        
        context.update({
            'account': account,
            'current_balance': current_balance,
            'monthly_deposits': monthly_deposits,
            'monthly_withdrawals': monthly_withdrawals,
            'accumulated_interest': accumulated_interest,
            'recent_transactions': recent_transactions,
            'chart_labels': chart_labels,
            'chart_data': chart_data,
        })
        
        return context
    
    def _generate_balance_evolution(self, account):
        from transactions.models import Transaction
        
        labels = []
        data = []
        
        today = timezone.now().date()
        start_date = today - timedelta(days=30)
        
        transactions = account.transactions.filter(
            timestamp__date__gte=start_date
        ).order_by('timestamp')
        
        transactions_in_range = account.transactions.filter(
            timestamp__date__gte=start_date
        )
        
        balance_change = Decimal('0')
        for txn in transactions_in_range:
            if txn.transaction_type == DEPOSIT or txn.transaction_type == INTEREST:
                balance_change += txn.amount
            elif txn.transaction_type == WITHDRAWAL:
                balance_change -= txn.amount
        
        current_balance = account.balance
        initial_balance = current_balance - balance_change
        
        current_date = start_date
        running_balance = initial_balance
        
        transactions_by_date = {}
        for txn in transactions:
            txn_date = txn.timestamp.date()
            if txn_date not in transactions_by_date:
                transactions_by_date[txn_date] = []
            transactions_by_date[txn_date].append(txn)
        
        while current_date <= today:
            labels.append(current_date.strftime('%d/%m'))
            
            if current_date in transactions_by_date:
                for txn in transactions_by_date[current_date]:
                    if txn.transaction_type == DEPOSIT or txn.transaction_type == INTEREST:
                        running_balance += txn.amount
                    elif txn.transaction_type == WITHDRAWAL:
                        running_balance -= txn.amount
            
            data.append(float(running_balance))
            current_date += timedelta(days=1)
        
        return labels, data
