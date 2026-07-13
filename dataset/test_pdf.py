from app.services.pdf_generator import generate_pdf_report
payload = {
    "messages": [
        {"sender": "User", "text": "Generate report"},
        {"sender": "AI", "text": "## Executive Summary\n**Finding:** Subject used a ■■■■ knife.\n────────────────────────────────────────────\nEnd of report."}
    ]
}
generate_pdf_report("test_report", "./test_report.pdf", payload)
print("PDF generated successfully.")
