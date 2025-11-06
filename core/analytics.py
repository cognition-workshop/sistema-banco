import csv
from datetime import timedelta
from io import BytesIO
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncDate, TruncMonth
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from transactions.models import Transaction
from accounts.models import UserBankAccount
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST


class AnalyticsService:
    
    @staticmethod
    def get_transaction_volume_by_period(days=30):
        start_date = timezone.now() - timedelta(days=days)
        return Transaction.objects.filter(
            timestamp__gte=start_date
        ).annotate(
            date=TruncDate('timestamp')
        ).values('date').annotate(
            total_amount=Sum('amount'),
            count=Count('id'),
            deposits=Count('id', filter=Q(transaction_type=DEPOSIT)),
            withdrawals=Count('id', filter=Q(transaction_type=WITHDRAWAL)),
        ).order_by('date')
    
    @staticmethod
    def get_balance_growth_data(days=30):
        start_date = timezone.now() - timedelta(days=days)
        transactions = Transaction.objects.filter(
            timestamp__gte=start_date
        ).order_by('timestamp')
        
        data = []
        for transaction in transactions:
            data.append({
                'date': transaction.timestamp.date(),
                'account_no': transaction.account.account_no,
                'balance': transaction.balance_after_transaction,
            })
        return data
    
    @staticmethod
    def get_transaction_type_distribution():
        return Transaction.objects.values('transaction_type').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
    
    @staticmethod
    def get_top_accounts_by_balance(limit=10):
        return UserBankAccount.objects.order_by('-balance')[:limit]
    
    @staticmethod
    def export_to_csv(queryset, filename='report.csv'):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        
        if queryset.exists():
            fields = [field.name for field in queryset.model._meta.fields]
            writer.writerow(fields)
            
            for obj in queryset:
                writer.writerow([getattr(obj, field) for field in fields])
        
        return response
    
    @staticmethod
    def export_to_excel(queryset, filename='report.xlsx'):
        data = list(queryset.values())
        df = pd.DataFrame(data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Report', index=False)
        
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    @staticmethod
    def export_to_pdf(data, title='Report', filename='report.pdf'):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        styles = getSampleStyleSheet()
        
        title_paragraph = Paragraph(title, styles['Title'])
        elements.append(title_paragraph)
        elements.append(Spacer(1, 12))
        
        if data:
            table_data = [list(data[0].keys())]
            for row in data:
                table_data.append(list(row.values()))
            
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
        
        doc.build(elements)
        
        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
