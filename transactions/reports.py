from datetime import datetime
from decimal import Decimal
from django.db.models import Sum, Q
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
import csv
from io import BytesIO, StringIO
from .models import Transaction
from .constants import INTEREST


class IRPFReportGenerator:
    def __init__(self, user, year):
        self.user = user
        self.year = year
    
    def get_interest_transactions(self):
        return Transaction.objects.filter(
            account__user=self.user,
            transaction_type=INTEREST,
            timestamp__year=self.year
        ).order_by('timestamp')
    
    def calculate_annual_interest(self):
        total = self.get_interest_transactions().aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        return total
    
    def get_monthly_breakdown(self):
        monthly_data = {}
        for month in range(1, 13):
            month_total = self.get_interest_transactions().filter(
                timestamp__month=month
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            monthly_data[month] = month_total
        return monthly_data
    
    def generate_pdf(self):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        title = Paragraph(
            f"<b>Relatório IRPF {self.year}</b><br/>Rendimentos de Juros",
            styles['Title']
        )
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        user_info = [
            ['Nome:', f'{self.user.first_name} {self.user.last_name}'],
            ['CPF:', self.user.get_formatted_cpf()],
            ['Email:', self.user.email],
            ['Conta:', self.user.account.get_formatted_account() if hasattr(self.user, 'account') else 'N/A'],
        ]
        
        user_table = Table(user_info, colWidths=[80*mm, 100*mm])
        user_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(user_table)
        elements.append(Spacer(1, 20))
        
        monthly_breakdown = self.get_monthly_breakdown()
        month_names = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        
        monthly_data = [['Mês', 'Juros Recebidos (R$)']]
        for month, amount in monthly_breakdown.items():
            monthly_data.append([month_names[month-1], f'R$ {amount:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')])
        
        monthly_table = Table(monthly_data, colWidths=[100*mm, 80*mm])
        monthly_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(monthly_table)
        elements.append(Spacer(1, 20))
        
        total_annual = self.calculate_annual_interest()
        total_info = Paragraph(
            f"<b>Total Anual de Juros: R$ {total_annual:,.2f}</b>".replace(',', 'X').replace('.', ',').replace('X', '.'),
            styles['Heading2']
        )
        elements.append(total_info)
        elements.append(Spacer(1, 20))
        
        instructions = Paragraph(
            "<b>Instruções para Declaração:</b><br/>"
            "1. Declare este valor na ficha de 'Rendimentos Sujeitos à Tributação Exclusiva/Definitiva'<br/>"
            "2. Código 06 - Rendimentos de aplicações financeiras<br/>"
            "3. Informe o valor total anual de juros recebidos<br/>"
            "4. Guarde este comprovante junto com sua documentação fiscal",
            styles['Normal']
        )
        elements.append(instructions)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def generate_csv(self):
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Relatório IRPF', self.year])
        writer.writerow(['Nome', f'{self.user.first_name} {self.user.last_name}'])
        writer.writerow(['CPF', self.user.get_formatted_cpf()])
        writer.writerow(['Email', self.user.email])
        writer.writerow([])
        
        writer.writerow(['Mês', 'Juros Recebidos (R$)'])
        monthly_breakdown = self.get_monthly_breakdown()
        month_names = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        
        for month, amount in monthly_breakdown.items():
            writer.writerow([month_names[month-1], f'{amount:.2f}'])
        
        writer.writerow([])
        total_annual = self.calculate_annual_interest()
        writer.writerow(['Total Anual', f'{total_annual:.2f}'])
        
        return output.getvalue()
