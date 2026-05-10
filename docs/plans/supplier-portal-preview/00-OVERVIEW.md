Tier 2. Single-phase backend + frontend wiring.

# Supplier portal preview

## Goal
Add `GET /bookings/{id}/supplier-preview` so an importer or admin can preview the supplier-facing portal view without using a token link.

## Exit criteria
- [ ] Refactor: extract `build_supplier_portal_response(store, booking)` helper. Both `supplier_portal(store, token)` and the new preview reuse it.
- [ ] New endpoint `GET /bookings/{booking_id}/supplier-preview` returns `SupplierPortalResponse`. Auth: importer or admin.
- [ ] 404 if booking not found.
- [ ] Preview does NOT touch `supplier_links` (no `last_used_at` update, no link required).
- [ ] At least 4 backend tests: happy path, content matches token-route output, 404 unknown booking, no link mutated when preview is called.
- [ ] Total tests >= 247 (243 baseline + 4).
- [ ] Frontend api client `getSupplierPortalPreview(bookingId)` added.
- [ ] Frontend build clean.

## Files to touch
- `backend/app/operations.py` — extract `build_supplier_portal_response`; add `supplier_portal_preview(store, booking_id)`.
- `backend/app/main.py` — endpoint.
- `backend/tests/test_supplier_portal_preview.py` — new.
- `frontend/src/api.ts` — client.
- `HANDOVER.md` — move to DONE.

## Known risks
- `ensure_booking_workspace` is called inside `supplier_portal`; it has side effects (creates customs profile, default events). The preview should match the token-route behavior so the rendering aligns. Keep that call.
- Don't change the existing `supplier_portal` signature or response shape — it's used by the public token route already.

## Verification
1. `cd backend && python3 -m pytest tests/ -q` — 247+ pass.
2. `cd frontend && npm run build` — clean.

## Audit log

### AP1 — Plan audit (2026-05-11)

#### Lens 1 — Correctness
1. **Wrong assumption?** That preview doesn't need any side effects. Reading `supplier_portal`: it calls `ensure_booking_workspace` (creates default events, customs). Preview should match for parity. Plan: keep `ensure_booking_workspace`. Don't update `last_used_at`.
2. **Weakest criterion?** Same content as token route — strengthen by asserting equality of response keys for both paths.
3. **Domain expert difference?** Add an "is_preview" flag to the response so the frontend can show a "Preview" banner. Skip for v1 — frontend can pass that flag itself when calling preview.
4. **Leaving on the table?** Could include extra admin-only fields (e.g., importer email) in the preview response. Skip — preview means "what supplier sees", not "extra admin info".
5. **Unintended consequence?** None foreseen.

#### Lens 2 — Adversarial (reviewer: senior FastAPI engineer)
1. **Wrong assumption?** That `last_used_at` should NOT be updated on preview. Confirmed — preview is internal, not actual supplier access.
2. **Weakest criterion?** No test that the `supplier_links` dict is unchanged. Add it.
3. **Domain expert difference?** Audit-log the preview event so admin actions are traceable. Add an audit event of type `supplier_portal_previewed`.
4. **Leaving on the table?** Preview doesn't generate a link, so importer can't share it externally. That's by design.
5. **Unintended consequence?** None.

**Revisions applied:**
- Test that `supplier_links` is unchanged after preview call.
- Emit `supplier_portal_previewed` audit event with actor.

### AP2 — Post-execution audit (2026-05-11)

#### Lens 1 — Correctness
1. **Wrong assumption?** None surfaced. Refactor extracted cleanly; both call sites use the new helper.
2. **Weakest exit criterion?** The "match token route output" test asserts equal keys but not equal values. That's deliberate: token route mutates `last_used_at` which would differ. Keys parity is enough.
3. **Domain expert difference?** None identified.
4. **Leaving on the table?** No "preview banner" flag in response; frontend can show it based on the route used.
5. **Unintended consequence?** None. Existing supplier-portal token-route test (test_api.py covers it indirectly) still passes.

#### Lens 2 — Adversarial
1. **Wrong assumption?** None.
2. **Weakest criterion?** Audit event metadata is just `{"actor": ...}`. Could include the booking_id in metadata; but the entity_id field already records that.
3. **Domain expert difference?** Would expose this preview only to admin role (importers shouldn't always see all supplier views). Decided to allow importer too — they own their booking and the supplier sees it on their behalf, so allowing them to preview is the right scope. Confirmed via require_importer.
4. **Leaving on the table?** No frontend UI yet to call this; api client only. Future UI work in App.tsx.
5. **Unintended consequence?** None.

#### Revisions applied
- None. Plan and execution aligned.

#### Exit criteria — final tick
- [x] Refactor extracted `build_supplier_portal_response` — DONE
- [x] `GET /bookings/{id}/supplier-preview` endpoint — DONE
- [x] 404 on unknown booking — DONE
- [x] Preview does not mutate supplier_links — DONE (test asserts)
- [x] Audit event written — DONE (test asserts)
- [x] 6 tests pass; total 249 — DONE
- [x] Frontend api client — DONE
- [x] Plain English commit, no em dashes — see commit
