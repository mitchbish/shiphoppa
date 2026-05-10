Tier 2. Backend single-phase skeleton. Detection rules + decision-card UI follow later.

# PartnerProfile + PartnerCapability + ContingencyOption skeleton

## Goal
Add the data model and CRUD endpoints for tracking each partner's capabilities and the contingency options proposed against a shipment, so the future contingency engine has a place to write its findings.

## Exit criteria
- [ ] Models:
  - `PartnerProfile`: id, partner_type (supplier, courier, broker, forwarder, warehouse, destination_agent, trucker, inspection, customs, other), name, contact_email, contact_phone, organization_id (Optional), preferred_channel (email/sms/whatsapp/wechat/portal), upload_permissions (List[str]), notes, active, created_at, updated_at.
  - `PartnerCapability`: id, partner_id, capability_type (supplier_production, origin_pickup, inspection, warehouse_receipt, customs_brokerage, port_drayage, local_delivery, freight_forwarding, payment_support), service_regions (List[str]), service_lanes (List[str]), equipment (List[str]), cutoff_rules (Optional[str]), operating_hours (Optional[str]), escalation_contacts (List[str]), average_response_hours (Optional[float]), average_completion_hours (Optional[float]), failure_rate (Optional[float]), cost_model (Optional[str]), active, created_at, updated_at.
  - `ContingencyOption`: id, booking_id, issue_type (production_delay, cutoff_miss, sailing_change, eta_slip, customs_hold, biosecurity_risk, payment_delay, release_block, trucking_risk, spare_space_opportunity), option_type (approve_change, book_next_sailing, change_trucker, request_partner_update, pay_charge, split_shipment, hold_for_review), plain_language_summary, cost_impact_usd (Optional), time_impact_days (Optional), risk_level (low/medium/high), source_evidence (Optional[str]), approval_request_id (Optional), status (proposed/approved/rejected/expired/applied), created_at, updated_at.
- [ ] Store collections: `partner_profiles`, `partner_capabilities`, `contingency_options`.
- [ ] Operations: create/list/update for each + decide_contingency_option (status transitions).
- [ ] Endpoints (admin):
  - `POST /partners`, `GET /partners`, `PATCH /partners/{id}`
  - `POST /partners/{id}/capabilities`, `GET /partners/{id}/capabilities`, `PATCH /partner-capabilities/{id}`
  - `POST /bookings/{id}/contingency-options`, `GET /bookings/{id}/contingency-options`, `PATCH /contingency-options/{id}`
- [ ] At least 8 backend tests; total >= 284.
- [ ] Frontend types + minimal api clients.

## Files
- backend/app/models.py, store.py, operations.py, main.py, tests/test_partner_capabilities.py
- frontend/src/types.ts, api.ts
- HANDOVER.md, docs/plans/partner-capability-skeleton/

## Risks
- Don't auto-create PartnerProfile from existing Booking supplier fields; that's future work. Endpoints are pure CRUD.
- ContingencyOption.approval_request_id is optional pointer; not auto-created.

## Audit log

### AP1 — Plan audit (2026-05-11)

#### Lens 1 — Correctness
1. Most likely wrong assumption: `model_dump(exclude_unset=True)` works on Optional Pydantic v2 fields. Verified in DeliveryJob earlier in this session.
2. Weakest exit criterion: "8 tests" — strengthen by including: partner-not-found 404 on capability create; contingency status transition adds audit event.
3. Domain expert: would tag PartnerProfile with default capability_types, but skipped to keep scope tight.
4. Leaving on table: no detection rules that auto-create ContingencyOption. Future engine work.
5. Unintended consequence: none; additive.

#### Lens 2 — Adversarial (senior product engineer)
1. Wrong assumption: that admin auth is fine. Confirmed. Importers may want to view options later — out of scope.
2. Weakest criterion: status transition logic is permissive. Acceptable.
3. Domain expert: would add fingerprinting / dedup for ContingencyOption on (booking, issue_type, option_type). Skip; rely on caller for now.
4. Leaving on table: no archival of expired options. OK.
5. Unintended consequence: none.

Revisions applied: none beyond clarifying optional fields.

### AP2 — Post-execution audit (2026-05-11)

#### Lens 1 — Correctness
1. Wrong assumption surfaced during execution: list endpoint sort needs deterministic tie-break. Fixed with `(created_at, id)` tuple sort. Same lesson applied earlier in shipments aggregator.
2. Weakest exit criterion: 8 tests planned, 9 shipped covering create + list + patch for partners, capabilities, and contingencies, including ordering, filtering, status-change audit, and 404 paths.
3. Domain expert difference: would auto-link new ContingencyOption to an ApprovalRequest. Skipped; client may set approval_request_id manually.
4. Leaving on table: no spinner/race protection on idempotent re-create. Acceptable.
5. Unintended consequence: none observed.

#### Lens 2 — Adversarial
1. Wrong assumption: that admin-only auth is fine. Confirmed.
2. Weakest criterion: status-change audit verified by event_type lookup.
3. Domain expert difference: auto-emit Sentinel error code on high-risk contingency. Out of scope.
4. Leaving on table: no UI to surface contingency cards. Backend ready.
5. Unintended consequence: none.

#### Revisions applied
- Tie-break sort on list endpoint.

#### Exit criteria — final tick
- [x] All three models, store, operations, endpoints — DONE
- [x] 9 backend tests pass; total 285 — DONE
- [x] Frontend types + api clients — DONE
- [x] Build clean — DONE
