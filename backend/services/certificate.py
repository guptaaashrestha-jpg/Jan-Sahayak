import os
from fpdf import FPDF
from datetime import datetime

def generate_civic_certificate(username, points, output_dir, template_path):
    """
    Generates a PDF certificate overlaying text on the provided template image.
    Returns the filename of the generated PDF.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Create filename
    filename = f"Certificate_{username.replace(' ', '_')}.pdf"
    filepath = os.path.join(output_dir, filename)

    # A4 dimensions in mm: 210 x 297
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # Add background image
    if os.path.exists(template_path):
        pdf.image(template_path, x=0, y=0, w=210, h=297)
    
    # Assuming template is A4 Portrait based on the user's design
    
    # 1. Citizen Name (Centered below 'PROUDLY PRESENTED TO')
    pdf.set_xy(0, 144) # Stays the same as user didn't complain about Name this time
    pdf.set_font('Arial', 'B', 26)
    pdf.set_text_color(10, 20, 50) # Dark navy blue matching the theme
    pdf.cell(210, 15, username.upper(), align='C')
    
    # 2. Points Earned (Centered exactly on the underscore)
    pdf.set_xy(118, 207) # Box from 118 to 128, centering exactly on 123
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(10, 10, str(points), align='C')
    
    # 3. Date of Issuance (Left aligned starting exactly at the line)
    pdf.set_xy(102, 225) # Starting at 102 (just after ISSUANCE:) and sitting on line at 225
    pdf.set_font('Arial', 'B', 12)
    current_date = datetime.now().strftime("%B %d, %Y")
    pdf.cell(50, 10, current_date, align='L')
    
    # 4. Signatures (Optional, could just use a cursive font)
    # Since it's digital, we can place a cursive text or leave it blank for manual signing.
    
    pdf.output(filepath)
    return filename
