# CoFoundr AI — Phase 6 Performance Baseline

**Status:** To be filled on Day 30 (Oct 9, 2026)  
**Version:** TBD (v6.0.0)  
**Measured by:** SP-09 benchmark script (`scripts/benchmark.py`)

---

## Environment

| Property | Value |
|---|---|
| Date | TBD |
| Git tag | TBD |
| OS | TBD |
| CPU | TBD |
| RAM | TBD |
| PostgreSQL | local |
| Redis | local |
| ChromaDB | local |
| Concurrency limit | 5 tasks |
| Runs per workload | 5 |

---

## Workflow Duration

| Workload | Tasks | p50 (ms) | p95 (ms) | p99 (ms) | Min (ms) | Max (ms) |
|---|---:|---:|---:|---:|---:|---:|
| Small | ~3 | TBD | TBD | TBD | TBD | TBD |
| Medium | ~6 | TBD | TBD | TBD | TBD | TBD |

---

## Provider Latency

| Provider | p50 (ms) | p95 (ms) |
|---|---:|---:|
| Gemini | TBD | TBD |
| Groq | TBD | TBD |
| OpenRouter | TBD | TBD |

---

## Retrieval Latency

| Stage | p50 (ms) | p95 (ms) |
|---|---:|---:|
| Vector search | TBD | TBD |
| BM25 | TBD | TBD |
| Reranker | TBD | TBD |
| Total RAG | TBD | TBD |

---

## Release Gate Check
[ ] Workflows complete without hangs
[ ] p99 within 3x of p50 (no catastrophic outliers)
[ ] No retry storms observed under single-workflow load
[ ] No memory growth across 5 consecutive runs


---

## Notes

_Fill in after Day 30 benchmark run. Note any outliers, provider timeouts, or unexpected behaviour._