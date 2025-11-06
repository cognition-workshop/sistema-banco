"""
IRPF Report Generation Utilities
"""
import csv
from io import BytesIO, StringIO
from django.core.files import File
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch

from transactions.models import Transaction
from transactions.constants import INTEREST


def generate_irpf_data(account, year):
    """
    Generate IRPF data for a given account and year.
    Returns dictionary with relevant tax information.
    """
    transactions = Transaction.objects.filter(
        account=account,
        transaction_type=INTEREST,
        timestamp__year=year
    ).order_by('timestamp')
    
    total_interest = sum(t.amount for t in transactions)
    
    data = {
        'account': account,
        'year': year,
        'total_interest': total_interest,
        'transactions': transactions,
        'account_holder': account.user.get_full_name(),
        'cpf': account.user.cpf,
        'formatted_account': account.get_formatted_account(),
    }
    
    return data


def generate_irpf_pdf(data):
    """
    Generate PDF report for IRPF declaration.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title = Paragraph(f"<b>Informe de Rendimentos {data['year']}</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.5 * inch))
    
    info_data = [
        ['Titular:', data['account_holder']],
        ['CPF:', data['cpf']],
        ['Conta:', data['formatted_account']],
        ['Ano:', str(data['year'])],
    ]
    
    info_table = Table(info_data, colWidths=[2 * inch, 4 * inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.5 * inch))
    
    summary_title = Paragraph("<b>Rendimentos Tributáveis</b>", styles['Heading2'])
    elements.append(summary_title)
    elements.append(Spacer(1, 0.2 * inch))
    
    summary_data = [
        ['Descrição', 'Valor (R$)'],
        ['Juros sobre Capital Próprio', f"{data['total_interest']:.2f}"],
    ]
    
    summary_table = Table(summary_data, colWidths=[4 * inch, 2 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(summary_table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_irpf_csv(data):
    """
    Generate CSV file for IRPF declaration import.
    """
    buffer = StringIO()
    writer = csv.writer(buffer)
    
    writer.writerow(['Data', 'Tipo', 'Valor', 'Saldo Após'])
    
    for transaction in data['transactions']:
        writer.writerow([
            transaction.timestamp.strftime('%d/%m/%Y'),
            'Juros',
            f"{transaction.amount:.2f}",
            f"{transaction.balance_after_transaction:.2f}"
        ])
    
    writer.writerow([])
    writer.writerow(['Total de Juros', data['total_interest']])
    
    buffer.seek(0)
    return buffer
