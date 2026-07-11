# Developer Memory Integration Reference

This document provides developer guidelines, API instructions, and debug utilities for the Investigation Memory Engine.

## ⚙️ Memory API
Developers can query the singleton memory registry directly using:

```python
from app.ai.memory_engine import MemoryEngine

# 1. Retrieve current memory state safely (validating TTL)
memory = MemoryEngine.get_memory(conversation_id="default")

# 2. View forensic change audit records
audits = MemoryEngine.get_audit_trail(conversation_id="default")

# 3. Deterministically clear session
MemoryEngine.reset_memory(conversation_id="default")
```

## 🛠️ Overriding TTL in Tests
To test expiry conditions without sleeping:

```python
import time
from app.ai.memory_engine import MemoryEngine

# Set TTL to 1 second
MemoryEngine.TTL_SECONDS = 1.0

# Store state, sleep 1.1s, and confirm it returns None
time.sleep(1.1)
assert MemoryEngine.get_memory("default") is None
```
