import re

with open('/Users/tanaysharma/Desktop/KSP-Sentinel-AI/dataset/app/ai/investigation_brief_builder.py', 'r') as f:
    content = f.read()

# Fix models first
new_progress = """@dataclass
class InvestigationTask:
    task: str
    status: str

@dataclass
class InvestigationProgress:
    tasks: List[InvestigationTask] = field(default_factory=list)
    completion_pct: int = 0"""

content = re.sub(r"@dataclass\nclass InvestigationProgress:.*?    next_stage: str = \"Evidence Collection\"", new_progress, content, flags=re.DOTALL)

# Update Recommendation
new_rec = """@dataclass
class RecommendedAction:
    text: str
    evidence: str
    reason: str
    risk: str
    recommendation: str
    expected_impact: str
    priority: str
    confidence: float
    dependencies: List[str]"""

content = re.sub(r"@dataclass\nclass RecommendedAction:.*?    supporting_evidence: List\[str\] = field\(default_factory=list\)", new_rec, content, flags=re.DOTALL)

# Add imports for Validator and Calculator
import_block = """from app.ai.decision_support_engine import DecisionSupportStage
from app.ai.investigation_reasoning_engine import Contradiction, InvestigationLimitation, OfficerInsight, InvestigationConclusion
from app.ai.report_consistency_validator import ReportConsistencyValidator
from app.ai.confidence_calculator import ConfidenceCalculator"""

content = re.sub(r"from app.ai.decision_support_engine import DecisionSupportStage\nfrom app.ai.investigation_reasoning_engine import Contradiction, InvestigationLimitation, OfficerInsight, InvestigationConclusion", import_block, content, flags=re.DOTALL)

with open('/Users/tanaysharma/Desktop/KSP-Sentinel-AI/dataset/app/ai/investigation_brief_builder.py', 'w') as f:
    f.write(content)
