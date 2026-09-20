# Course and exam context

When a course is new, or exam preparation or planning needs missing information, consult the relevant syllabus, assessment instructions or past papers already in the vault. Read only what the task needs. Keep useful findings in the existing scope through the usual `save`; do not interrupt an exercise for a course intake or survey unrelated courses.

`course_context` is optional and replaces its previous object when saved (`null` clears it). Omit unknown fields; use `unknowns` only for unresolved details that affect the task. Save actual requirements from primary material or the user's explicit information. Label patterns inferred from past papers as indications, not requirements. A conflicting or outdated source remains uncertain until resolved; ask only if the answer matters now.

```json
{
  "sources": {
    "syllabus": {"path": "university/course/syllabus.pdf"},
    "sample": {"path": "university/course/sample-exam.pdf"}
  },
  "course_context": {
    "assessment": "Written problems followed by an oral discussion",
    "criteria": ["Explain method choice and justify assumptions"],
    "constraints": ["No calculator in the written exam"],
    "unknowns": ["Whether the sample paper reflects this year's exam"],
    "refs": [{"source": "syllabus", "locator": "Assessment section"}],
    "checked_on": "2026-09-18"
  },
  "coverage": {
    "text": "Examinable: chapters 1–4; chapter 5 excluded",
    "refs": [{"source": "syllabus", "locator": "Programme"}]
  }
}
```

Keep the deadline in top-level `exam`, and examinable material in top-level `coverage`; do not copy them into `course_context`. Reference representative exercises through ordinary source/topic records when useful. `checked_on` means when you actually checked the supporting material, not an automatic freshness guarantee. Recheck when new information, a changed assessment or a consequential uncertainty warrants it, not every session.

Use this context to choose useful explanation depth, practice and review. It does not establish the learner's understanding. Sources identify cited content: record a known edition/version when available and use a new handle for changed content; a path move preserves the existing handle. Reuse loaded context; course administration should stay out of the teaching response unless it helps the user decide what to study.
