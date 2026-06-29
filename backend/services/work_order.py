import os
from fpdf import FPDF
from datetime import datetime

class WorkOrderPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'JAN SAHAYAK - OFFICIAL WORK ORDER', border=False, ln=1, align='C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, 'Municipal Repair & Maintenance Dispatch', border=False, ln=1, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_work_order_pdf(report, output_dir):
    """
    Generates a PDF work order for a given issue report.
    Returns the filename of the generated PDF.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Create filename
    timestamp = datetime.now().strftime("%Y%md_%H%M%S")
    filename = f"WO_Report_{report.id}_{timestamp}.pdf"
    filepath = os.path.join(output_dir, filename)

    pdf = WorkOrderPDF()
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '1. INCIDENT DETAILS', ln=1, border='B')
    pdf.ln(2)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, 'Report ID:', 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 8, f"#{report.id}", 0, 1)

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, 'Category:', 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 8, str(report.category), 0, 1)

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, 'Severity Level:', 0, 0)
    pdf.set_font('Arial', 'B', 10)
    
    # High severity gets red text (if possible in FPDF, else just bold)
    if report.ai_severity >= 4:
        pdf.set_text_color(200, 0, 0)
    pdf.cell(0, 8, f"{report.ai_severity} / 5 (URGENT)", 0, 1)
    pdf.set_text_color(0, 0, 0)

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, 'GPS Location:', 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 8, f"{report.latitude}, {report.longitude}", 0, 1)

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, 'Reported At:', 0, 0)
    pdf.set_font('Arial', '', 10)
    reported_date = report.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if report.created_at else "Unknown"
    pdf.cell(0, 8, reported_date, 0, 1)
    
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '2. AI DIAGNOSTIC SUMMARY', ln=1, border='B')
    pdf.ln(2)
    
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 8, str(report.ai_summary))
    
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '3. CITIZEN DESCRIPTION', ln=1, border='B')
    pdf.ln(2)
    
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 8, str(report.description))
    
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '4. FIELD REPAIR SIGN-OFF', ln=1, border='B')
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(50, 10, 'Assigned Team:', 0, 0)
    pdf.cell(0, 10, '___________________________________________________', 0, 1)
    
    pdf.cell(50, 10, 'Date Resolved:', 0, 0)
    pdf.cell(0, 10, '___________________________________________________', 0, 1)
    
    pdf.cell(50, 10, 'Supervisor Signature:', 0, 0)
    pdf.cell(0, 10, '___________________________________________________', 0, 1)
    
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 9)
    pdf.cell(0, 10, 'Note: Return this completed physical copy to the Municipal Command Center for archiving.', align='C')

    pdf.output(filepath)
    return filename
