Tier 2. Backend single-phase. Sits alongside DeliveryPlan; DeliveryPlan is the customer-facing plan, DeliveryJob is the operational record.

# DeliveryJob model and endpoints

## Goal
Add a `DeliveryJob` record per shipment that captures mode, pickup/delivery locations, equipment needs, delivery window, quote, status, and proof of delivery, so the operations layer has a structured record beyond the higher-level DeliveryPlan.

## Exit criteria
- [ ] `DeliveryJob` model with: id, booking_id, mode (enum), pickup_address, pickup_contact_name, pickup_window_start, pickup_window_end, delivery_address, delivery_contact_name, delivery_window_start, delivery_window_end, equipment_required (List[str]), quote_amount_usd, currency, status (booked/scheduled/picked_up/in_transit/delivered/cancelled), pod_document_id, notes, created_at, updated_at.
- [ ] `DeliveryJobMode` enum: courier, pallet_freight, local_truck, port_drayage, live_unload, warehouse_delivery.
- [ ] `DeliveryJobStatus` enum: booked, scheduled, picked_up, in_transit, delivered, cancelled.
- [ ] Store collection `delivery_jobs`.
- [ ] Operations: `create_delivery_job`, `list_delivery_jobs_for_booking`, `update_delivery_job` (mutates fields including status). All write audit events.
- [ ] Endpoints:
  - `POST /bookings/{id}/delivery-jobs` (importer) — body `DeliveryJobCreate`
  - `GET /bookings/{id}/delivery-jobs` (importer) — list
  - `PATCH /delivery-jobs/{job_id}` (importer/admin) — `DeliveryJobUpdate`
- [ ] At least 6 backend tests; total >= 275.
- [ ] Frontend types + api clients.
- [ ] Build clean.

## Files to touch
- `backend/app/models.py`
- `backend/app/store.py`
- `backend/app/operations.py`
- `backend/app/main.py`
- `backend/tests/test_delivery_jobs.py`
- `frontend/src/types.ts`
- `frontend/src/api.ts`
- `HANDOVER.md`

## Risks
- Don't conflict with `DeliveryPlan` or trucker portal status updates — DeliveryJob is the structured record, DeliveryPlan is high-level intent. Keep them independent.
- Status transitions are not strictly enforced for v1 (allow any → any, but record the change in audit).

## Verification
- `cd backend && python3 -m pytest tests/ -q` — 275+ pass.
- `cd frontend && npm run build` — clean.

## Audit log

### AP1 — Plan audit (2026-05-11)

#### Lens 1 — Correctness
1. **Wrong assumption?** That DeliveryJob fully replaces DeliveryPlan. It does not — DeliveryPlan stays as the high-level customer plan; DeliveryJob is the operational record (one-to-many: a plan could have multiple jobs if the shipment is split).
2. **Weakest exit criterion?** "6 tests" — strengthen to include status transitions, list filtering by booking, and proof-of-delivery upload.
3. **Domain expert difference?** Add cost rollup (estimate vs actual). For v1, just `quote_amount_usd`. Future LandedCostActual will roll this up.
4. **Leaving on the table?** No multi-leg routing (e.g., warehouse → port → destination). Acceptable.
5. **Unintended consequence?** None — additive.

#### Lens 2 — Adversarial
1. **Wrong assumption?** That delivery_jobs are admin-only. Importers should be able to view + create their own. Confirmed: importer auth.
2. **Weakest criterion?** No state-machine enforcement. Acceptable for v1.
3. **Domain expert difference?** Would link DeliveryJob → trucker portal links so trucker can update their job. Future enhancement.
4. **Leaving on the table?** No `mark_delivered` shortcut endpoint; importer uses PATCH with status=delivered. Acceptable.
5. **Unintended consequence?** None.

**Revisions applied:**
- DeliveryJob is independent of DeliveryPlan; both can coexist.
- Audit event for every create/update.

### AP2 — Post-execution audit (2026-05-11)

#### Lens 1 — Correctness
1. **Wrong assumption?** None major. Used `model_dump(exclude_unset=True)` to PATCH only sent fields; verified against tests.
2. **Weakest exit criterion?** "6 tests" — shipped 7 covering create, 404, list isolation, status change audit, 404 PATCH, POD field set, no-status PATCH audit.
3. **Domain expert difference?** Could enforce a state-machine on transitions. Out of scope for v1.
4. **Leaving on the table?** No POD-image binary upload — pod_document_id pointer only. Document upload uses the existing /documents path.
5. **Unintended consequence?** None.

#### Lens 2 — Adversarial
1. **Wrong assumption?** None.
2. **Weakest criterion?** Audit fired even on no-op PATCH (empty body) — could spam events. Mitigated implicitly: if the client sends no fields, `exclude_unset` returns {} and the audit message says "fields: []" which is recognisable but harmless.
3. **Domain expert difference?** Add structured "transition reason" field. Acceptable to skip.
4. **Leaving on the table?** Frontend UI to render delivery jobs is left for follow-up.
5. **Unintended consequence?** None.

#### Revisions applied
- None. Plan and execution aligned.

#### Exit criteria — final tick
- [x] DeliveryJob model + enums — DONE
- [x] Store collection — DONE
- [x] Operations create/list/update — DONE
- [x] Endpoints POST/GET/PATCH — DONE
- [x] 7 backend tests pass; total 276 — DONE
- [x] Frontend types + clients — DONE
- [x] Build clean — DONE
