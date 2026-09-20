# Journal architecture

Journal has two feature packages. `sync` renders journal notes and runs session,
media, and grade commands. `learning` owns study memory, lesson publication,
retrieval, and teaching-client integrations. Both belong to the same project;
neither needs a generic application framework.

Learning reads recorded study activity and schedules through
`sync.study.context.journal_summary`. That read-only interface owns knowledge of
the journal's Markdown schema. Learning does not access the Flow database.
`sync.study.repository.FlowSessionRepository` owns Flow persistence and
transactions; session enrichment remains pure study-domain logic.

Within sync, readers parse external Markdown into contracts, metrics calculate
results, and writers render typed chart/table specifications. Application
services coordinate external sources and note publication. The CLI parses first
and constructs the integrations needed by the selected command. Small protocols
remain where they isolate real filesystem, database, and status inputs.

Note publication owns locking, conflict detection, no-op comparison, and atomic
replacement. Learning storage separately owns revision-checked JSON publication;
its evidence and lesson-ownership rules belong to learning. Raw files, shortcuts,
and model-generated JSON are validated on entry. Internal typed values are not
repeatedly converted back into generic mappings and validated again.

Each period synchronization reads its required dates once. Flow interruption
totals are loaded in grouped queries. Learning retrieval indexes observation
counts and traverses correction relationships directly. None of these require a
persistent cache or background worker.

## Maintenance

Run `python tools/check.py` from the project environment. Use `sync` or `learning`
as an optional argument for focused checks, and `--coverage` when coverage detail
is useful. Ruff, strict mypy, import contracts, Python tests, and the Pi adapter
tests cover the maintained code. The sync check also verifies rendering fixtures
without rewriting them.

Rendering fixtures are a compatibility contract, not refactoring targets. Changes
to architecture must preserve note text, whitespace, charts, tables, CLI behavior,
and stored learning records. Keep tests for observable behavior, external-input
errors, transactions, and concurrent publication. Avoid tests that merely assert
which private helper called another.
