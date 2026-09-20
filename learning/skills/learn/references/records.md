# Learning records

One scope is one course or coherent learning interest. Schema 4 keeps observations separate from current assessments, reviews and unfinished tasks. The helper owns versions, handles, revisions, timestamps and freshness fields. Use `learning_save` with `scope`, `expected_revision` and a `changes` patch, or pipe the same patch to `scripts/learn save SCOPE --expect REV`. Revision 0 creates a scope; read existing state before patching.

```json
{
  "title": "Course title",
  "sources": {"worksheet": {"path": "university/course/worksheet.md", "version": "2026-09 edition"}},
  "refs": [{"source": "worksheet"}],
  "topics": {
    "linear-systems": {
      "assessment": {
        "summary": "Recognized coincident equations after a hint",
        "gap": "Independent classification remains untested",
        "observations": ["$attempt"]
      },
      "review": {
        "in_days": 2,
        "reason": "Check independent use after assisted success",
        "task": "Classify a new singular system and justify its solution count",
        "observations": ["$attempt"]
      }
    }
  },
  "focus": ["linear-systems"],
  "observations": [{
    "as": "attempt",
    "topics": ["linear-systems"],
    "text": "Recognized infinitely many solutions after the hint",
    "origin": "direct_attempt",
    "response": "The two equations describe the same line",
    "assistance": "Pointed out that the equations coincide",
    "refs": [{"source": "worksheet", "locator": "Exercise 5(b)"}]
  }],
  "tasks": {"exercise-5b": {"task": "Exercise 5(b)", "topics": ["linear-systems"], "question": "Justify the solution count for a new system", "assistance": "Coincident equations already explained"}},
  "current_task": "exercise-5b"
}
```

Send changed fields only. Scope metadata survives omission. `sources` and `topics` merge by handle; topic metadata merges. A topic's `assessment` and `review` replace as complete objects (`null` clears one). Store learner interpretations under `assessment`, never flat topic `summary`, `gap` or `status`. Assessment prose fields are `summary`, `gap`, `status` and `uncertainty`; `observations` identifies the supporting evidence. An explicitly uncertain assessment may have no support and remains pending. No numeric mastery score is inferred or validated.

The helper stamps assessments/reviews with `assessed_at` and an observation watermark `reviewed_through`; reads compute `pending` when relevant new evidence or corrections need reconciliation. Do not submit these fields. Before using a pending interpretation for a consequential decision, retrieve its relevant evidence and corrections, then replace it with the supported interpretation. A watermark records what was considered, not a guarantee that the judgment is true. Unrelated activity does not require reassessment.

`observations` appends new events on save and is keyed by handles on read. Submit each event once. Optional `as` names a local alias for that addition; `$attempt` can appear in reference lists in the same patch and is resolved to its assigned handle. Aliases do not persist. Preserve the actual response, assistance, task and uncertainty when diagnostic, without repeating the same prose across fields. Shared observations may name several topics.

Observation `origin` is `direct_attempt`, `self_report`, `tutor_inference`, `external_assessment` or `unknown`; omission means unknown. These labels describe where the evidence came from, not its reliability. Optional `provenance` preserves additional source context as text; migration keeps unclassified legacy origin text there and sets `origin` to unknown. The helper assigns UTC `recorded_at`; optional `date` is the known event date, not an invented date copied from the save time. Do not submit `recorded_at`. Missing assistance means unknown, never independent performance. Dates, task, response, assistance and uncertainty must use their canonical date/string types when present.

A real improvement is a new observation. Correct an incorrectly recorded event with a new observation containing `corrects: ["o1"]`, explaining the supported correction. Later learning does not erase an earlier genuine mistake. A tutor's factual error must not become a learner misconception: correct affected assessments, reviews and task assumptions too. A removed task is a completed workflow checkpoint, not evidence of mastery.

Source handles identify cited content. Optional `version` is an established edition/revision label, or null/omitted when unknown. Once cited, the handle's version cannot change; use a new handle for changed content. A path relocation may update the existing handle. References use `source`, optional `locator` and optional short `excerpt`; the helper captures `source_version`, which callers must not submit. Do not invent versions or copy whole sources into memory. Unknown handles are errors; repair the patch without dropping its evidence.

Tasks use stable logical keys across providers. Fields patch independently: omitted fields survive, null clears a field, and a null task removes it. Nested `frame` and `plan` replace as units. Other tasks survive; removing the current one clears its pointer. `current_task` is the default continuation, never an override of the learner's request. Keep the enduring task label, original purpose, current question and actual assistance clear. See [lessons.md](lessons.md) for frames and routes. Temporary handoff instructions belong in that task's `instructions`.

New reviews require `due: "YYYY-MM-DD"` or `in_days`, nonempty `reason` and retrieval `task`, and at least one supporting observation. Optional `retain: true` keeps lasting fundamentals in view. The tutor chooses pacing; the helper computes dates and caps a new interval before an upcoming exam. Use the resolved date from the receipt; do not resend an unchanged interval. Record meaningful review performance as an observation before revising its schedule. Migrated reviews with missing support or rationale remain pending.

`journal_activity` uses the exact established Journal label; an unmapped course is not zero study. `plan [SCOPE] --days N --horizon N` combines assessments, evidence, reviews, assessment context and recorded effort with scheduled study windows. Windows are not confirmed availability; hours are not mastery.

Use the receipt's revision for the next patch. On conflict, read and reconcile. If completion was uncertain, check whether the event committed before submitting it again. A successful receipt needs no confirming read. For a requested standalone artifact outside Pi's automatic lesson, pipe Markdown to `scripts/learn note --title 'Title'` and link its path; do not duplicate the mirrored lesson.
