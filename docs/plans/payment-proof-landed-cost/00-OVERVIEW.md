Tier 2. Backend single-phase skeleton. Wise integration handled separately.

# PaymentProof + LandedCostActual model + endpoints

## Goal
Capture proof-of-payment records and final actual landed-cost numbers per shipment, so the next layer (variance reconciliation, accounting export, Wise wiring) has a place to live.

## Exit criteria
- [ ] `PaymentProof` model: id, booking_id, invoice_id (Optional), supplier_pay_request_id (Optional), payment_type (supplier_invoice, freight_invoice, duty_gst, customs_brokerage, destination_delivery, other), paid_amount, paid_currency, paid_at, paid_by, payment_method (bank_transfer, card, wise, ofx, other), reference_number (Optional), proof_document_id (Optional), bank_account_last_digits (Optional), reconciliation_status (pending_review, matched, variance, rejected), variance_amount (Optional), reviewed_by (Optional), reviewed_at (Optional), notes (Optional), created_at, updated_at.
- [ ] `LandedCostActual` model: id, booking_id, estimated_total_usd (Optional), actual_total_usd, currency, supplier_invoice_amount (Optional), fx_cost (Optional), international_freight (Optional), platform_fee (Optional), origin_pickup (Optional), inspection (Optional), warehouse_charges (Optional), customs_duty (Optional), gst (Optional), broker_fees (Optional), port_charges (Optional), destination_trucking (Optional), insurance (Optional), storage_demurrage_detention (Optional), adjustments (Optional), variance_amount_usd (auto-derived if estimated set), variance_reason (Optional), finalised_at (Optional), created_at, updated_at.
- [ ] Store collections.
- [ ] Operations:
  - `record_payment_proof(store, booking_id, payload, actor)` writes the record + audit event.
  - `update_payment_proof_reconciliation(store, proof_id, status, variance_amount, actor)` flips reconciliation_status and notes.
  - `list_payment_proofs_for_booking(store, booking_id)`.
  - `record_landed_cost_actual(store, booking_id, payload, actor)` upserts the booking's LandedCostActual record (one per booking).
  - `get_landed_cost_actual_for_booking(store, booking_id)`.
- [ ] Endpoints:
  - `POST /bookings/{id}/payment-proofs` (importer auth)
  - `GET /bookings/{id}/payment-proofs` (importer auth)
  - `PATCH /payment-proofs/{id}` (admin auth) — only changes reconciliation fields
  - `POST /bookings/{id}/landed-cost-actual` (admin auth)
  - `GET /bookings/{id}/landed-cost-actual` (importer auth)
- [ ] At least 7 backend tests; total >= 292.
- [ ] Frontend types + api clients.

## Risks
- Don't recompute variance on the client side. Backend computes variance_amount_usd as `actual_total_usd - estimated_total_usd` when both present.
- Reconciliation patch is admin-only to avoid importer self-marking variance.
- LandedCostActual is one-per-booking; second POST replaces fields rather than creates a new row.

## Audit log

### AP1
Lens 1: most-likely-wrong assumption is that LandedCostActual should be one-per-booking. Confirmed by build plan spec: "Stores the final actual cost of a shipment". One-per-booking is right.

Lens 2: adversarial: variance recomputation must run on every PUT/POST so the field is always derived. Confirmed.

Revisions: variance_amount_usd is computed in the operation, not stored from client.

### AP2 — Post-execution audit (2026-05-11)

#### Lens 1 — Correctness
1. Wrong assumption surfaced: `reset_store_for_tests` had not been updated for any of the new collections shipped tonight (delivery_jobs, partner_*, contingency_options, payment_proofs, landed_cost_actuals, sentinel_subscribers, supplier_profile_claims). Caught by my own no-record test for landed cost. Fixed by adding all of them to the reset function.
2. Weakest exit criterion: 7 tests planned, 8 shipped including no-record 404 (the test that surfaced the reset bug).
3. Domain expert: would tie variance_amount_usd to currency conversion; v1 assumes USD-only variance.
4. Leaving on table: no automatic linkage from PaymentProof to a SupplierPayRequest's status. Acceptable for v1.
5. Unintended consequence: none — the reset fix actually makes other tests more reliable.

#### Lens 2 — Adversarial
1. Wrong assumption: that admin reconciliation patch could come before importer record. Order is enforced implicitly: admin can only PATCH an existing proof.
2. Weakest criterion: variance computation runs on every upsert. Verified in upsert test.
3. Domain expert: would record per-line cost components against a structured chart of accounts. Out of scope.
4. Leaving on table: no soft-delete on PaymentProof. Acceptable.
5. Unintended consequence: none.

#### Revisions applied
- `reset_store_for_tests` now clears all 8 collections introduced this session.

#### Exit criteria — final tick
- [x] Models + store collections — DONE
- [x] Operations including upsert with variance derivation — DONE
- [x] Endpoints (importer record + admin reconcile + admin record actual + importer view) — DONE
- [x] 8 backend tests pass; total 293 — DONE
- [x] Frontend types + clients — DONE
- [x] Build clean — DONE
