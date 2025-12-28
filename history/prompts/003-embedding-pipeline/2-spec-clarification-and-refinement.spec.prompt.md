---
id: 2
title: Spec Clarification and Refinement
stage: spec
date: 2025-12-15
surface: agent
model: claude-opus-4-5-20251101
feature: embedding-pipeline
branch: 003-embedding-pipeline
user: developer
command: /sp.specify (review and clarify)
labels: ["spec-review", "clarification", "cohere", "qdrant", "embedding"]
links:
  spec: specs/003-embedding-pipeline/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/003-embedding-pipeline/spec.md
  - specs/003-embedding-pipeline/checklists/requirements.md
tests:
  - N/A (specification phase)
---

## Prompt

```text
review Spec-1 spec

[After review identified gaps]

ask questions

[After receiving 5 clarification questions]

clarify Q1 and recommend the best free approach

[After Q1 research]

before proceeding for this clarify and recommend best free approach for other remaining questions

[After Q2-Q5 research]

yes but for Qdrant use cloud free tier and update the @specs\003-embedding-pipeline\spec.md add Create Collection section after the embedding one
Collection named with (Rag-embedding)
```

## Response snapshot

**Spec Review Findings:**
- Initial spec was ~80% ready but had critical gaps
- Missing: specific Cohere model, chunk sizes, change detection mechanism, Qdrant collection schema

**5 Clarification Questions Asked:**
1. Cohere model selection (v3.0 vs v2.0)
2. URL discovery strategy (sitemap vs hardcoded vs crawling)
3. Code block handling (include, separate, or exclude)
4. Qdrant deployment (Cloud vs Docker vs local)
5. Change detection granularity (document vs chunk level)

**Research-Backed Recommendations:**
| Question | Recommendation | Rationale |
|----------|----------------|-----------|
| Q1: Cohere Model | `embed-english-v3.0` (1024 dims) | Top quality, free tier covers 500+ re-runs |
| Q2: URL Discovery | sitemap.xml + hardcoded fallback | Zero maintenance, auto-discovery |
| Q3: Code Blocks | Include with surrounding prose | Prose provides semantic context |
| Q4: Qdrant | Qdrant Cloud free tier | User preference, 1GB RAM/4GB disk |
| Q5: Change Detection | Document-level SHA-256 | Simple, scale-appropriate |

**Spec Updates Applied:**
- Added Qdrant Collection Configuration section (FR-025 to FR-030)
- Collection name: `Rag-embedding`
- Updated all FRs with specific values (41 total FRs)
- Added explicit constraints (20 total across IC, PC, OC, OpC)
- Added Qdrant Cloud inactivity edge case
- Expanded "Not Building" section to 15 items

## Outcome

- ✅ Impact: Specification fully refined with all gaps addressed, ready for `/sp.plan`
- 🧪 Tests: N/A (specification phase)
- 📁 Files: Updated spec.md (41 FRs, 10 SC, 20 constraints) and requirements.md checklist
- 🔁 Next prompts: `/sp.plan` to create technical architecture
- 🧠 Reflection: Research agents provided authoritative information from official docs (Cohere, Qdrant). User clarification on Qdrant Cloud vs local was essential - research had recommended local mode but user preferred cloud free tier.

## Evaluation notes (flywheel)

- Failure modes observed: Initial spec lacked numeric bounds; review caught this before planning
- Graders run and results (PASS/FAIL): Checklist validation PASS (16/16 items)
- Prompt variant (if applicable): Used global-tech-research-advisor agent for Q1-Q5 research in parallel
- Next experiment (smallest change to try): Could have asked all 5 clarification questions upfront instead of sequentially
