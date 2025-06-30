# src/portfolio_mapper/reporting.py

# Copyright (c) Adrian Robinson 2025
# This software is dual-licensed under the MIT License (for NHS use only)
# and a Commercial License (for other commercial use).
# For commercial licensing inquiries, please contact adrian.j.robinson@gmail.com

"""
This module is responsible for generating downloadable reports,
such as PDFs and CSVs, from the analysis results.
"""
from collections import defaultdict
from datetime import datetime
from typing import Dict
from fpdf import FPDF

from .models.llm_response import LLMAnalysisResult
from .models.framework import FrameworkFile

class PDF(FPDF):
    """Custom PDF class to handle headers and footers."""
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Portfolio Mapper Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        timestamp = datetime.now().strftime("%d-%m-%Y at %H:%M")
        self.cell(0, 10, f'Page {self.page_no()} - generated on {timestamp}', 0, 0, 'C')

def generate_pdf_report(
    analysis_result: LLMAnalysisResult,
    available_frameworks: Dict[str, FrameworkFile],
    reflection_text: str
) -> bytes:
    """
    Generates a PDF report from the analysis results.
    """
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- 1. User's Reflection ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "Your Reflection", 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.set_fill_color(245, 245, 245)  # Light grey background
    pdf.multi_cell(0, 5, reflection_text.encode('latin-1', 'replace').decode('latin-1'), border=1, fill=True)
    pdf.ln(10)

    # --- 2. Overall Summary ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Overall Summary', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 5, analysis_result.overall_summary.encode('latin-1', 'replace').decode('latin-1'))
    pdf.ln(10)

    # --- 3. Competencies Table ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Suggested Matching Competencies', 0, 1)

    if not analysis_result.assessed_competencies:
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, 'No specific competencies were matched.', 0, 1)
    else:
        # Group competencies by framework
        grouped_competencies = defaultdict(list)
        for competency in analysis_result.assessed_competencies:
            grouped_competencies[competency.framework_code].append(competency)

        def clean_text(text: str) -> str:
            """Encodes text to latin-1, replacing unsupported characters."""
            return text.encode('latin-1', 'replace').decode('latin-1')

        for framework_code, competencies in grouped_competencies.items():
            # --- Framework Title ---
            if framework_obj := available_frameworks.get(framework_code):
                pdf.ln(5) # Add space before a new framework section
                pdf.set_font('Arial', 'B', 11)
                # Use multi_cell to allow for title wrapping
                framework_title = clean_text(f"{framework_obj.metadata.abbreviation}: {framework_obj.metadata.title}")
                pdf.multi_cell(0, 6, framework_title, 0, 'L')
                pdf.ln(2)

            # --- List of Competencies ---
            for competency in sorted(competencies, key=lambda c: c.competency_id):
                # Heuristic check for page break before adding a new item.
                # A full item is roughly 40-50mm.
                if pdf.get_y() > (pdf.page_break_trigger - 50):
                    pdf.add_page()
                    # Re-print framework title on new page
                    if framework_obj:
                        pdf.set_font('Arial', 'B', 11)
                        pdf.multi_cell(0, 6, f"{framework_title} (continued)", 0, 'L')
                        pdf.ln(2)

                # Competency ID and Text
                pdf.set_font('Arial', 'B', 10)
                pdf.multi_cell(0, 5, clean_text(f"{competency.competency_id}: {competency.competency_text}"))

                # Achieved Level
                pdf.set_font('Arial', 'BI', 9) # Bold Italic
                pdf.cell(30, 6, "Achieved Level: ")
                pdf.set_font('Arial', '', 9)
                pdf.multi_cell(0, 6, clean_text(competency.achieved_level))

                # Justification
                pdf.set_font('Arial', 'B', 9)
                pdf.multi_cell(0, 5, "Justification:")
                pdf.set_font('Arial', '', 9)
                pdf.multi_cell(0, 5, clean_text(competency.justification_for_level))

                # Next Level Evidence
                if competency.emerging_evidence_for_next_level:
                    pdf.set_font('Arial', 'B', 9)
                    pdf.multi_cell(0, 5, "Next Level Evidence:")
                    pdf.set_font('Arial', '', 9)
                    pdf.multi_cell(0, 5, clean_text(competency.emerging_evidence_for_next_level))
                
                pdf.ln(8) # Space between competency items
            
    return pdf.output(dest='S').encode('latin-1')
