from datetime import date, timedelta
from decimal import Decimal
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.template.loader import render_to_string
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from transactions.models import Transaction
from transactions.constants import INTEREST


def generate_ir_report(account, year):
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    interest_transactions = Transaction.objects.filter(
        account=account,
        transaction_type=INTEREST,
        timestamp__gte=start_date,
        timestamp__lte=end_date
    ).order_by('timestamp')
    
    total_interest = interest_transactions.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    report_data = {
        'account': account,
        'user': account.user if hasattr(account, 'user') else None,
        'year': year,
        'total_interest': total_interest,
        'transactions': interest_transactions,
        'transaction_count': interest_transactions.count(),
        'generated_date': date.today(),
    }
    
    return report_data


def export_ir_report_pdf(account, year):
    report_data = generate_ir_report(account, year)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="relatorio_ir_{year}_conta_{account.account_no}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=30,
    )
    
    title = Paragraph(f'Relatório de Rendimentos - Imposto de Renda {year}', title_style)
    story.append(title)
    story.append(Spacer(1, 0.5*cm))
    
    info_data = [
        ['Instituição Financeira:', 'Sistema Bancário Digital'],
        ['CNPJ:', '00.000.000/0001-00'],
        ['', ''],
        ['Contribuinte:', report_data['user'].get_full_name() if report_data['user'] else 'N/A'],
        ['CPF:', account.cpf if hasattr(account, 'cpf') and account.cpf else 'N/A'],
        ['Conta:', f"#{account.account_no}"],
        ['Tipo de Conta:', account.account_type.name],
        ['', ''],
        ['Ano Base:', str(year)],
        ['Total de Transações:', str(report_data['transaction_count'])],
        ['', ''],
        ['TOTAL DE RENDIMENTOS:', f"R$ {report_data['total_interest']:.2f}"],
    ]
    
    info_table = Table(info_data, colWidths=[5*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 12),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#059669')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 1*cm))
    
    if report_data['transactions']:
        story.append(Paragraph('Detalhamento dos Rendimentos', styles['Heading2']))
        story.append(Spacer(1, 0.3*cm))
        
        transaction_data = [['Data', 'Valor', 'Saldo Após']]
        for trans in report_data['transactions']:
            transaction_data.append([
                trans.timestamp.strftime('%d/%m/%Y'),
                f"R$ {trans.amount:.2f}",
                f"R$ {trans.balance_after_transaction:.2f}",
            ])
        
        trans_table = Table(transaction_data, colWidths=[4*cm, 4*cm, 4*cm])
        trans_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F3F4F6')]),
        ]))
        
        story.append(trans_table)
    
    story.append(Spacer(1, 1*cm))
    footer_text = f"Relatório gerado em {report_data['generated_date'].strftime('%d/%m/%Y')} às {date.today().strftime('%H:%M')}"
    footer = Paragraph(footer_text, styles['Normal'])
    story.append(footer)
    
    doc.build(story)
    return response
