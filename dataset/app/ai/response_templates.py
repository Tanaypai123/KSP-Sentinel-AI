"""
Centralized response templates for the AI pipeline.
Ensures consistent, professional communication and clear error messages.
"""

from typing import List

# ---------------------------------------------------------
# Conversational Templates
# ---------------------------------------------------------
CONVERSATIONAL_RESPONSES = {
    "GREETING": "Welcome Officer. I am ready to assist with your investigation today.",
    "GOODBYE": "Session closed. Stay safe.",
    "THANKS": "Acknowledged. Let me know if you need further assistance.",
    "HELP": "I am equipped to search cases, look up FIRs, predict crime trends, and analyze hotspot data. Provide a query such as 'Show theft cases in Mysuru' or 'Predict crime next month'.",
    "BOT_IDENTITY": "I am KSP Sentinel AI, your advanced police investigation assistant.",
    "BOT_CAPABILITIES": "I can analyze crime trends, predict future crime rates, identify hotspots, and search the database for specific cases, victims, and accused.",
    "GENERAL_CHAT": "I am an AI assistant built for police investigations. Please provide a relevant query.",
    "UNKNOWN": (
        "I could not determine the objective of your request.\n\n"
        "Please rephrase or request one of the following:\n"
        "- FIR lookup (e.g., 'Open FIR KSP-000245')\n"
        "- Crime trends (e.g., 'Show theft cases')\n"
        "- Crime statistics\n"
        "- Accused or Victim searches\n"
        "- Predictive analysis"
    )
}

# ---------------------------------------------------------
# Error and Fallback Templates
# ---------------------------------------------------------
def get_no_records_found(crime_name: str) -> str:
    """Format a professional 'no records' message for search queries."""
    c_name = crime_name.replace('_', ' ').title() if crime_name else "cases"
    other_districts = f"- Show {c_name} cases in other districts" if c_name != "cases" else "- Show cases in other districts"
    return (
        "I searched the available Karnataka Police database but could not find any matching records.\n\n"
        "**Possible reasons:**\n"
        "• Different spelling\n"
        "• Different district\n"
        "• No registered FIR\n"
        "• Filters too restrictive\n\n"
        "You may try these related searches:\n"
        "- Show all cases\n"
        f"{other_districts}"
    )

def get_fir_not_found(suggestions: List[str]) -> str:
    """Format a professional 'FIR not found' message with suggestions."""
    suggestion_lines = "\n".join(f"- {s}" for s in suggestions)
    return (
        "I searched the available Karnataka Police database but could not find any matching records for the requested FIR.\n\n"
        "**Possible reasons:**\n"
        "• The FIR number might not exist in the database.\n"
        "• The case might be registered under a different jurisdiction.\n\n"
        "**You may try these valid FIR numbers:**\n"
        f"{suggestion_lines}"
    )

def get_invalid_district(raw_district: str, suggestions: List[str]) -> str:
    """Format a professional invalid district message."""
    return "I couldn't identify this as a Karnataka district.\n\nPlease enter a valid Karnataka district."
