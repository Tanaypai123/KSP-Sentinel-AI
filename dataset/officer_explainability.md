# Officer Explainability Reference

This document outlines the presentation guidelines and target metrics of **Officer Mode** within the Explainability Engine.

## 🎯 Purpose
Provide law enforcement officers operating under operational pressure with a fast, clear, and high-trust summary of why an AI response was generated.

## 📋 Officer Mode Design Rules
1. **Conciseness:** Maximum **5 bullets**.
2. **Simple Language:** No SQL syntax, python object representations, or technical terms.
3. **Structured Metrics:** Clearly state the detected intent, extracted filters, records found, safety guard checks, and final system confidence.

## 📋 Example Presentation

* **Detected Intent:** Search Accused.
* **Extracted search parameters:** accused_name=Raju.
* **No database records matched your search parameters.**
* **Safety Guard:** Some unbacked details were suppressed to prevent hallucination.
* **System Confidence:** 0.0%.
