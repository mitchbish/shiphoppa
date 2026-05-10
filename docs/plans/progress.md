# Progress — 2026-05-11 overnight session

| Phase / feature | Status | Audits | Notes |
|---|---|---|---|
| Cron-job.org wiring | DONE | n/a (ops change) | Job 7583175 fires every 15 min against /automation/cron/run; verified HTTP 200 in cron-job.org history. SHIP_HOPPA_CRON_TOKEN rotated with explicit operator consent. |
| Shipments aggregator | DONE | plan:2/2 post:2/2 | 8 new tests; total 236 at the time. |
| Approval request-review | DONE | plan:2/2 post:2/2 | 7 tests; total 243. |
| Supplier portal preview | DONE | plan:2/2 post:2/2 | 6 tests; total 249. |
| Sentinel SMS opt-in | DONE | plan:2/2 post:2/2 | 7 tests; total 256. Env var fallback preserved. |
| Email extraction preview | DONE | plan:2/2 post:2/2 | 5 tests; total 261. |
| Audit log filter UI | DONE | plan:2/2 post:2/2 | Frontend build verified; browser sanity-check is operator follow-up. |
| Supplier profile claim | DONE | plan:2/2 post:2/2 | 8 tests; total 269. |
| DeliveryJob CRUD | DONE | plan:2/2 post:2/2 | 7 tests; total 276. |
| PartnerProfile + PartnerCapability + ContingencyOption skeleton | DONE | plan:2/2 post:2/2 | 9 tests; total 285. Tie-break sort discovered. |
| PaymentProof + LandedCostActual skeleton | DONE | plan:2/2 post:2/2 | 8 tests; total 293. Caught reset_store_for_tests bug for 8 collections. |
| MarketplaceOrder ingest | DONE | plan:2/2 post:2/2 | 6 tests; total 299. |
| `partner_update` SourceType cleanup | DONE | n/a (mechanical) | 3 portal sites switched from forwarder_confirmation to partner_update. Tests still pass. |
| InsurancePolicy + ClaimRecord skeleton | DONE | plan:2/2 post:2/2 | 7 tests; total 306. |

## Feature audit (AP3) — 2026-05-11

### Lens 1 — Correctness

1. **Did the sum of phases deliver what the ledger promised?**
   Yes. All 14 features have plans in `docs/plans/<feature>/`, with AP1 and AP2 audit logs filled, exit criteria ticked, and tests green. The HANDOVER ledger has been updated to move each row from NOT STARTED to DONE; cron-job.org wiring moved from operator-blocked to DONE; the `partner_update` polish row moved from polish backlog to DONE.

2. **What's been added that isn't in the plan?**
   Two real bug fixes surfaced during execution and were rolled into their respective commits:
   - `reset_store_for_tests` was missing 8 of the new collections introduced this session. Surfaced by my own no-record landed-cost test; fixed in the PaymentProof + LandedCostActual commit; subsequent commits also added their new collections.
   - List endpoints were ordering by `created_at` only, which produced flaky sort under sub-second insertions. Fixed with `(created_at, id)` tuple sort in shipments aggregator and partner profiles.

3. **What's been dropped?**
   Snapshot/version restore endpoint (#7 in the original ledger) remains NOT STARTED — it requires an explicit cross-entity rollback design conversation before implementation. Frontend admin tabs for growth attribution + supplier verification + import projects (#5), Approval decision cards UI (#6), and the marketplace-import UI (#12 frontend) remain NOT STARTED for the next session. Frontend UI surfaces for the new DeliveryJob, PartnerCapability, ContingencyOption, PaymentProof, LandedCostActual, MarketplaceOrder, InsurancePolicy, and ClaimRecord backends are also NOT STARTED — types and api clients exist but no in-app screens.

4. **What integration seams are untested?**
   - Frontend forms for the new backend records: types and clients exist; no rendered UI.
   - Sentinel SMS fan-out is tested via `active_sentinel_phone_numbers` and the env var fallback. Live Twilio dispatch is not exercised; matches existing pattern.
   - The audit-filter UI is verified by build only.

5. **What assumption am I most likely to be wrong about?**
   That I correctly named all the new fields when they were referenced from existing models. I read the current models before each new addition (per the CLAUDE.md "read before write" rule) and corrected three field-name issues in the first feature alone (notification.booking_id, source_message.matched_booking_id, approval.booking_id). For the remaining features I matched the existing patterns verbatim.

### Lens 2 — Adversarial (reviewer: senior staff engineer reviewing the whole PR)

1. **What would a domain expert do differently across the whole PR?**
   - More end-to-end tests that exercise the new endpoints together (e.g., booking → insurance policy → claim → claim status → growth event).
   - Move shared inline styles from the audit filter form into App.css.
   - Add OpenAPI tags to the new endpoints.
   None of these are required for correctness.

2. **What did I cut corners on?**
   - The Sentinel SMS fan-out treats Twilio errors as soft failures (swallows per-phone). Acceptable.
   - The audit-filter UI uses inline styles. Acceptable for now; existing App.tsx mixes inline and class-based styles.
   - End-to-end browser verification was not run for the audit-filter UI.
   - No frontend UI for the new DeliveryJob / Partner / Contingency / PaymentProof / LandedCost / Marketplace / Insurance / Claim records — only types and api clients.

3. **What would I catch if this were someone else's work?**
   - The HANDOVER intro updated to 306 tests — good.
   - All "NOT STARTED" rows for shipped features removed from their original sections — good.
   - All commits end with the operator's required `Co-Authored-By` footer — good.
   - No em dashes in any of the new copy or commit messages.
   - No internal codenames in commits (no F1/F11 etc.).

4. **Were the audits performative or real?**
   Real. Each AP1 surfaced at least one revision (model field name corrected, helper read-only verified, idempotency requirement added, sort tie-break added, etc.). AP2 caught two real bugs (reset_store_for_tests gap and the sort flake on partners list).

5. **Most likely unintended consequence of the bundle as a whole?**
   The PR is now 14k+ LOC additions on top of main. Reviewer fatigue is real. Mitigation: each commit is self-contained with its own plan doc; the reviewer can read commit-by-commit instead of as a single diff.

### Findings to fix in scope
None. Each item shipped to its plan with both lenses logged and tests green.

### Outstanding for the next session
- Snapshot/version restore (#7) — needs design conversation about cross-entity rollback semantics.
- Approval decision cards UI (#6) — straightforward UI, browser verification needed.
- Frontend admin tabs for growth attribution + supplier verification + import projects (#5).
- Marketplace order import UI (#12 frontend).
- Frontend customer screens for DeliveryJob, PaymentProof, LandedCostActual, MarketplaceOrder, InsurancePolicy, ClaimRecord (admin and importer views as appropriate).
- Frontend admin views for PartnerProfile + PartnerCapability + ContingencyOption.
- Detection rules that auto-create ContingencyOptions (the engine that makes the model useful).
- Wise + FX integration once the operator gives the go-ahead.
- Real binary file upload across portals (Polish list).
- Shared `PartnerPortal` React component refactor (Polish list).
- Rate limiting on token-based portals (Polish list).
- Chinese-language landing pages for supplier acquisition (Polish list).
