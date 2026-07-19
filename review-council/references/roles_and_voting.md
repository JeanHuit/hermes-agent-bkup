# Council Roles, Workflow, and Voting Mechanics

## The Council of Three

Every review is conducted by exactly three council members, each with a distinct, non-overlapping mandate. Don't collapse or blend these lenses — the value of the process comes from each role staying in its lane during Stage II.

### 1. Technical Specialist (Technical Reviewer)
- **Focus:** "How" — can it be built?
- **Specialty areas:** Scientific rigor, methodological soundness, technical novelty, architecture/infrastructure, scalability, code quality, interoperability, dependency-stack stability.
- **Verdict concern:** Technical debt.
- Assesses against the Scientific/Technical Rigor and Implementation Feasibility criteria (see `review_criteria.md`).

### 2. Domain Application Expert (Domain Application Reviewer / DAR)
- **Focus:** "Why now" — who needs this?
- **Specialty areas:** Industry/market alignment, real-world viability, integration with existing processes and standards, jobs-to-be-done fit.
- **Verdict concern:** UX / relevance gap.
- Assesses against the Market and System Potential criteria.

### 3. Ethical & Impact Reviewer (EIR)
- **Focus:** "Should we" — is it safe and responsible?
- **Specialty areas:** Bias detection, data privacy compliance (e.g. GDPR/CCPA-style considerations), fairness, societal and regulatory impact, representation across affected user groups.
- **Verdict concern:** Harm / bias.
- Assesses ethical alignment and flags any regulatory or societal risk regardless of how well the idea scores technically or commercially.

## The Five-Stage Workflow

1. **Submission & Intake Review** — Intake Coordinator gatekeeps for completeness against the required input materials.
2. **Individual Deep-Dive Reviews** — Each of the three roles reviews independently and produces a Pass/Fail recommendation with evidence and risk vectors.
3. **Deliberation Meeting & Synthesis** — A Moderator convenes the three reviews, surfaces disagreement, and forges a unified narrative around consensus or dissent.
4. **Final Decision Body Review** — The three roles reconvene against the synthesis and determine the final outcome: Pass / Revise / Reject.
5. **Outcome & Feedback Generation** — Formal notification, plus a mandatory feedback loop for anything that isn't a clean Pass, guiding resubmission.

Roles referenced elsewhere (e.g. "Review Moderator," "Decision Body/Committee," "Submitter") map onto this same five-stage flow; the Moderator runs Stages III–IV, and the "Decision Body" is simply the three council members meeting for Stage IV.

## Voting Mechanic — Two-of-Three PASS Consensus

**The only rule that matters mechanically:** count how many of the three roles voted **PASS**.

- `PASS count ≥ 2` → **APPROVED** (the submission proceeds to development/publication), regardless of which specific role cast the dissenting vote.
- `PASS count < 2` (i.e. 0 or 1 Pass) → **BLOCKED — Requires Follow-up Review** (Revise or Reject, per Stage IV discussion).

This is a strict supermajority-of-PASS-votes rule, **not** a "no single reviewer can block it" or "majority of positive sentiment" rule. A single Fail is not by itself disqualifying, but two Fails always block the submission — there is no scenario where one PASS is sufficient.

### Worked examples
| Technical | Domain | Ethical | PASS count | Outcome |
|---|---|---|---|---|
| Pass | Pass | Fail | 2 | **APPROVED** |
| Pass | Fail | Pass | 2 | **APPROVED** |
| Fail | Pass | Pass | 2 | **APPROVED** |
| Pass | Pass | Pass | 3 | **APPROVED** |
| Pass | Fail | Fail | 1 | **BLOCKED** |
| Fail | Fail | Fail | 0 | **BLOCKED** |

Note: even when the outcome is APPROVED with a dissenting vote, the dissent and its rationale (especially if it came from the Ethical & Impact Reviewer) should still be recorded in the final decision report as a flagged risk — approval doesn't mean the concern disappears, only that it didn't block progression.

### A note on the intermediate "conditional PASS"
Some source material allows a reviewer to vote YES / NO / PASS, where "PASS" here means "acceptable with conditions." For the purposes of the gatekeeping threshold above, only this middle "PASS (acceptable with conditions)" vote — treated the same as a formal Pass recommendation — counts toward the two-vote threshold. A straightforward Fail/No does not count, no matter how minor the stated conditions were.
