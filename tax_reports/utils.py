from decimal import Decimal
from datetime import date
from django.db.models import Sum, Q
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST, PIX_TRANSFER
from .models import AnnualTaxReport


def calculate_annual_totals(account, year):
    """
    Calculate annual transaction totals for tax reporting.
    """
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    transactions = Transaction.objects.filter(
        account=account,
        timestamp__date__range=[start_date, end_date]
    )
    
    totals = {
        'total_deposits': transactions.filter(
            transaction_type=DEPOSIT
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0'),
        
        'total_withdrawals': transactions.filter(
            transaction_type=WITHDRAWAL
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0'),
        
        'total_interest': transactions.filter(
            transaction_type=INTEREST
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0'),
        
        'total_pix_received': transactions.filter(
            transaction_type=PIX_TRANSFER,
            pix_transaction__receiver_account=account
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0'),
        
        'total_pix_sent': transactions.filter(
            transaction_type=PIX_TRANSFER,
            pix_transaction__sender_account=account
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0'),
    }
    
    previous_year_last = Transaction.objects.filter(
        account=account,
        timestamp__date__lt=start_date
    ).order_by('-timestamp').first()
    
    totals['opening_balance'] = (
        previous_year_last.balance_after_transaction 
        if previous_year_last else Decimal('0')
    )
    
    current_year_last = transactions.order_by('-timestamp').first()
    totals['closing_balance'] = (
        current_year_last.balance_after_transaction
        if current_year_last else totals['opening_balance']
    )
    
    return totals


def generate_tax_report(account, year):
    """
    Generate or update annual tax report.
    """
    totals = calculate_annual_totals(account, year)
    
    report, created = AnnualTaxReport.objects.update_or_create(
        account=account,
        year=year,
        defaults=totals
    )
    
    return report


def generate_pdf_report(report):
    """
    Generate PDF file for tax report using reportlab.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from io import BytesIO
    from django.core.files import File
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title = Paragraph(
        f"Relatório de Imposto de Renda - Ano {report.year}",
        styles['Title']
    )
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    account_info = Paragraph(
        f"Conta: {report.account.account_no}<br/>Titular: {report.account.user.get_full_name()}",
        styles['Normal']
    )
    elements.append(account_info)
    elements.append(Spacer(1, 20))
    
    data = [
        ['Descrição', 'Valor (R$)'],
        ['Saldo Inicial', f'{report.opening_balance:.2f}'],
        ['Total de Depósitos', f'{report.total_deposits:.2f}'],
        ['Total de Saques', f'{report.total_withdrawals:.2f}'],
        ['Juros Recebidos', f'{report.total_interest:.2f}'],
        ['PIX Recebidos', f'{report.total_pix_received:.2f}'],
        ['PIX Enviados', f'{report.total_pix_sent:.2f}'],
        ['Saldo Final', f'{report.closing_balance:.2f}'],
    ]
    
    table = Table(data, colWidths=[300, 150])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 30))
    
    footer = Paragraph(
        f"Relatório gerado em {report.generated_at.strftime('%d/%m/%Y às %H:%M')}",
        styles['Normal']
    )
    elements.append(footer)
    
    doc.build(elements)
    
    buffer.seek(0)
    filename = f'irpf_{report.year}_{report.account.account_no}.pdf'
    report.pdf_file.save(filename, File(buffer), save=True)
    buffer.close()
    
    return report
