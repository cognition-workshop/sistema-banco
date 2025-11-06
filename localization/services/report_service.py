import csv
from io import StringIO, BytesIO
from datetime import datetime
from decimal import Decimal
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm

from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST


class ReportService:
    """Serviço para geração de relatórios IRPF"""
    
    @staticmethod
    def gerar_relatorio_irpf(usuario, ano):
        """Gera relatório anual para IRPF"""
        data_inicio = datetime(ano, 1, 1, 0, 0, 0, tzinfo=timezone.get_current_timezone())
        data_fim = datetime(ano, 12, 31, 23, 59, 59, tzinfo=timezone.get_current_timezone())
        
        transacoes = Transaction.objects.filter(
            account__user=usuario,
            timestamp__range=(data_inicio, data_fim)
        ).order_by('timestamp')
        
        total_depositos = Decimal('0.00')
        total_saques = Decimal('0.00')
        total_juros = Decimal('0.00')
        
        movimentacoes = []
        
        for transacao in transacoes:
            if transacao.transaction_type == DEPOSIT:
                total_depositos += transacao.amount
                tipo = 'Depósito'
            elif transacao.transaction_type == WITHDRAWAL:
                total_saques += transacao.amount
                tipo = 'Saque'
            elif transacao.transaction_type == INTEREST:
                total_juros += transacao.amount
                tipo = 'Rendimento'
            else:
                tipo = 'Outro'
            
            movimentacoes.append({
                'data': transacao.timestamp,
                'tipo': tipo,
                'valor': transacao.amount,
                'saldo': transacao.balance_after_transaction
            })
        
        return {
            'usuario': usuario,
            'ano': ano,
            'cpf': usuario.cpf if hasattr(usuario, 'cpf') and usuario.cpf else 'N/A',
            'total_depositos': total_depositos,
            'total_saques': total_saques,
            'total_juros': total_juros,
            'saldo_inicial': movimentacoes[0]['saldo'] - movimentacoes[0]['valor'] if movimentacoes else Decimal('0.00'),
            'saldo_final': movimentacoes[-1]['saldo'] if movimentacoes else Decimal('0.00'),
            'movimentacoes': movimentacoes,
            'quantidade_transacoes': len(movimentacoes)
        }
    
    @staticmethod
    def exportar_csv(relatorio):
        """Exporta relatório para CSV"""
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Relatório IRPF - Ano {}'.format(relatorio['ano'])])
        writer.writerow(['CPF', relatorio['cpf']])
        writer.writerow(['Nome', f"{relatorio['usuario'].first_name} {relatorio['usuario'].last_name}"])
        writer.writerow([])
        
        writer.writerow(['Resumo Anual'])
        writer.writerow(['Total Depósitos', f"R$ {relatorio['total_depositos']:.2f}"])
        writer.writerow(['Total Saques', f"R$ {relatorio['total_saques']:.2f}"])
        writer.writerow(['Total Rendimentos', f"R$ {relatorio['total_juros']:.2f}"])
        writer.writerow(['Saldo Inicial', f"R$ {relatorio['saldo_inicial']:.2f}"])
        writer.writerow(['Saldo Final', f"R$ {relatorio['saldo_final']:.2f}"])
        writer.writerow([])
        
        writer.writerow(['Data', 'Tipo', 'Valor', 'Saldo'])
        for mov in relatorio['movimentacoes']:
            writer.writerow([
                mov['data'].strftime('%d/%m/%Y %H:%M'),
                mov['tipo'],
                f"R$ {mov['valor']:.2f}",
                f"R$ {mov['saldo']:.2f}"
            ])
        
        return output.getvalue()
    
    @staticmethod
    def exportar_pdf(relatorio):
        """Exporta relatório para PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        styles = getSampleStyleSheet()
        
        titulo = Paragraph(
            f"<b>Relatório IRPF - Ano {relatorio['ano']}</b>",
            styles['Title']
        )
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        info_data = [
            ['CPF:', relatorio['cpf']],
            ['Nome:', f"{relatorio['usuario'].first_name} {relatorio['usuario'].last_name}"],
            ['Email:', relatorio['usuario'].email]
        ]
        info_table = Table(info_data, colWidths=[3*cm, 12*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.5*cm))
        
        resumo_data = [
            ['Resumo Anual', ''],
            ['Total Depósitos', f"R$ {relatorio['total_depositos']:.2f}"],
            ['Total Saques', f"R$ {relatorio['total_saques']:.2f}"],
            ['Total Rendimentos', f"R$ {relatorio['total_juros']:.2f}"],
            ['Saldo Inicial', f"R$ {relatorio['saldo_inicial']:.2f}"],
            ['Saldo Final', f"R$ {relatorio['saldo_final']:.2f}"]
        ]
        resumo_table = Table(resumo_data, colWidths=[8*cm, 7*cm])
        resumo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(resumo_table)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
