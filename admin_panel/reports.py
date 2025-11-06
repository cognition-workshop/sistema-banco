try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

import csv
from io import BytesIO, StringIO
from django.utils import timezone


class ReportGenerator:
    
    def generate_transaction_csv(self, transactions):
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'ID', 'Account Number', 'User Email', 'Amount', 'Type', 
            'Date', 'Balance After'
        ])
        
        for t in transactions:
            writer.writerow([
                t.id,
                t.account.account_no,
                t.account.user.email,
                str(t.amount),
                t.get_transaction_type_display(),
                t.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                str(t.balance_after_transaction)
            ])
        
        return output.getvalue()
    
    def generate_transaction_pdf(self, transactions):
        if not REPORTLAB_AVAILABLE:
            raise ImportError(
                "reportlab is not installed. PDF generation is not available. "
                "Install system dependencies (libfreetype6-dev libjpeg-dev) and "
                "run: pip install reportlab==3.6.12"
            )
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        title = Paragraph("Transaction Report", title_style)
        elements.append(title)
        
        subtitle = Paragraph(
            f"Generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles['Normal']
        )
        elements.append(subtitle)
        elements.append(Spacer(1, 0.3*inch))
        
        data = [['ID', 'Account', 'Amount', 'Type', 'Date']]
        
        for t in transactions[:100]:
            data.append([
                str(t.id),
                str(t.account.account_no),
                f"${t.amount}",
                t.get_transaction_type_display(),
                t.timestamp.strftime('%Y-%m-%d %H:%M')
            ])
        
        table = Table(data, colWidths=[0.8*inch, 1.5*inch, 1.2*inch, 1.5*inch, 1.8*inch])
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        elements.append(table)
        
        doc.build(elements)
        
        pdf_value = buffer.getvalue()
        buffer.close()
        return pdf_value
    
    def generate_fraud_alerts_csv(self, alerts):
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'Alert ID', 'Transaction ID', 'Account Number', 'Rule Name', 
            'Severity', 'Status', 'Detected At', 'Reviewed By'
        ])
        
        for alert in alerts:
            writer.writerow([
                alert.id,
                alert.transaction.id,
                alert.transaction.account.account_no,
                alert.rule.name,
                alert.rule.severity,
                alert.get_status_display(),
                alert.detected_at.strftime('%Y-%m-%d %H:%M:%S'),
                alert.reviewed_by.user.email if alert.reviewed_by else 'N/A'
            ])
        
        return output.getvalue()
