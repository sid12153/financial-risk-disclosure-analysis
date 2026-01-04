# Tests

This directory contains automated tests that enforce the **reliability and safety guarantees** of the Financial Disclosure Intelligence system.

The goal of these tests is not model accuracy, but **behavioral correctness**:  
the system must refuse when it should, and must never return unsupported answers.

---

## What These Tests Enforce

### 1. Guardrails and Refusals
The system must **refuse** to answer questions that are:
- out of scope for SEC filings
- speculative (e.g., stock price predictions)
- unsupported by retrieved evidence

This ensures the system never hallucinates.

**File:**  
- `test_guardrails.py`

---

### 2. Citation Discipline
If the system produces an answer, it **must include citations** pointing to retrieved filing chunks.

Answers without citations are treated as failures.

**File:**  
- `test_citations_required.py`

---

### 3. Test Configuration
Shared fixtures and test configuration live in:
- `conftest.py`

This keeps test setup consistent and avoids duplication.

---

## Why This Matters

These tests make the system suitable for **compliance, audit, and analyst workflows**:

- refusal is a feature, not a bug  
- evidence is mandatory  
- unsupported answers are never allowed  

This mirrors how real enterprise AI systems are evaluated.

---

## How to Run Tests (Local)

From the project root:

```bash
pytest -q
```

All tests must pass before changes are considered safe.

Notes:
- Tests are intentionally lightweight and deterministic.
- No external APIs are called during testing.
- The focus is policy enforcement, not model performance.






