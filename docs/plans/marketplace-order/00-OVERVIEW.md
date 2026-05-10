Tier 2. Backend single-phase. Frontend UI for the Alibaba paste/import experience is out of scope; that's a follow-up.

# MarketplaceOrder model + ingest endpoint

## Goal
Capture optional marketplace-specific order data (Alibaba, 1688, Made-in-China, Global Sources, direct supplier, agent, trading company, other) so a forwarded marketplace order can be stored against a booking and surfaced later. Backend skeleton, no scraping or external API calls.

## Exit criteria
- [ ] `MarketplaceOrder` model: id, booking_id (Optional), import_project_id (Optional), marketplace, external_order_id (Optional), trade_assurance_status (Optional), supplier_profile_url (Optional), product_url (Optional), order_url (Optional), buyer_account_reference (Optional), agreed_terms_snapshot (Optional[str]), messages_snapshot_reference (Optional), payment_method (Optional), protection_notes (Optional), last_synced_at (Optional), sync_method (email_forward, document_upload, browser_extension, official_api, manual), created_at, updated_at.
- [ ] `MarketplaceProvider` enum: alibaba, direct_supplier, agent, trading_company, "1688", global_sources, made_in_china, other.
- [ ] `MarketplaceSyncMethod` enum.
- [ ] Store collection.
- [ ] Operations: `record_marketplace_order(store, payload, actor_id)`, `list_marketplace_orders(store, booking_id?, import_project_id?)`.
- [ ] Endpoints (importer-or-admin):
  - `POST /marketplace-orders` — body MarketplaceOrderCreate
  - `GET /marketplace-orders` — query by booking_id and/or import_project_id
- [ ] At least 5 backend tests; total >= 298.
- [ ] Frontend types + clients.
- [ ] Build clean.

## Files
backend models/store/operations/main + tests/test_marketplace_orders.py
frontend types/api
HANDOVER.md, docs/plans/marketplace-order/

## Risks
- The marketplace value `1688` starts with a digit; Python enum names can't. Use member name `marketplace_1688` with value `"1688"`.
- `agreed_terms_snapshot` is text; future work can promote it to a structured object.

## Audit log

### AP1
Lens 1: enum naming for `1688` is the main correctness risk. Use member name with prefix.
Lens 2: importer auth for both endpoints; admin can also call.

### AP2 — Post-execution audit (2026-05-11)
Lens 1: enum naming for `1688` worked with `marketplace_1688 = "1688"`. Build plan called for it; round-trip test confirms the wire value is `"1688"`.
Lens 2: filter endpoint accepts both booking_id and import_project_id; no auth confusion.
Revisions: none beyond plan.

#### Exit criteria — final tick
- [x] Models + enums — DONE
- [x] Store collection added + reset_store_for_tests updated — DONE
- [x] Operations record + list — DONE
- [x] Endpoints POST + GET (with filter) — DONE
- [x] 6 backend tests pass; total 299 — DONE
- [x] Frontend types + clients — DONE
- [x] Build clean — DONE
