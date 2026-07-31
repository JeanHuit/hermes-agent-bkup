---
name: teaching-session
description: "Use when preparing teaching sessions, lesson plans, quizzes, or student handouts for any subject."
version: 1.0.0
author: JeanHuit
license: MIT
metadata:
  hermes:
    tags: [teaching, lesson-plan, quiz, education]
    related_skills: [ocr-and-documents, pdf]
---

# Teaching Session Planner

Prepare structured teaching sessions, lesson plans, quizzes, and student handouts for any subject area. Subject-agnostic — works for Python, Linux, electronics, robotics, or anything else.

## When to Use

- Preparing a new teaching session (2-hour format)
- Generating a lesson plan from source material (PDFs, books, user notes)
- Creating quizzes from weekly topics (QuizForge-compatible .md format)
- Writing student take-home reference sheets or cheat sheets
- Reviewing and updating existing lesson plans

Don't use for: grading, student progress tracking, or course-level syllabus design.

## Inputs

Source material can be anything the user provides:

- PDFs or scanned notes → extract with `pdftotext <file.pdf> -`
- Books or articles → user pastes key sections
- Verbal description of what to teach → user explains the topic
- Existing lesson notes → user shares files

Always ask: "What topic are we covering, and do you have any source material?"

## Output Location

Per-subject folders under:
```
/home/jeanhuit/Documents/HermesVault/Teaching/<subject>/
```

Create the folder if it doesn't exist. Examples:
- `Teaching/python/`
- `Teaching/linux/`
- `Teaching/electronics/`

Each session produces up to 3 files:
1. `weekNN-session.md` — Facilitator lesson plan with timing
2. `weekNN-cheatsheet.md` — Student take-home reference
3. `weekNN-quiz.md` — Quiz file (QuizForge-compatible)

Use the week number if known, otherwise use a descriptive name.

## Session Plan Structure (2-hour template)

### Hour 1 — Build the Foundation (60 min)

1. **Warm-up quiz (10 min):** 5 quick questions from previous week. Surfaces gaps before building on new material.
2. **Topic A deep dive (15 min):** Live-code or demonstrate 2 examples. First practical, second engaging/fun.
3. **Topic B deep dive (15 min):** Teach 3 recurring patterns or techniques students will use often.
4. **Integration (20 min):** Show how A and B connect. Introduce a function, wrapper, or abstraction that ties them together.

### Hour 2 — Apply and Practice (60 min)

5. **Mini-project (30 min):** Live-build something that uses everything from Hour 1. Step by step, students follow along.
6. **Student exercises (25 min):** Pair work. 3 exercises: easy warm-up, medium challenge, hard stretch goal.
7. **Wrap-up (5 min):** Recap 3 big ideas. Preview next week.

### Timing Adjustments

- If running long: shorten Block 2 (cut the second example)
- If running short: extend exercises with a bonus challenge
- The mini-project (Block 5) is the payoff — never rush it

## Quiz Generation

Quizzes must be in the QuizForge-compatible Markdown format. Generate them as part of session preparation when the user asks for a quiz.

### QuizForge Markdown Format

```markdown
# Question

Question text goes here?

- [ ] Wrong answer A
- [x] Correct answer B
- [ ] Wrong answer C
- [ ] Wrong answer D
```

Rules:
- Every question starts with exactly `# Question` on its own line
- A blank line separates the question text from options
- Options use `- [ ]` for incorrect, `- [x]` for correct
- Exactly 4 options per question (standard for QuizForge)
- Code or commands wrap in backticks: `grep -i error`
- One correct answer per question (mark exactly one `- [x]`)

### Quiz Composition

A good weekly quiz has 20-30 questions mixing:

1. **Recall from this week's topic (60-70%):** Direct knowledge checks. "Which command does X?" "What does this code output?"
2. **Application questions (20-25%):** Scenario-based. "A user wants to Y. Which command should they use?" "What is the output of this code snippet?"
3. **Review from previous weeks (10-15%):** 3-5 questions from earlier material to reinforce retention.

Vary question types:
- Direct command/syntax recall
- "What is the output of..." (code snippets)
- "Which command performs..." (multiple choice commands)
- Scenario-based ("A sysadmin needs to...")
- Conceptual ("What is the purpose of...")

## Writing Exercises

Good exercises follow this tiered pattern:

- **Easy (5-10 lines):** Single concept. "Print all even numbers 1-50"
- **Medium (10-20 lines):** Combines 2 concepts. "Password validator using conditionals + loops"
- **Hard (20-30 lines):** Combines 3+ concepts. "Number guessing game with attempts limit"

Always include:
- A clear spec (what it should do)
- Expected output for test cases
- A hint (not the full solution)

## Facilitator Notes to Include

Every session plan should end with a section containing:
- Timing tips (what to cut if running long)
- Common mistakes students make in this topic
- Live coding tips (type in files not interpreter, make deliberate mistakes, let students predict output)
- Materials needed (if any)

## Workflow

1. Ask the user: what subject, what topic, any source material, what week number
2. If PDFs provided, extract text with `pdftotext`
3. Draft the session plan → save to `Teaching/<subject>/`
4. Draft the cheat sheet → save alongside
5. If quiz requested, generate 20-30 questions in QuizForge format → save alongside
6. Confirm with user before finalizing
