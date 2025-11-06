from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.utils import timezone
from django.db import models
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import csv
from datetime import datetime

from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST

User = get_user_model()


class RelatorioIRPFView(TemplateView):
    template_name = 'reports/irpf_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        ano = self.request.GET.get('ano', timezone.now().year)
        ano = int(ano)
        
        demo_user = User.objects.filter(email='demo@example.com').first()
        if not demo_user or not hasattr(demo_user, 'account'):
            context['error'] = 'Conta não encontrada'
            return context
        
        account = demo_user.account
        
        transacoes = Transaction.objects.filter(
            account=account,
            timestamp__year=ano
        )
        
        depositos = transacoes.filter(transaction_type=DEPOSIT).aggregate(
            models.Sum('amount')
        )['amount__sum'] or 0
        
        saques = transacoes.filter(transaction_type=WITHDRAWAL).aggregate(
            models.Sum('amount')
        )['amount__sum'] or 0
        
        rendimentos = transacoes.filter(transaction_type=INTEREST).aggregate(
            models.Sum('amount')
        )['amount__sum'] or 0
        
        saldo_final = account.balance
        
        limite_receita = 10000
        transacoes_relevantes = transacoes.filter(
            amount__gte=limite_receita
        )
        
        context.update({
            'ano': ano,
            'account': account,
            'depositos_total': depositos,
            'saques_total': saques,
            'rendimentos_total': rendimentos,
            'saldo_final': saldo_final,
            'transacoes_relevantes': transacoes_relevantes,
            'limite_receita': limite_receita,
            'anos_disponiveis': range(2020, timezone.now().year + 1),
        })
        
        return context


def exportar_irpf_pdf(request):
    """Export IRPF report as PDF"""
    ano = int(request.GET.get('ano', timezone.now().year))
    
    demo_user = User.objects.filter(email='demo@example.com').first()
    if not demo_user or not hasattr(demo_user, 'account'):
        return HttpResponse('Conta não encontrada', status=404)
    
    account = demo_user.account
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="irpf_{ano}_{account.cpf}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title = Paragraph(f'<b>Relatório IRPF - Ano {ano}</b>', styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.5*cm))
    
    info_data = [
        ['CPF:', account.cpf],
        ['Nome:', f'{account.user.first_name} {account.user.last_name}'],
        ['Agência:', account.agencia],
        ['Conta:', f'{account.conta}-{account.digito_verificador}'],
    ]
    info_table = Table(info_data, colWidths=[4*cm, 12*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 1*cm))
    
    transacoes = Transaction.objects.filter(
        account=account,
        timestamp__year=ano
    )
    
    depositos = transacoes.filter(transaction_type=DEPOSIT).aggregate(
        models.Sum('amount')
    )['amount__sum'] or 0
    
    saques = transacoes.filter(transaction_type=WITHDRAWAL).aggregate(
        models.Sum('amount')
    )['amount__sum'] or 0
    
    rendimentos = transacoes.filter(transaction_type=INTEREST).aggregate(
        models.Sum('amount')
    )['amount__sum'] or 0
    
    summary_data = [
        ['Descrição', 'Valor (R$)'],
        ['Total de Depósitos', f'{depositos:,.2f}'],
        ['Total de Saques', f'{saques:,.2f}'],
        ['Rendimentos (Juros)', f'{rendimentos:,.2f}'],
        ['Saldo em 31/12', f'{account.balance:,.2f}'],
    ]
    
    summary_table = Table(summary_data, colWidths=[10*cm, 6*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 1*cm))
    
    note = Paragraph(
        '<b>Nota:</b> Movimentações acima de R$ 10.000,00 devem ser declaradas à Receita Federal.',
        styles['Normal']
    )
    elements.append(note)
    
    doc.build(elements)
    return response


def exportar_irpf_csv(request):
    """Export IRPF report as CSV"""
    ano = int(request.GET.get('ano', timezone.now().year))
    
    demo_user = User.objects.filter(email='demo@example.com').first()
    if not demo_user or not hasattr(demo_user, 'account'):
        return HttpResponse('Conta não encontrada', status=404)
    
    account = demo_user.account
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="irpf_{ano}_{account.cpf}.csv"'
    
    writer = csv.writer(response)
    
    writer.writerow(['Relatório IRPF', f'Ano {ano}'])
    writer.writerow([])
    writer.writerow(['CPF', account.cpf])
    writer.writerow(['Nome', f'{account.user.first_name} {account.user.last_name}'])
    writer.writerow(['Agência', account.agencia])
    writer.writerow(['Conta', f'{account.conta}-{account.digito_verificador}'])
    writer.writerow([])
    
    transacoes = Transaction.objects.filter(
        account=account,
        timestamp__year=ano
    )
    
    depositos = transacoes.filter(transaction_type=DEPOSIT).aggregate(
        models.Sum('amount')
    )['amount__sum'] or 0
    
    saques = transacoes.filter(transaction_type=WITHDRAWAL).aggregate(
        models.Sum('amount')
    )['amount__sum'] or 0
    
    rendimentos = transacoes.filter(transaction_type=INTEREST).aggregate(
        models.Sum('amount')
    )['amount__sum'] or 0
    
    writer.writerow(['Descrição', 'Valor (R$)'])
    writer.writerow(['Total de Depósitos', f'{depositos:.2f}'])
    writer.writerow(['Total de Saques', f'{saques:.2f}'])
    writer.writerow(['Rendimentos (Juros)', f'{rendimentos:.2f}'])
    writer.writerow(['Saldo em 31/12', f'{account.balance:.2f}'])
    writer.writerow([])
    
    writer.writerow(['Transações acima de R$ 10.000,00'])
    writer.writerow(['Data', 'Tipo', 'Valor (R$)', 'Saldo Após'])
    
    transacoes_relevantes = transacoes.filter(amount__gte=10000)
    for t in transacoes_relevantes:
        writer.writerow([
            t.timestamp.strftime('%d/%m/%Y %H:%M'),
            t.get_transaction_type_display(),
            f'{t.amount:.2f}',
            f'{t.balance_after_transaction:.2f}'
        ])
    
    return response
