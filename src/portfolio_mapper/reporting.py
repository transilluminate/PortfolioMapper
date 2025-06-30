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
        self.cell(0, 10, f'Page {self.page_no()}, generated on {timestamp}', 0, 0, 'C')

def generate_pdf_report(analysis_result: LLMAnalysisResult, available_frameworks: Dict[str, FrameworkFile]) -> bytes:
    """
    Generates a PDF report from the analysis results.
    """
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Overall Summary', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 5, analysis_result.overall_summary.encode('latin-1', 'replace').decode('latin-1'))
    pdf.ln(10)

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Suggested Matching Competencies', 0, 1)
    
    grouped_competencies = defaultdict(list)
    for competency in analysis_result.assessed_competencies:
        grouped_competencies[competency.framework_code].append(competency)

    for framework_code, competencies in grouped_competencies.items():
        if framework_obj := available_frameworks.get(framework_code):
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, f"{framework_obj.metadata.abbreviation}: {framework_obj.metadata.title}", 0, 1)
        
        for competency in sorted(competencies, key=lambda c: c.competency_id):
            pdf.set_font('Arial', 'B', 10)
            pdf.multi_cell(0, 5, f"{competency.competency_id}: {competency.competency_text}".encode('latin-1', 'replace').decode('latin-1'))
            pdf.set_font('Arial', '', 10)
            pdf.multi_cell(0, 5, f"\nJustification: {competency.justification_for_level}".encode('latin-1', 'replace').decode('latin-1'))
            if competency.emerging_evidence_for_next_level:
                pdf.multi_cell(0, 5, f"\nNext Level Evidence: {competency.emerging_evidence_for_next_level}".encode('latin-1', 'replace').decode('latin-1'))
            pdf.ln(5)
            
    return pdf.output(dest='S').encode('latin-1')
