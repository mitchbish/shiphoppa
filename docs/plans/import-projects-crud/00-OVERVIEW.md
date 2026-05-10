# Saved import projects — CRUD

The `ImportProject` models exist (project, versions, snapshots, steps,
files, events) and the GET endpoints work, but there's no way to
create, rename, archive, clone, or delete a project from the API. This
slice adds the missing surface so importers can:

- Save a draft project before they have a booking.
- Rename or describe a project.
- Archive a finished one (soft-delete via status flip).
- Clone a past project as a starting point for a new one.
- Hard-delete a draft they never want.

## Phase

Single-phase Tier 2 — backend-only. Frontend "Save / Clone / Archive"
buttons can come in a follow-up; the API surface is the unblocker.

## Goal

Importers can POST `/import-projects` with a title, PATCH an existing
project to rename or update its status / current_step / next_action,
POST `/import-projects/{id}/clone` to duplicate, and DELETE to
soft-delete. All operations write audit events and append a project
version.

## Files to touch

- `backend/app/models.py` — `ImportProjectCreate`, `ImportProjectUpdate`.
- `backend/app/operations.py` — `create_import_project`,
  `update_import_project`, `clone_import_project`, `soft_delete_import_project`.
- `backend/app/main.py` — new endpoints: POST, PATCH, POST clone, DELETE.
- `backend/tests/test_import_projects_crud.py` — tests.

## Tests

1. POST creates a project with title + description; status active;
   audit event written; `project_created` version appended.
2. PATCH renames the project; updates `updated_at`; appends
   `project_updated` version.
3. PATCH on archived project still works (no 400 — archiving is just
   a status, not a freeze).
4. POST clone produces a new project with the same workflow_type,
   description, summary, and a fresh ID. Clone keeps a reference to
   the source via `source_project_id` in the version metadata.
5. DELETE flips status to `deleted_pending_retention` and sets
   `deleted_at`. The project still exists in store; GET returns it
   with the new status.
6. DELETE on already-deleted project is a no-op (idempotent).
7. PATCH with empty body returns the unchanged project.
8. POST with empty title returns 422.

## Out of scope

- Hard delete (would purge the project + cascading children). The
  soft-delete pattern is enough for v1.
- Per-step CRUD (steps are populated by automation; manual edits are
  a follow-up).
- Snapshot / version restore UI.
- Frontend "Save / Clone / Archive" buttons.

## AP1 audits

#### Lens 1 — Correctness (2026-05-11 09:50 AEST)

(a) Likely-wrong: that `owner_user_id` should be the importer's
    email. Looking at the existing `ensure_import_project_for_booking`
    flow (line 733), it sets owner to importer.email if available.
    For standalone create, I'll use the principal's actor_id (e.g.
    "dev-importer") which is what audit events use elsewhere.
(b) Weakest exit: test #1 "creates a project". Tighten by also
    asserting `project.id in store.import_projects` AND
    `len([v for v in store.import_project_versions.values() if
    v.import_project_id == project.id]) == 1`.
(c) Domain expert (product manager): would want the clone to also
    copy the linked purchase orders so the importer doesn't lose
    workflow continuity. For now, clone copies metadata only;
    linked_* arrays are reset. Clone-with-POs is a follow-up.
(d) Leaving on the table: bulk archive endpoint, project tags /
    folders, search. Out of scope.
(e) Unintended consequence: a soft-deleted project still appears in
    the GET list because the existing endpoint doesn't filter by
    status. Mitigation: extend the GET endpoint to skip
    `deleted_pending_retention` and `deleted` statuses by default;
    add `?include_deleted=true` opt-in.

#### Lens 2 — Adversarial (2026-05-11 09:53 AEST) — reviewer persona: a backend engineer reviewing a CRUD slice

(a) Idempotency on DELETE matters. Test #6 covers it.
(b) PATCH semantics: only update fields the caller sends (use
    `model_dump(exclude_unset=True)`). Don't blank fields the caller
    didn't include.
(c) Workflow type immutability: changing it mid-project is messy.
    Keep workflow_type out of the update model for now. Clone can
    create a project with a different workflow type explicitly.
(d) Audit + version on every write. Test #1 already covers create;
    add similar assertions to PATCH and DELETE tests.
(e) Empty title rejection (test #8) at the Pydantic layer using
    `Field(..., min_length=2)`.

#### Plan revisions

- GET `/import-projects` filters out deleted projects by default;
  query param `include_deleted=true` reverses this.
- `ImportProjectCreate.title` validated `min_length=2`.
- `ImportProjectUpdate` excludes `workflow_type`.
- Test #1 also asserts version count.
- PATCH and DELETE tests assert audit/version growth.

## Status — DONE 2026-05-11

10 new tests pass; full suite at 194.

#### AP2 Lens 1 — Correctness

All four operations (create, update, clone, soft-delete) wired to
endpoints. Each writes an audit event and an
ImportProjectVersion. Soft-deleted projects are excluded from the
default GET list, included with `?include_deleted=true`.

#### AP2 Lens 2 — Adversarial — reviewer persona: backend engineer reviewing CRUD diff

Validation: title `min_length=2` enforced at Pydantic layer (test
catches 422). PATCH uses `model_dump(exclude_unset=True)` so absent
fields are not blanked. Empty PATCH body short-circuits to a no-op
return without bumping `updated_at` or writing a version.

Idempotency: DELETE on already-deleted project returns the same
state without writing a duplicate audit event (early-return in
`soft_delete_import_project`).

Clone: copies metadata only; `linked_purchase_order_ids` and
`linked_shipment_ids` are reset (a clone is a fresh workflow). The
clone's `project_cloned` event captures the source ID.

#### AP2 findings — none blocking

## Follow-up backlog

- Hard-delete (with cascading purge of versions/snapshots/files).
- Per-step CRUD endpoints.
- Snapshot / version restore endpoint.
- Frontend "Save / Clone / Archive" buttons + draft list view.
- Clone-with-POs (carry over linked purchase orders).
- Project tags / folders.
- Free-text search across projects.
