from fpdf import FPDF
import io

def generate_expert_report(res, user_name, company):
    pdf = FPDF()
    pdf.add_page()
    
    # Title & Header
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 15, "SynoCore Expert Intelligence Report", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, f"Client: {user_name} ({company}) | Confidential", ln=True, align='C')
    pdf.ln(5)
    
    # Section I. Design Metrics
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "I. Design Performance Metrics", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, f"- Areal Capacity: {res['areal_capacity']} mAh/cm2", ln=True)
    pdf.cell(0, 8, f"- Total Capacity: {res['total_capacity']} mAh", ln=True)
    pdf.cell(0, 8, f"- Specific Energy: {res['specific_energy']} Wh/kg", ln=True)
    pdf.ln(5)
    
    # Section II. Strategic AI Insight
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "II. Strategic AI Insight", ln=True)
    pdf.set_font("Arial", size=11)
    insight_text = (
        f"Based on the loading of {res.get('loading', 'N/A')} mg/cm2, "
        f"the N/P ratio of {res.get('np_ratio', 'N/P')} is optimal for cycling stability. "
        "Recommend monitoring electrolyte depletion during the first 100 cycles."
    )
    pdf.multi_cell(0, 7, insight_text)
    
    # Footer
    pdf.set_y(-25)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, "Copyright 2026 SynoTech Co., Ltd. All Rights Reserved.", align='C')
    
    return bytes(pdf.output(dest='S'))