from celery import task
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from datetime import datetime
from decimal import Decimal
from transactions.models import Transaction
from transactions.constants import INTEREST, DEPOSIT, WITHDRAWAL
from .models import RelatorioIRPF
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from io import BytesIO

User = get_user_model()


@task(name="gerar_relatorios_irpf")
def gerar_relatorios_irpf(ano):
    """Generate IRPF reports for all users for a given year"""
    
    for user in User.objects.filter(account__isnull=False):
        try:
            transactions = Transaction.objects.filter(
                account__user=user,
                timestamp__year=ano
            )
            
            rendimentos_juros = sum(
                t.amount for t in transactions if t.transaction_type == INTEREST
            ) or Decimal('0')
            
            total_depositado = sum(
                t.amount for t in transactions if t.transaction_type == DEPOSIT
            ) or Decimal('0')
            
            total_sacado = sum(
                t.amount for t in transactions if t.transaction_type == WITHDRAWAL
            ) or Decimal('0')
            
            try:
                last_transaction = transactions.filter(
                    timestamp__lte=datetime(ano, 12, 31, 23, 59, 59)
                ).latest('timestamp')
                saldo_31_dezembro = last_transaction.balance_after_transaction
            except Transaction.DoesNotExist:
                saldo_31_dezembro = Decimal('0')
            
            relatorio, created = RelatorioIRPF.objects.update_or_create(
                usuario=user,
                ano_calendario=ano,
                defaults={
                    'rendimentos_juros': rendimentos_juros,
                    'total_depositado': total_depositado,
                    'total_sacado': total_sacado,
                    'saldo_31_dezembro': saldo_31_dezembro,
                }
            )
            
            pdf_content = gerar_pdf_irpf(user, relatorio, ano)
            relatorio.arquivo_pdf.save(
                f'irpf_{ano}_{user.id}.pdf',
                ContentFile(pdf_content),
                save=True
            )
            
        except Exception as e:
            print(f"Error generating IRPF for user {user.email}: {e}")
            continue
    
    return f"Generated IRPF reports for {ano}"


def gerar_pdf_irpf(user, relatorio, ano):
    """Generate PDF report using reportlab"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title = Paragraph(f"<b>INFORME DE RENDIMENTOS {ano}</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    user_info = [
        ['Nome:', f"{user.first_name} {user.last_name}"],
        ['CPF:', user.cpf if hasattr(user, 'cpf') and user.cpf else 'N/A'],
        ['Email:', user.email],
    ]
    
    user_table = Table(user_info, colWidths=[150, 350])
    user_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(user_table)
    elements.append(Spacer(1, 20))
    
    financial_data = [
        ['Descrição', 'Valor (R$)'],
        ['Rendimentos de Juros (Código 06)', f'{relatorio.rendimentos_juros:.2f}'],
        ['Total Depositado', f'{relatorio.total_depositado:.2f}'],
        ['Total Sacado', f'{relatorio.total_sacado:.2f}'],
        ['Saldo em 31/12', f'{relatorio.saldo_31_dezembro:.2f}'],
    ]
    
    financial_table = Table(financial_data, colWidths=[300, 200])
    financial_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(financial_table)
    
    doc.build(elements)
    
    pdf_content = buffer.getvalue()
    buffer.close()
    return pdf_content
