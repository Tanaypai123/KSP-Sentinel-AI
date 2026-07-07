"""
Text Normalization Layer for the NLP Pipeline.

Handles basic string standardization, spacing, casing, and punctuation removal
to ensure the downstream TF-IDF engine receives clean input.
"""

import re

def normalize_text(text: str) -> str:
    """
    Standardize raw user input.
    Note: Kannada translation is currently handled by the frontend before hitting the API.
    """
    if not text:
        return ""
        
    # Lowercase
    cleaned = text.lower()
    
    # Standardize spacing
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Remove special punctuation that interferes with generic word boundaries,
    # except for hyphens and slashes which might be part of FIR numbers.
    # We will keep alphanumeric, spaces, hyphens, and slashes.
    cleaned = re.sub(r'[^\w\s\-\/]', '', cleaned)
    
    return cleaned
