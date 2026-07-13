with open('/Users/tanaysharma/Desktop/KSP-Sentinel-AI/dataset/app/ai/enterprise_orchestrator.py', 'r') as f:
    content = f.read()

# Fix the broken dictionary key
content = content.replace(
    '"ContextNormalizerStage, InvestigationReasoningEngineStage": ContextNormalizerStage, InvestigationReasoningEngineStage,',
    '"ContextNormalizerStage": ContextNormalizerStage,'
)

with open('/Users/tanaysharma/Desktop/KSP-Sentinel-AI/dataset/app/ai/enterprise_orchestrator.py', 'w') as f:
    f.write(content)
