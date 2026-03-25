---
phase: 1
slug: core-infrastructure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pytest.ini or pyproject.toml |
| **Quick run command** | `pytest tests/ -v --tb=short` |
| **Full suite command** | `pytest tests/ -v --tb=long -k "phase1"` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -v --tb=short`
- **After every plan wave:** Run `pytest tests/ -v --tb=long -k "phase1"`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | FRIS-01, FRIS-02, FRIS-03 | unit | `pytest tests/ -v -k "topic"` | ✅ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | FRIS-20, FRIS-21, FRIS-22 | unit | `pytest tests/ -v -k "data_source"` | ✅ W0 | ⬜ pending |
| 1-01-03 | 01 | 1 | FRIS-13 | unit | `pytest tests/ -v -k "cache"` | ✅ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_topic_classifier.py` — stubs for FRIS-01, FRIS-02, FRIS-03 (topic matching)
- [ ] `tests/test_data_source.py` — stubs for FRIS-20, FRIS-21, FRIS-22 (yfinance/FMP integration)
- [ ] `tests/test_cache.py` — stubs for FRIS-22 (TTL caching)
- [ ] `conftest.py` — shared fixtures for mock data

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Topic→GICS mapping accuracy | FRIS-02 | Needs human judgment on keyword relevance | Run with 5 test topics, verify returned industries make sense |
| End-to-end topic search | FRIS-01, FRIS-03 | Full pipeline integration test | Manual test: "AI chips" → verify semantically related stocks returned |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
