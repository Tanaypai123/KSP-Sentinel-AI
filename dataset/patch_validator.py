with open('/Users/tanaysharma/Desktop/KSP-Sentinel-AI/dataset/app/ai/decision_support_engine.py', 'r') as f:
    content = f.read()

import re

# Fix ActionValidator._check
new_check = """    @classmethod
    def _check(cls, s: InvestigationStrategy) -> Optional[str]:
        if not s.title:
            return "Missing title"
        if not getattr(s, "evidence", getattr(s, "supporting_evidence", None)):
            return "No supporting evidence provided"
        if not s.reasoning and not getattr(s, "reason", None):
            return "No reason provided"
        if s.confidence < 0.1:
            return "Confidence too low"
        return None"""

content = re.sub(r"    @classmethod\n    def _check\(cls, s: InvestigationStrategy\) -> Optional\[str\]:.*?        return None", new_check, content, flags=re.DOTALL)

with open('/Users/tanaysharma/Desktop/KSP-Sentinel-AI/dataset/app/ai/decision_support_engine.py', 'w') as f:
    f.write(content)
