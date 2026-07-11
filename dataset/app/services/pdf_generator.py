import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from typing import Dict, Any

def generate_pdf_report(report_id: str, output_path: str, payload: Dict[str, Any] = None):
    """
    Generate a dynamic PDF report including the chat history and findings.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    story.append(Paragraph(f"KSP Sentinel AI Investigation Report", styles['Title']))
    story.append(Spacer(1, 12))
    
    # Subtitle
    story.append(Paragraph(f"Report ID: {report_id}", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    if payload and "messages" in payload:
        messages = payload["messages"]
        for msg in messages:
            sender = msg.get("sender", "Unknown").capitalize()
            text = msg.get("text", "")
            
            # Use different styles for User vs Assistant
            style_name = 'Heading4' if sender == 'User' else 'Normal'
            prefix = "Officer Query:" if sender == 'User' else "AI Assistant:"
            
            story.append(Paragraph(f"<b>{prefix}</b>", styles[style_name]))
            story.append(Spacer(1, 4))
            
            # Clean up the text for PDF rendering
            clean_text = text.replace('\n', '<br />')
            story.append(Paragraph(clean_text, styles['Normal']))
            story.append(Spacer(1, 12))
            
    else:
        # Fallback if no payload
        body_text = (
            f"This is an automatically generated intelligence report for {report_id}. "
            "No chat history was provided."
        )
        story.append(Paragraph(body_text, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    return output_path

