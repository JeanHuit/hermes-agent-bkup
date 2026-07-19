---
name: review-council
description: Runs a structured three-member "Council of Three" peer review (Technical Specialist, Domain Application Expert, Ethical & Impact Reviewer) to validate the scientific merit, technical feasibility, market potential, and ethical alignment of a novel idea, paper, or proposal, ending in a formal Pass/Fail/Revise verdict via two-of-three supermajority voting. Use this skill whenever the user asks to "review," "vet," "evaluate," "assess," or "put through council" a novel idea, research concept, product proposal, or applied-tech pitch — or whenever they ask for a formal Pass/Fail decision, a consensus/voting-based evaluation, or a structured multi-perspective critique of a submission. Also use it to generate the intake submission form or the final decision report for this process, even if the user only asks for "the form" or "the report."
---

# Review Council Skill

A five-stage, stage-gated peer review process that puts a submission (a scientific paper, novel idea, or applied-tech proposal) in front of a three-member expert council and produces a formal, evidence-backed Pass/Fail/Revise verdict.

Use this skill end-to-end when asked to review/vet/evaluate a submission. Use it partially when asked only for one artifact (e.g. "just give me the intake form" or "draft the criteria checklist").

## Quick summary

- **Council:** 3 mandatory roles — Technical Specialist, Domain Application Expert, Ethical & Impact Reviewer. See `references/roles_and_voting.md`.
- **Consensus rule:** ≥2 of 3 "Pass" votes required to pass. This is a strict count of PASS votes, not a majority-of-opinions rule — see the voting reference for worked examples.
- **Workflow:** 5 stages — Intake → Individual Reviews → Deliberation → Final Decision → Outcome/Feedback. See below and `references/roles_and_voting.md`.
- **Criteria:** 3 dimensions — Scientific/Technical Rigor, Implementation Feasibility, Market/System Potential — each with its own pass benchmarks. See `references/review_criteria.md`.
- **Templates:** intake submission form and final decision report are in `assets/`.

## When running a full review

Work through the five stages in order. Do not skip a stage or merge Stage II and Stage III — the deliberation step is what turns three independent opinions into a defensible consensus, and skipping it is the most common way this process gets shortcut incorrectly.

### Stage I — Submission & Intake Review
Act as the **Intake Coordinator**. Before anything else, verify the submission includes, at minimum:
- An Executive Summary / Abstract (max ~500 words: problem, proposed solution, novelty claim)
- A high-level Technical Diagram or architecture sketch
- A Methodology Deep Dive (data sources, experimental controls, tools, resource estimates)
- A Literature Review / State-of-the-Art section (5+ relevant citations)

If any mandatory piece is missing, stop here, tell the user what's missing, and don't proceed to Stage II with an incomplete package (you may still draft the missing sections collaboratively with the user if they want help completing intake). Use `assets/submission_form_template.md` to structure or request this intake material.

### Stage II — Individual Deep-Dive Reviews
Adopt each of the three council roles **in turn**, independently, using the lens and mandate described in `references/roles_and_voting.md`. For each role produce a short, self-contained review containing:
1. A Pass/Fail recommendation
2. Evidence for the vote, citing specific parts of the submission or specific criteria from `references/review_criteria.md`
3. Risk vectors identified (technical debt, market inertia, ethical blind spots, etc. as appropriate to the role)

Do this before comparing the three reviews to each other — each role's verdict should be reached independently, not harmonized in advance.

### Stage III — Deliberation & Synthesis
Adopt the **Moderator** role. Convene the three (already-written) reviews and:
- Identify where they agree and disagree — don't just restate each review
- Surface any critical disagreement and try to resolve it into either an objective consensus point or a clearly-labeled irreconcilable dissent
- Note explicitly whether the two-Pass threshold is met, at risk, or missed

### Stage IV — Final Decision
Reconvene the three roles against the Stage III synthesis and determine the outcome using the voting rule in `references/roles_and_voting.md` (Pass / Revise / Reject). Compile this into `assets/decision_report_template.md`.

### Stage V — Outcome & Feedback
Deliver the final decision report. If the outcome is not a clean Pass, include a specific, actionable feedback section pointing to which criteria in `references/review_criteria.md` were unmet and what a resubmission would need to change.

## Producing individual artifacts

- **"Give me the submission/intake form"** → fill out `assets/submission_form_template.md` for the user's idea.
- **"Give me the decision report"** → fill out `assets/decision_report_template.md` using whatever review content you have.
- **"What are the review criteria?"** → summarize or hand back `references/review_criteria.md`.
- **"Who's on the council / how does voting work?"** → summarize or hand back `references/roles_and_voting.md`.

## Notes on scope

This process is for internal vetting of proposals that need formal "Novel Idea" validation — new product concepts, applied-tech pitches, research proposals, or major strategic shifts. It is intentionally rigorous (stage-gated, evidence-cited, two-of-three consensus) — don't compress it into a single free-form critique unless the user explicitly asks for a lightweight/informal pass instead of the full council process.
