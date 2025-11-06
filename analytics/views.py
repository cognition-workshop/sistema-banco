from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.db.models import Count, Sum, Avg, Q, Case, When, IntegerField
from django.db.models.functions import ExtractHour, ExtractWeekDay, TruncMonth, TruncDate
from django.utils import timezone
from datetime import datetime, timedelta

from accounts.models import User, BankAccountType, UserBankAccount
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class FinancialOverviewView(StaffRequiredMixin, TemplateView):
    template_name = 'analytics/financial_overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        total_balance = UserBankAccount.objects.aggregate(
            total=Sum('balance')
        )['total'] or 0
        
        deposits_total = Transaction.objects.filter(
            transaction_type=DEPOSIT
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        withdrawals_total = Transaction.objects.filter(
            transaction_type=WITHDRAWAL
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        active_accounts = UserBankAccount.objects.filter(
            balance__gt=0
        ).count()
        
        total_accounts = UserBankAccount.objects.count()
        
        balance_evolution = Transaction.objects.values(
            'timestamp'
        ).annotate(
            date=TruncDate('timestamp')
        ).values('date').annotate(
            balance=Sum('balance_after_transaction')
        ).order_by('date')[:30]
        
        evolution_labels = [item['date'].strftime('%Y-%m-%d') for item in balance_evolution]
        evolution_data = [float(item['balance']) for item in balance_evolution]
        
        context.update({
            'total_balance': total_balance,
            'deposits_total': deposits_total,
            'withdrawals_total': withdrawals_total,
            'active_accounts': active_accounts,
            'total_accounts': total_accounts,
            'evolution_labels': evolution_labels,
            'evolution_data': evolution_data,
        })
        
        return context


class TransactionAnalysisView(StaffRequiredMixin, TemplateView):
    template_name = 'analytics/transaction_analysis.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        volume_by_type = Transaction.objects.values(
            'transaction_type'
        ).annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('transaction_type')
        
        type_labels = []
        type_counts = []
        type_amounts = []
        for item in volume_by_type:
            if item['transaction_type'] == DEPOSIT:
                type_labels.append('Deposit')
            elif item['transaction_type'] == WITHDRAWAL:
                type_labels.append('Withdrawal')
            elif item['transaction_type'] == INTEREST:
                type_labels.append('Interest')
            type_counts.append(item['count'])
            type_amounts.append(float(item['total_amount']))
        
        transactions_by_hour = Transaction.objects.annotate(
            hour=ExtractHour('timestamp')
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('hour')
        
        hour_labels = [f"{item['hour']:02d}:00" for item in transactions_by_hour]
        hour_data = [item['count'] for item in transactions_by_hour]
        
        transactions_by_weekday = Transaction.objects.annotate(
            weekday=ExtractWeekDay('timestamp')
        ).values('weekday').annotate(
            count=Count('id')
        ).order_by('weekday')
        
        weekday_map = {1: 'Sunday', 2: 'Monday', 3: 'Tuesday', 4: 'Wednesday', 
                       5: 'Thursday', 6: 'Friday', 7: 'Saturday'}
        weekday_labels = [weekday_map.get(item['weekday'], str(item['weekday'])) 
                          for item in transactions_by_weekday]
        weekday_data = [item['count'] for item in transactions_by_weekday]
        
        top_users = Transaction.objects.values(
            'account__user__email'
        ).annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('-count')[:10]
        
        user_labels = [item['account__user__email'] for item in top_users]
        user_counts = [item['count'] for item in top_users]
        
        context.update({
            'type_labels': type_labels,
            'type_counts': type_counts,
            'type_amounts': type_amounts,
            'hour_labels': hour_labels,
            'hour_data': hour_data,
            'weekday_labels': weekday_labels,
            'weekday_data': weekday_data,
            'user_labels': user_labels,
            'user_counts': user_counts,
        })
        
        return context


class AccountTypesView(StaffRequiredMixin, TemplateView):
    template_name = 'analytics/account_types.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        accounts_by_type = UserBankAccount.objects.values(
            'account_type__name'
        ).annotate(
            count=Count('id'),
            avg_balance=Avg('balance'),
            total_balance=Sum('balance')
        ).order_by('-count')
        
        type_labels = [item['account_type__name'] for item in accounts_by_type]
        type_counts = [item['count'] for item in accounts_by_type]
        type_avg_balances = [float(item['avg_balance']) for item in accounts_by_type]
        
        account_types = BankAccountType.objects.all()
        
        interest_rate_labels = [acc_type.name for acc_type in account_types]
        interest_rate_data = [float(acc_type.annual_interest_rate) for acc_type in account_types]
        interest_freq_data = [acc_type.interest_calculation_per_year for acc_type in account_types]
        
        context.update({
            'type_labels': type_labels,
            'type_counts': type_counts,
            'type_avg_balances': type_avg_balances,
            'interest_rate_labels': interest_rate_labels,
            'interest_rate_data': interest_rate_data,
            'interest_freq_data': interest_freq_data,
            'account_types': account_types,
            'accounts_by_type': accounts_by_type,
        })
        
        return context


class InterestView(StaffRequiredMixin, TemplateView):
    template_name = 'analytics/interest.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        total_interest = Transaction.objects.filter(
            transaction_type=INTEREST
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        interest_transactions = Transaction.objects.filter(
            transaction_type=INTEREST
        ).count()
        
        eligible_accounts = UserBankAccount.objects.filter(
            balance__gt=0,
            interest_start_date__isnull=False,
            initial_deposit_date__isnull=False
        ).select_related('account_type', 'user')
        
        current_month = timezone.now().month
        accounts_with_upcoming_interest = []
        
        for account in eligible_accounts:
            try:
                calculation_months = account.get_interest_calculation_months()
                if current_month in calculation_months or any(
                    m > current_month for m in calculation_months
                ):
                    next_month = min([m for m in calculation_months if m >= current_month] or [calculation_months[0]])
                    accounts_with_upcoming_interest.append({
                        'account': account,
                        'next_month': next_month,
                        'user_email': account.user.email,
                    })
            except:
                pass
        
        recent_interest = Transaction.objects.filter(
            transaction_type=INTEREST
        ).select_related('account__user').order_by('-timestamp')[:20]
        
        context.update({
            'total_interest': total_interest,
            'interest_transactions': interest_transactions,
            'eligible_accounts_count': eligible_accounts.count(),
            'accounts_with_upcoming_interest': accounts_with_upcoming_interest,
            'recent_interest': recent_interest,
        })
        
        return context


class LimitsView(StaffRequiredMixin, TemplateView):
    template_name = 'analytics/limits.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from django.conf import settings
        
        min_deposit = settings.MINIMUM_DEPOSIT_AMOUNT
        min_withdrawal = settings.MINIMUM_WITHDRAWAL_AMOUNT
        
        low_balance_threshold = min_deposit * 5
        low_balance_accounts = UserBankAccount.objects.filter(
            balance__lt=low_balance_threshold,
            balance__gt=0
        ).select_related('user', 'account_type').order_by('balance')
        
        withdrawals_near_max = Transaction.objects.filter(
            transaction_type=WITHDRAWAL
        ).select_related('account__account_type', 'account__user').order_by('-amount')[:20]
        
        near_limit_withdrawals = []
        for txn in withdrawals_near_max:
            max_withdrawal = txn.account.account_type.maximum_withdrawal_amount
            percentage = (txn.amount / max_withdrawal * 100) if max_withdrawal > 0 else 0
            if percentage >= 80:
                near_limit_withdrawals.append({
                    'transaction': txn,
                    'percentage': round(percentage, 2),
                    'max_amount': max_withdrawal,
                })
        
        recent_large_transactions = Transaction.objects.filter(
            amount__gte=1000
        ).select_related('account__user').order_by('-timestamp')[:20]
        
        context.update({
            'min_deposit': min_deposit,
            'min_withdrawal': min_withdrawal,
            'low_balance_threshold': low_balance_threshold,
            'low_balance_accounts': low_balance_accounts,
            'near_limit_withdrawals': near_limit_withdrawals,
            'recent_large_transactions': recent_large_transactions,
        })
        
        return context


class UsersView(StaffRequiredMixin, TemplateView):
    template_name = 'analytics/users.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        registrations_by_month = User.objects.annotate(
            month=TruncMonth('date_joined')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        month_labels = [item['month'].strftime('%Y-%m') for item in registrations_by_month]
        month_data = [item['count'] for item in registrations_by_month]
        
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = User.objects.filter(is_active=False).count()
        
        gender_distribution = UserBankAccount.objects.values(
            'gender'
        ).annotate(
            count=Count('id')
        )
        
        gender_labels = []
        gender_data = []
        for item in gender_distribution:
            if item['gender'] == 'M':
                gender_labels.append('Male')
            elif item['gender'] == 'F':
                gender_labels.append('Female')
            else:
                gender_labels.append('Other')
            gender_data.append(item['count'])
        
        total_users = User.objects.count()
        users_with_accounts = UserBankAccount.objects.count()
        
        recent_users = User.objects.select_related('account').order_by('-date_joined')[:10]
        
        context.update({
            'month_labels': month_labels,
            'month_data': month_data,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'gender_labels': gender_labels,
            'gender_data': gender_data,
            'total_users': total_users,
            'users_with_accounts': users_with_accounts,
            'recent_users': recent_users,
        })
        
        return context
