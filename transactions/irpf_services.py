from datetime import datetime
from decimal import Decimal
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER
from io import BytesIO
from .models import Transaction
from .irpf_models import IRPFReport
from .constants import DEPOSIT, WITHDRAWAL, INTEREST


class IRPFCalculator:
    
    @classmethod
    def calculate_annual_report(cls, user, year):
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)
        
        transactions = Transaction.objects.filter(
            account__user=user,
            timestamp__range=[start_date, end_date]
        ).order_by('timestamp')
        
        opening_balance = cls._get_balance_at_date(user, start_date)
        
        total_deposits = sum(
            t.amount for t in transactions if t.transaction_type == DEPOSIT
        )
        total_withdrawals = sum(
            t.amount for t in transactions if t.transaction_type == WITHDRAWAL
        )
        total_interest = sum(
            t.amount for t in transactions if t.transaction_type == INTEREST
        )
        
        if year == timezone.now().year:
            closing_balance = user.account.balance if hasattr(user, 'account') else 0
        else:
            last_transaction = transactions.last()
            closing_balance = last_transaction.balance_after_transaction if last_transaction else opening_balance
        
        report, created = IRPFReport.objects.update_or_create(
            user=user,
            year=year,
            defaults={
                'total_deposits': total_deposits,
                'total_withdrawals': total_withdrawals,
                'total_interest': total_interest,
                'opening_balance': opening_balance,
                'closing_balance': closing_balance,
                'transaction_count': transactions.count(),
            }
        )
        
        return report
    
    @classmethod
    def _get_balance_at_date(cls, user, date):
        if not hasattr(user, 'account'):
            return Decimal('0')
        
        last_transaction = Transaction.objects.filter(
            account=user.account,
            timestamp__lt=date
        ).order_by('-timestamp').first()
        
        if last_transaction:
            return last_transaction.balance_after_transaction
        return Decimal('0')
    
    @classmethod
    def generate_irpf_pdf(cls, report):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a202c'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        title = Paragraph(f'Relatório IRPF {report.year}', title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        user_info = [
            ['Contribuinte:', report.user.email],
            ['CPF:', str(report.user.account.account_no) if hasattr(report.user, 'account') else 'N/A'],
            ['Ano de Referência:', str(report.year)],
        ]
        
        user_table = Table(user_info, colWidths=[2*inch, 4*inch])
        user_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f7fafc')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(user_table)
        elements.append(Spacer(1, 0.3*inch))
        
        summary_title = Paragraph('Resumo Financeiro', styles['Heading2'])
        elements.append(summary_title)
        elements.append(Spacer(1, 0.1*inch))
        
        summary_data = [
            ['Descrição', 'Valor (R$)'],
            ['Saldo Inicial (01/01)', f'{report.opening_balance:,.2f}'],
            ['Total de Depósitos', f'{report.total_deposits:,.2f}'],
            ['Total de Saques', f'{report.total_withdrawals:,.2f}'],
            ['Rendimentos (Juros)', f'{report.total_interest:,.2f}'],
            ['Saldo Final (31/12)', f'{report.closing_balance:,.2f}'],
            ['Número de Transações', str(report.transaction_count)],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))
        
        footer_text = f'Relatório gerado em {report.generated_at.strftime("%d/%m/%Y às %H:%M")}'
        footer = Paragraph(footer_text, styles['Normal'])
        elements.append(footer)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
