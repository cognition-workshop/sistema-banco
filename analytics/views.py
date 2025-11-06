import csv
import io
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import TemplateView, View

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

from accounts.models import UserBankAccount
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST


class DashboardView(TemplateView):
    template_name = 'analytics/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if not demo_user or not hasattr(demo_user, 'account'):
            context.update({
                'total_transactions': 0,
                'total_deposits': 0,
                'total_withdrawals': 0,
                'total_interest': 0,
                'total_accounts': 0,
                'total_balance': 0,
                'recent_transactions_count': 0,
                'chart_data': {},
            })
            return context
        
        account = demo_user.account
        
        transactions = Transaction.objects.filter(account=account)
        
        deposit_stats = transactions.filter(
            transaction_type=DEPOSIT
        ).aggregate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        withdrawal_stats = transactions.filter(
            transaction_type=WITHDRAWAL
        ).aggregate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        interest_stats = transactions.filter(
            transaction_type=INTEREST
        ).aggregate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_transactions = transactions.filter(
            timestamp__gte=thirty_days_ago
        )
        
        daily_transactions = {}
        for transaction in transactions.order_by('timestamp'):
            date_key = transaction.timestamp.strftime('%Y-%m-%d')
            if date_key not in daily_transactions:
                daily_transactions[date_key] = {
                    'deposits': 0,
                    'withdrawals': 0,
                    'interest': 0,
                }
            
            if transaction.transaction_type == DEPOSIT:
                daily_transactions[date_key]['deposits'] += 1
            elif transaction.transaction_type == WITHDRAWAL:
                daily_transactions[date_key]['withdrawals'] += 1
            elif transaction.transaction_type == INTEREST:
                daily_transactions[date_key]['interest'] += 1
        
        context.update({
            'account': account,
            'total_transactions': transactions.count(),
            'total_deposits': deposit_stats['count'] or 0,
            'total_withdrawals': withdrawal_stats['count'] or 0,
            'total_interest': interest_stats['count'] or 0,
            'deposit_amount': deposit_stats['total'] or Decimal('0'),
            'withdrawal_amount': withdrawal_stats['total'] or Decimal('0'),
            'interest_amount': interest_stats['total'] or Decimal('0'),
            'total_accounts': UserBankAccount.objects.count(),
            'total_balance': account.balance,
            'recent_transactions_count': recent_transactions.count(),
            'chart_dates': list(daily_transactions.keys()),
            'chart_deposits': [daily_transactions[d]['deposits'] for d in daily_transactions.keys()],
            'chart_withdrawals': [daily_transactions[d]['withdrawals'] for d in daily_transactions.keys()],
            'chart_interest': [daily_transactions[d]['interest'] for d in daily_transactions.keys()],
        })
        
        return context


class ExportCSVView(View):
    def get(self, request, *args, **kwargs):
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if not demo_user or not hasattr(demo_user, 'account'):
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
            writer = csv.writer(response)
            writer.writerow(['No data available'])
            return response
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Account Number',
            'Transaction Type',
            'Amount',
            'Balance After Transaction',
            'Timestamp'
        ])
        
        transactions = Transaction.objects.filter(
            account=demo_user.account
        ).order_by('timestamp')
        
        for transaction in transactions:
            writer.writerow([
                transaction.account.account_no,
                transaction.get_transaction_type_display(),
                f'${transaction.amount}',
                f'${transaction.balance_after_transaction}',
                transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response


class ExportPDFView(View):
    def get(self, request, *args, **kwargs):
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="banking_analytics_report.pdf"'
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        
        elements = []
        styles = getSampleStyleSheet()
        
        title = Paragraph("Banking Analytics Report", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        if not demo_user or not hasattr(demo_user, 'account'):
            no_data = Paragraph("No data available", styles['Normal'])
            elements.append(no_data)
            doc.build(elements)
            pdf = buffer.getvalue()
            buffer.close()
            response.write(pdf)
            return response
        
        account = demo_user.account
        transactions = Transaction.objects.filter(account=account)
        
        deposit_count = transactions.filter(transaction_type=DEPOSIT).count()
        withdrawal_count = transactions.filter(transaction_type=WITHDRAWAL).count()
        interest_count = transactions.filter(transaction_type=INTEREST).count()
        
        summary_text = f"""
        <b>Account Summary</b><br/>
        Account Number: {account.account_no}<br/>
        Current Balance: ${account.balance}<br/>
        Total Transactions: {transactions.count()}<br/>
        Deposits: {deposit_count}<br/>
        Withdrawals: {withdrawal_count}<br/>
        Interest Payments: {interest_count}<br/>
        """
        
        summary = Paragraph(summary_text, styles['Normal'])
        elements.append(summary)
        elements.append(Spacer(1, 0.3*inch))
        
        recent_transactions = transactions.order_by('-timestamp')[:10]
        
        if recent_transactions.exists():
            elements.append(Paragraph("Recent Transactions", styles['Heading2']))
            elements.append(Spacer(1, 0.2*inch))
            
            data = [['Type', 'Amount', 'Balance After', 'Date']]
            
            for transaction in recent_transactions:
                data.append([
                    transaction.get_transaction_type_display(),
                    f'${transaction.amount}',
                    f'${transaction.balance_after_transaction}',
                    transaction.timestamp.strftime('%Y-%m-%d')
                ])
            
            table = Table(data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
        
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        
        return response


class ExportExcelView(View):
    def get(self, request, *args, **kwargs):
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        wb = Workbook()
        
        ws_summary = wb.active
        ws_summary.title = "Summary"
        
        ws_summary['A1'] = 'Banking Analytics Summary'
        ws_summary['A1'].font = Font(size=16, bold=True)
        
        if not demo_user or not hasattr(demo_user, 'account'):
            ws_summary['A3'] = 'No data available'
            
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="banking_analytics.xlsx"'
            wb.save(response)
            return response
        
        account = demo_user.account
        transactions = Transaction.objects.filter(account=account)
        
        deposit_stats = transactions.filter(transaction_type=DEPOSIT).aggregate(
            count=Count('id'),
            total=Sum('amount')
        )
        withdrawal_stats = transactions.filter(transaction_type=WITHDRAWAL).aggregate(
            count=Count('id'),
            total=Sum('amount')
        )
        interest_stats = transactions.filter(transaction_type=INTEREST).aggregate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        ws_summary['A3'] = 'Account Number:'
        ws_summary['B3'] = account.account_no
        ws_summary['A4'] = 'Current Balance:'
        ws_summary['B4'] = float(account.balance)
        ws_summary['A5'] = 'Total Transactions:'
        ws_summary['B5'] = transactions.count()
        
        ws_summary['A7'] = 'Transaction Type'
        ws_summary['B7'] = 'Count'
        ws_summary['C7'] = 'Total Amount'
        ws_summary['A7'].font = Font(bold=True)
        ws_summary['B7'].font = Font(bold=True)
        ws_summary['C7'].font = Font(bold=True)
        
        ws_summary['A8'] = 'Deposits'
        ws_summary['B8'] = deposit_stats['count'] or 0
        ws_summary['C8'] = float(deposit_stats['total'] or 0)
        
        ws_summary['A9'] = 'Withdrawals'
        ws_summary['B9'] = withdrawal_stats['count'] or 0
        ws_summary['C9'] = float(withdrawal_stats['total'] or 0)
        
        ws_summary['A10'] = 'Interest'
        ws_summary['B10'] = interest_stats['count'] or 0
        ws_summary['C10'] = float(interest_stats['total'] or 0)
        
        ws_transactions = wb.create_sheet(title="Transactions")
        
        headers = ['Account Number', 'Transaction Type', 'Amount', 'Balance After', 'Timestamp']
        ws_transactions.append(headers)
        
        for cell in ws_transactions[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        for transaction in transactions.order_by('timestamp'):
            ws_transactions.append([
                transaction.account.account_no,
                transaction.get_transaction_type_display(),
                float(transaction.amount),
                float(transaction.balance_after_transaction),
                transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        for column in ws_transactions.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws_transactions.column_dimensions[column_letter].width = adjusted_width
        
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="banking_analytics.xlsx"'
        
        wb.save(response)
        
        return response
