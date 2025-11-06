from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO


def gerar_pdf_irpf(relatorio):
    """Generate IRPF PDF report."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#003366'),
        spaceAfter=30,
        alignment=1
    )
    
    elements.append(Paragraph(
        f"Relatório de Rendimentos {relatorio.ano_calendario}",
        title_style
    ))
    elements.append(Spacer(1, 0.5*cm))
    
    user_data = [
        ['Nome:', f"{relatorio.user.first_name} {relatorio.user.last_name}"],
        ['CPF:', relatorio.user.cpf or 'N/A'],
        ['Email:', relatorio.user.email],
        ['Ano:', str(relatorio.ano_calendario)],
    ]
    
    user_table = Table(user_data, colWidths=[5*cm, 12*cm])
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
    elements.append(Spacer(1, 1*cm))
    
    elements.append(Paragraph("Resumo de Rendimentos", styles['Heading2']))
    elements.append(Spacer(1, 0.3*cm))
    
    income_data = [
        ['Tipo', 'Valor (R$)'],
        ['Rendimentos Totais', f"{relatorio.rendimentos_totais:,.2f}"],
        ['Rendimentos Isentos', f"{relatorio.rendimentos_isentos:,.2f}"],
        ['Rendimentos Tributáveis', f"{relatorio.rendimentos_tributaveis:,.2f}"],
    ]
    
    income_table = Table(income_data, colWidths=[10*cm, 7*cm])
    income_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ]))
    
    elements.append(income_table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
