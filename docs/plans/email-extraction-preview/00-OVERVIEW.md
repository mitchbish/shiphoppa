Tier 2. Single-phase backend + frontend wiring.

# Email extraction preview endpoint

## Goal
Add `POST /automation/extract-preview` so users can dry-run fact extraction on raw email/text without persisting a SourceMessage or applying anything to a booking. Frontend can show a "what we inferred" preview before the user forwards or applies.

## Exit criteria
- [ ] Endpoint accepts `{text: str, subject?: str}` and returns `{facts: List[ExtractedFact], extracted_count: int, would_match_booking_id: Optional[str]}`.
- [ ] Auth: importer or admin.
- [ ] No state mutation: no SourceMessage created, no AutomationRun, no booking write.
- [ ] `would_match_booking_id` populated by reusing the booking-id matcher from `automation.py:extract_facts_from_text`/`run_extraction_for_message` if any fact has field `booking_id` AND that id exists in the store; otherwise None.
- [ ] At least 4 backend tests: happy path with extractable facts, empty text returns empty facts, would_match reflects existing booking match, no mutation occurs (audit_events count unchanged).
- [ ] Frontend `extractFactsPreview(text, subject?)` client.
- [ ] Backend tests >= 260; frontend build clean.

## Files to touch
- `backend/app/main.py` — endpoint.
- `backend/tests/test_extraction_preview.py` — new.
- `frontend/src/api.ts` — client.
- `HANDOVER.md` — move to DONE.

## Known risks
- `run_extraction_for_message` mutates state. We only want the pure parser. Plan: import `extract_facts_from_text` directly.
- `would_match_booking_id`: only fill if extracted booking_id exists in store.

## Verification
1. `cd backend && python3 -m pytest tests/ -q` — 260+ pass.
2. `cd frontend && npm run build` — clean.

## Audit log

### AP1 — Plan audit (2026-05-11)

#### Lens 1 — Correctness
1. **Wrong assumption?** That `extract_facts_from_text` is pure. Read it (line 246). Yes — it returns facts from regex matching, no DB access.
2. **Weakest criterion?** "No mutation" — strengthen by snapshotting `len(audit_events)`, `len(source_messages)`, `len(automation_runs)` before/after.
3. **Domain expert difference?** Could try matching by container_id, vessel_name etc. as well, not just booking_id. Out of scope; v1 is booking_id only.
4. **Leaving on the table?** No PDF parsing in preview (text-only). Acceptable.
5. **Unintended consequence?** None.

#### Lens 2 — Adversarial (reviewer: senior NLP/regex engineer)
1. **Wrong assumption?** Regex extraction may reach into store state for cross-validation. Verified — it doesn't.
2. **Weakest criterion?** "Empty text returns empty" — could regress silently. Test asserts `extracted_count == 0` and `facts == []`.
3. **Domain expert difference?** Confidence scoring per fact. Already in ExtractedFact.confidence; no new work needed.
4. **Leaving on the table?** No throttling on the endpoint. Importer-only auth mitigates abuse.
5. **Unintended consequence?** None.

**Revisions applied:**
- Snapshot audit_events / source_messages / automation_runs counts in tests.
- `would_match_booking_id` only populated when extracted booking_id exists in store.

### AP2 — Post-execution audit (2026-05-11)

#### Lens 1 — Correctness
1. **Wrong assumption?** That booking_id was extractable from text. Reading `extract_facts_from_text`: it does extract `booking_id` (BKG-NNNN format). Test with a real booking confirmed.
2. **Weakest criterion?** `would_match_booking_id` test — the booking ID extraction depends on regex. Test now also includes the negative path (unknown booking).
3. **Domain expert difference?** Could match by container_id, vessel, or PO too. Out of scope for v1.
4. **Leaving on the table?** No PDF support in preview. v1 is text-only.
5. **Unintended consequence?** None.

#### Lens 2 — Adversarial
1. **Wrong assumption?** No.
2. **Weakest criterion?** Tested empty text, normal text, with-existing-booking, with-unknown-booking. Covered.
3. **Domain expert difference?** Could rate-limit. Importer auth scoping is fine for now.
4. **Leaving on the table?** Frontend UI to consume this is left to a follow-up.
5. **Unintended consequence?** None.

#### Revisions applied
- None.

#### Exit criteria — final tick
- [x] Endpoint accepts text + optional subject — DONE
- [x] Returns facts, count, would_match_booking_id — DONE
- [x] No state mutation (audit/source_messages/automation_runs counts unchanged) — DONE
- [x] 5 backend tests pass; total 261 — DONE
- [x] Frontend api client added — DONE
- [x] Frontend build clean — DONE
- [x] Plain English commit, no em dashes — see commit
