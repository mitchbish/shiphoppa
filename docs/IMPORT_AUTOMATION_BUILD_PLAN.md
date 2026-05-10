# Ship Hoppa Import Automation Build Plan

## Product Direction

Ship Hoppa should become import and shipping automation software for small and medium businesses.

The current MCL booking product should become one module inside the main platform, not the centre of the product. The main product is a system that turns a company's existing shipping emails, supplier documents, courier invoices, broker updates, sailing data, customs information, trucking needs and payment approvals into one live import workflow.

The customer should not have to change behaviour before they get value. The first input should be the workflow they already use: email, PDFs, spreadsheets and partner messages.

For product purchases, Ship Hoppa should take over at the cleanest handoff point: once the buyer and supplier have agreed or drafted the order terms. Ship Hoppa should capture the order, check it, track production, manage payment workflow, prepare shipping and handle delivery.

Alibaba should be an optional wire-in, not the foundation of the product. The core system should work for any supplier relationship: Alibaba, direct factory, agent, trading company, 1688, Global Sources, Made-in-China, email-only suppliers or existing long-term supplier relationships.

## Core Principle

The app should ask for outcomes, not logistics steps.

Instead of asking a user to manually manage bookings, documents, trucking, customs, duties, invoices and release checks, Ship Hoppa should:

- ingest existing shipment information;
- create and update shipment records automatically;
- invite suppliers, couriers, brokers and warehouses to provide missing data directly;
- calculate duties, GST, landed cost, delivery cost and spare-space opportunities;
- prepare next actions automatically;
- ask the user to approve important decisions in plain language.

## Customer Phase Architecture

The customer app should be organised around three operational phases plus Account. This phase map should drive navigation, models, automation prompts, partner portals and admin queues.

### 1. Order

Order covers everything from "I am buying stock" to "the goods are approved and ready to be moved."

Order subtabs:

- **Supplier**: supplier details, order source, buyer handoff, supplier invite and missing supplier data.
- **Production**: purchase order, production milestones, ready date, delays and factory updates.
- **Inspection**: supplier photos, QC requirement, third-party inspection, defects and buyer approval before release.
- **Supplier Pay**: supplier invoice, deposit, balance, FX/payment quote comparison, approval and mark-paid-outside-app.
- **Docs**: commercial proof and product files, including commercial invoice, supplier photos, product specs and factory certificates.

Alibaba, 1688, Global Sources, Made-in-China and similar marketplaces are **Account integrations**, not primary Order tabs. The Order workflow should prompt the user to connect or import from Alibaba only when it can reduce typing, verify an order, or reconcile a supplier invoice. The core flow must still work from email, PDFs, spreadsheets, direct suppliers and agents.

### 2. Ship

Ship starts once the goods can move. It covers the physical and documentary handoff into logistics.

Ship subtabs:

- **Cargo**: cartons, dimensions, CBM, weight, goods category and container matching.
- **Ship Docs**: packing list, ISPM/fumigation evidence, shipping instructions, house BL, arrival notice and delivery order.
- **Pickup**: factory pickup, self-delivery, warehouse/CFS receipt deadline, origin trucking and cutoff feasibility.
- **Sailings**: origin, destination, sailing window, carrier/service options, ETD, ETA and available space.
- **Tracking**: journey map, milestone timeline, ETA and exceptions.

### 3. Clear

Clear covers the border, money owed to Ship Hoppa or partners, release, destination charges and final delivery.

Clear subtabs:

- **Customs**: HS code, incoterm, goods value, duty/GST/tax estimates, broker handoff and biosecurity checks.
- **Payments**: Ship Hoppa invoice, freight share, service fee, pickup fee, customs/brokerage/destination charges and release holds.
- **Delivery**: destination delivery profile, delivery booking, courier/trucker upload, proof of delivery and final landed-cost reconciliation.

### 4. Account

Account contains reusable settings that reduce repeated data entry.

Account subtabs:

- **Profile**: company details, contacts, delivery defaults and supplier defaults.
- **Integrations**: Alibaba and marketplace connectors, email ingestion, accounting, payment providers, storage and other reusable wires into the customer's existing workflow.

## Phase-By-Tab Build Sequence

Build the platform in the same order the customer experiences an import. Each tab should be useful on its own, but every tab should also feed the next tab automatically.

Current implementation status:

- **Account / Profile**: API-backed account profile, persistence, tests and booking-prefill wiring are implemented.
- **Account / Integrations**: API-backed integration records for Alibaba/1688, email inbox, accounting, Supplier Pay and Railway/R2 storage are implemented.
- **Account / Help**: implemented as a real guidance screen with importer/supplier/courier/broker handoff prompts.
- **Order / Supplier**: supplier details, email-ingestion demo flow, source-message matching and supplier portal actions are implemented.
- **Order / Production**: purchase order creation, production milestones, Supplier Pay quote generation and milestone completion actions are implemented.
- **Order / Inspection**: evidence check, inspection decision and QC pass gate are implemented on top of production milestones.
- **Ship / Pickup**: pickup details, cutoff protection and origin movement event actions are implemented.
- **Clear / Delivery**: API-backed delivery plan, release blocking, delivery detail saving, delivery booking endpoint and final delivery endpoint are implemented.
- **Verification**: backend tests, frontend build, frontend lint and browser checks have been run for the completed slices.

### Step 1: Account Foundation

Build Account first because it removes repeated typing from every later workflow.

1. **Profile**
   - Store organisation, contacts, default delivery location, default supplier locations, approval limits and preferred customs/delivery settings.
   - Feed these defaults into Order, Ship and Clear.
   - Acceptance: a new import can prefill buyer, delivery and common supplier fields from Account.

2. **Integrations**
   - Add integration records for marketplace, email, accounting, payments, object storage and partner systems.
   - Alibaba and similar marketplaces live here, not in the Order phase.
   - Order should prompt for Alibaba only when an order appears to have come from Alibaba or a marketplace import would save work.
   - Acceptance: the user can leave integrations disconnected and still complete the full workflow manually/email-first.

### Step 2: Order Phase

Build Order next because it creates the source data for every shipment.

1. **Supplier**
   - Capture supplier, origin, order source, contact, buyer handoff and supplier invite link.
   - Prompt for Alibaba/import integration only when relevant.
   - Acceptance: a supplier can be invited without seeing importer pricing.

2. **Production**
   - Create purchase order, milestones, ready date, delay state and automatic supplier update requests.
   - Acceptance: Ship planning can see a reliable expected ready date before cargo is ready.

3. **Inspection**
   - Support supplier photos, QC requirement, third-party inspection, defect report and buyer approval.
   - Acceptance: failed or unapproved inspection blocks the ready-to-ship gate unless waived.

4. **Supplier Pay**
   - Capture supplier invoice, deposit/balance, FX/payment quote comparison, approval and mark-paid-outside-app.
   - Acceptance: supplier payment status updates production and audit trail, but does not mix with Ship Hoppa freight invoice.

5. **Docs**
   - Store commercial proof: commercial invoice, supplier photos, product specs and factory certificates.
   - Acceptance: commercial proof can be used later by customs without re-uploading.

### Step 3: Ship Phase

Build Ship after Order because cargo can only move once Order has enough readiness and proof.

1. **Cargo**
   - Capture carton count, dimensions, CBM, weight, goods category and container-matching requirements.
   - Acceptance: matching rejects sailings that cannot make cutoff.

2. **Ship Docs**
   - Store packing list, ISPM/fumigation evidence, shipping instructions, house BL, arrival notice and delivery order.
   - Acceptance: movement documents are separated from commercial proof but share the same document engine.

3. **Pickup**
   - Plan Ship Hoppa pickup or self-delivery, supplier address, contact, pickup window, warehouse cutoff and origin trucking.
   - Acceptance: pickup feasibility is calculated before a booking is confirmed.

4. **Sailings**
   - Search by origin, destination and calendar window; show carrier, service, cutoff, ETD, ETA and available space.
   - Acceptance: selected sailing is respected unless feasibility fails, then the next feasible sailing is offered.

5. **Tracking**
   - Show route map, milestones, ETA and exceptions.
   - Acceptance: current and previous stages are visually clear and source/confidence is stored for every event.

### Step 4: Clear Phase

Build Clear after Ship because costs, customs and release depend on the confirmed shipment.

1. **Customs**
   - Capture HS code, incoterm, goods value, broker preference, biosecurity flags, duty/GST/tax estimate and broker handoff.
   - Acceptance: customs explanations are layperson-readable and country source data is stored.

2. **Payments**
   - Show Ship Hoppa invoice, freight share, service fee, pickup, customs/brokerage/destination charges, payment status and release holds.
   - Acceptance: invoice lines add up quickly and release stays blocked while payment holds are active.

3. **Delivery**
   - Use saved delivery profile, choose courier/trucker method, collect delivery window/equipment needs, courier invoice and proof of delivery.
   - Acceptance: delivery cannot be booked while customs, payment, document or release holds are unresolved.

### Step 5: Automation And Admin

After the customer tabs are structurally correct, add automation behind them in this order:

1. Intake and extraction from email, PDFs and marketplace imports.
2. Missing-data prompts to suppliers, couriers, warehouses and brokers.
3. Approval cards for money, inspection, sailing changes, customs and delivery.
4. Sentinel checks for stale data, failed integrations, missing deadlines and provider errors.
5. Admin exception queues that mirror the customer phases instead of becoming a separate manual workflow.

## Launch Country Scope

Launch countries should be:

- Australia;
- United States;
- China.

This does not mean the product is hard-coded to three countries. It means the first production-grade country packs must be complete for these markets before broad global expansion.

Country roles:

- **China**: origin-market supplier workspace, production control, pickup readiness, export documents, supplier outreach, Chinese-language supplier onboarding and China-to-overseas shipment handoff.
- **Australia**: importer workspace, ABN/GST context, ABF tariff/GST sources, BICON biosecurity checks, customs broker handoff, destination trucking and landed-cost reconciliation.
- **United States**: importer workspace, US tariff/customs references, customs broker handoff, destination delivery and landed-cost reconciliation.

Launch lanes should prioritize China-to-Australia and China-to-USA because those lanes exercise the full product: supplier, production, Supplier Pay, pickup, shipping, customs, delivery and landed cost.

## Production-Grade First Build Standard

Ship Hoppa should not be built as a disposable prototype with a vague promise to rebuild later.

The right delivery model is staged, but every stage should use the final product shape:

- real database-backed models, not throwaway state;
- provider adapter contracts from the first implementation;
- durable file storage shape from the first implementation;
- audit events for every important action;
- source references for every extracted fact;
- approval flows for money, legal, customs, release and delivery decisions;
- Sentinel health checks around integrations, queues, stale data and failed automations;
- plain-language customer UI over a complete operational model;
- manual or sandbox fallback only behind the same interface the live provider will use.

If a provider is not connected yet, the system can run in manual/sandbox mode, but the user flow, data model, audit trail and admin controls should be the same as the final flow.

Completion standard:

- no important information should live only in an email thread, spreadsheet or admin memory;
- every import can be saved, resumed, audited, exported and cloned;
- every customer-facing task has a clear owner, deadline, consequence and next action;
- every automation has a source, confidence level, fallback and failure code;
- every integration can fail gracefully without breaking the import workflow.

## Supplier-Side Wedge

Ship Hoppa should offer a free supplier workspace for suppliers in China and other origin markets.

The promise to suppliers:

"Make it easier for overseas customers to buy from you, pay you, track production, collect goods and ship internationally."

This helps suppliers look more professional to overseas buyers while giving Ship Hoppa clean upstream data before shipping starts.

The supplier workspace should be free because the commercial value comes from:

- importers using Ship Hoppa for shipping automation;
- MCL shared-space bookings;
- FCL spare-space recovery;
- Supplier Pay workflow;
- destination delivery and customs workflow;
- long-term network effects from more suppliers feeding accurate production and packing data.
- suppliers funneling overseas buyers into Ship Hoppa at the moment the buyer needs production tracking, payment, pickup, shipping and delivery help.

The supplier should not need a full account at first. They should be able to use a secure link, then optionally claim a free supplier profile later.

Supplier-led importer acquisition should be built into the workflow, not bolted on as a referral gimmick.

Examples:

- supplier creates a buyer-facing order status page and invites the overseas buyer;
- supplier sends a "Track production and shipping with Ship Hoppa" link;
- supplier shares pickup/packing details through Ship Hoppa instead of email attachments;
- buyer lands in a prefilled Ship Hoppa import workspace;
- Ship Hoppa suggests Supplier Pay, production tracking, pickup, MCL/FCL options, customs and delivery;
- supplier gets attribution when their buyer becomes an active importer.

## Irresistible Adoption Loop

Ship Hoppa should become easy to discover because it appears inside the workflows suppliers and importers already use.

The core loop:

1. Supplier uses Ship Hoppa for free to make overseas orders easier.
2. Supplier invites the overseas buyer to a professional order status page.
3. Buyer lands in a prefilled workspace with product, supplier, payment and production details already there.
4. Ship Hoppa offers the next obvious actions:
   - approve supplier payment;
   - confirm production milestones;
   - book QC;
   - prepare pickup;
   - find shared MCL space or manage FCL;
   - prepare customs;
   - book delivery to warehouse.
5. Buyer gets value before filling in a blank form.
6. Buyer asks future suppliers to use Ship Hoppa because it reduces chasing, payment admin and shipping confusion.
7. More suppliers join because overseas buyers prefer suppliers who can provide a cleaner post-order workflow.

This creates a two-sided adoption loop:

- suppliers bring importers;
- importers invite suppliers;
- every shipment creates more structured supplier, product, packing, payment and route data;
- better data makes the next shipment easier.

### Make It Irresistible For Suppliers

Supplier promise:

"Win and retain overseas buyers by giving them a clean production, payment and shipping experience after the order is agreed."

Supplier features:

- free supplier profile;
- buyer-facing order status page;
- production milestone tracker;
- packing list and commercial invoice uploader;
- pickup-ready checklist;
- professional "Ship Hoppa ready" export handoff;
- reusable pickup address, contacts and bank details;
- buyer invite links with order details prefilled;
- fewer repetitive overseas buyer questions;
- optional badges:
  - fast document response;
  - packing data complete;
  - ready-date reliability;
  - export-ready supplier.

Supplier should not be charged for this basic workspace. The supplier's job is to make overseas trade cleaner and introduce buyers into the Ship Hoppa workflow.

### Make It Irresistible For Importers

Importer promise:

"Forward the order. Ship Hoppa turns it into production tracking, supplier payment, pickup, shipping, customs and delivery."

Importer features:

- no blank onboarding;
- supplier invite comes prefilled;
- supplier chasing handled automatically;
- production and goods-ready dates tracked;
- Supplier Pay with mark-as-paid support;
- QC and photo reminders;
- shipping options prepared before goods are ready;
- landed cost and payment timeline;
- delivery-to-warehouse planning;
- all source emails, docs and decisions in one shipment record;
- Sentinel monitors the process and surfaces exceptions.

The first experience should feel like magic:

"I forwarded one supplier email and Ship Hoppa built the import workflow."

### Best Initial Customer Profiles

Start where the pain is sharp and repeatable.

Best-fit importers:

- Australian SMBs importing from China several times per year;
- bulky goods where freight cost and container space matter;
- importers using spreadsheets, inboxes and WhatsApp/WeChat today;
- importers with multiple suppliers and recurring SKUs;
- businesses paying suppliers in foreign currency;
- importers who regularly ask "where is my order?";
- businesses with 3-30 CBM shipments that are too big for parcel freight but too small for clean FCL economics;
- FCL importers with recurring unused container space.

Best-fit suppliers:

- Chinese suppliers selling to Australia, New Zealand, UK, US or Europe;
- suppliers with repeat overseas buyers;
- factories that already handle export documentation;
- suppliers who get frequent buyer questions about production, packing, payment and shipping;
- suppliers who want to look more professional than competitors;
- suppliers selling bulky, repeatable, container-friendly goods.

### Make It Easy To Come Across

Ship Hoppa should appear in distribution points that already exist.

Supplier-led discovery:

- supplier order status links;
- supplier email signatures;
- supplier WeChat/WhatsApp templates;
- QR code on pro forma invoice;
- QR code on packing list;
- "Track this order with Ship Hoppa" link;
- "Prepare pickup with Ship Hoppa" button;
- free supplier profile page;
- buyer-facing shipment-readiness page.

Importer-led discovery:

- forward-to-create-shipment email address;
- "invite supplier" button;
- accountant/bookkeeper referral for landed cost and payment reconciliation;
- customs broker referral;
- freight forwarder/warehouse referral;
- content around "how to import from China to Australia without spreadsheets";
- templates for PO, packing list, supplier payment and pickup readiness.

Operational discovery:

- every partner upload link should be branded and useful;
- every status page should have a clear "manage your next import with Ship Hoppa" path;
- every supplier-created buyer invite should produce a prefilled importer workspace.

### Activation Metrics

Measure whether the loop is working:

- supplier invite acceptance rate;
- buyer invite acceptance rate;
- forwarded email to shipment-created conversion;
- time from first email to first shipment workspace;
- percentage of shipments with supplier-provided packing data;
- percentage of payments marked/approved through Ship Hoppa;
- number of suppliers inviting more than one buyer;
- number of importers inviting more than one supplier;
- repeat shipment rate by importer;
- repeat overseas buyer count by supplier.

## China-First Supplier Acquisition Strategy

Ship Hoppa should target China first because the pain is dense: overseas buyers, supplier production updates, payment milestones, packing data, export pickup and Australia-bound shipping all collide in the same workflow.

The strategy should be supplier-led, but compliant. Do not build the company on automated Alibaba scraping, spam, fake buyer accounts or brittle page extraction. Alibaba should be treated as one research and relationship channel, not an owned database.

### Target Supplier Segments

Prioritize suppliers who are most likely to feel the pain and create importer demand:

- factories and trading companies selling bulky goods to Australia;
- suppliers with repeat overseas customers;
- suppliers already handling export documentation;
- suppliers with Trade Assurance / verified / Gold Supplier-style profiles;
- suppliers who sell products usually shipped by pallet, LCL, MCL or FCL;
- suppliers in categories such as furniture, tiles/stone, bathroom fittings, lighting, hardware, homewares, building materials, machinery, automotive accessories and garden products;
- suppliers in export-heavy regions such as Guangdong, Shenzhen, Guangzhou, Foshan, Dongguan, Zhongshan, Xiamen, Ningbo, Yiwu, Qingdao and Shanghai.

### Compliant Alibaba Research Loop

Use Alibaba as an automated research signal where permitted, not as an unapproved scraped database.

1. Generate high-fit category and region searches automatically.
2. Use search APIs, supplier-owned pages, approved directories, official/partner APIs and permitted public snippets to identify candidate companies.
3. If a supplier is discovered through Alibaba, store the profile URL and visible fit signals, then enrich from the supplier's own website or permitted public business sources.
4. Shortlist suppliers with visible export signals:
   - Australia/NZ buyers mentioned;
   - export-ready documentation;
   - Trade Assurance or verified profile;
   - strong response rate;
   - recurring product categories;
   - bulky/container-suitable goods.
5. Record only business contact details that suppliers publicly provide for sales contact or that come from compliant data partners.
6. Run automated dedupe, fit scoring, contactability checks and risk checks.
7. Send relevant outreach inside controlled limits.
8. Track reply, invite, activation and buyer-conversion rates.

Do not:

- scrape Alibaba at scale without permission;
- mass-message suppliers through platform messages;
- pretend to be a buyer;
- ask suppliers to move active Trade Assurance payments off-platform;
- use Alibaba logos or imply partnership without permission;
- rely on browser scraping as a core workflow.

Official API or partnership access can be explored later.

### Automated Supplier Intelligence Engine

The product should automate supplier discovery aggressively, but through a defensible pipeline.

Inputs:

- search APIs for category + city + export terms;
- supplier-owned websites and contact pages;
- approved business data providers;
- trade show and exhibitor data where reuse is permitted;
- public export directories;
- importer supplier invites;
- supplier referrals;
- warehouse, inspection and sourcing partner referrals;
- official marketplace APIs or partnership feeds where available;
- manually approved seed lists that the system expands into similar suppliers.

Automated workflow:

1. **Seed**
   - Admin chooses category, lane, city/region and target buyer profile.
   - Example: "bathroom vanities, Foshan/Guangdong, exports to Australia, bulky freight".

2. **Discover**
   - Run scheduled searches across permitted sources.
   - Pull candidate company names, websites, public profile URLs, categories and locations.
   - Respect `robots.txt`, platform terms, rate limits and source restrictions.

3. **Enrich**
   - Visit supplier-owned websites and permitted directory pages.
   - Extract company-level sales/export emails, phone numbers, WeChat/QR references, factory addresses, product categories, export markets and certificates.
   - Do not bypass login walls, CAPTCHAs, anti-bot controls or private messages.

4. **Verify**
   - Validate website, email format, domain match, duplicate records and bounced/suppressed contacts.
   - Prefer company domains over generic personal inboxes.
   - Flag risky records for review.

5. **Score**
   - Rank suppliers by fit, buyer value, category, export readiness, Australia relevance and likely freight pain.
   - Auto-reject low-fit, duplicate, blocked or non-export suppliers.

6. **Prepare Outreach**
   - Generate a short, Chinese-language message tailored to the supplier's product category.
   - Offer a free buyer order-status/export handoff page, not a generic freight pitch.
   - Include Ship Hoppa identity, contact details and opt-out.

7. **Contact**
   - Auto-send only to leads that pass source, compliance, duplicate and suppression checks.
   - Start with email/contact form/WeChat QR where appropriate.
   - Use SMS only as a later channel where the phone number is clearly published for business contact and the message can include opt-out.

8. **Learn**
   - Measure reply quality, supplier signup, importer invites and shipments created.
   - Feed winners back into the category/city scoring model.

This creates scale without turning Ship Hoppa into a platform-scraping or spam operation.

### Large-Scale Safe Supplier Discovery Engine

Ship Hoppa needs scale, but it should scale through automated permitted discovery, clean lead records, fit scoring and controlled outreach rather than unapproved platform scraping.

The safe acquisition system should have four layers:

1. **Discovery**
   - Alibaba, Made-in-China, Global Sources, 1688, trade show exhibitor lists, supplier websites, export directories, sourcing agent referrals, inspection company referrals, warehouse partner referrals and inbound Chinese landing pages.
   - Alibaba is used to identify supplier categories, company names, regions and product fit, not to mass-harvest platform data.
   - High-scale data sources should be public business directories, paid/compliant data providers, official APIs, approved platform partnerships or supplier-submitted profiles.

2. **Enrichment**
   - Find the supplier's own public website, export sales email, WeChat/QR, business phone, factory city, product categories, export regions and Australia/NZ signals.
   - Store the exact source URL, captured date and contact basis for every email or phone number.
   - Prefer company-level channels such as `sales@`, `export@`, contact forms, WhatsApp/WeChat business QR codes and published export sales numbers.
   - Avoid personal mobile numbers unless the person has clearly published that number for business/export enquiries or has given permission.

3. **Scoring**
   - Score suppliers before outreach so the team contacts fewer, better leads.
   - Suggested score inputs:
     - sells bulky goods suitable for LCL/MCL/FCL;
     - exports to Australia, New Zealand, US, UK or Europe;
     - has repeat overseas buyers;
     - publishes packing/export documentation;
     - is in a priority region;
     - has recent activity and strong response signals;
     - likely buyer pain: many custom orders, production milestones, photos, inspections, packing lists or pickup coordination;
     - likely importer value: high freight cost, recurring shipments or spare FCL space risk.

4. **Outreach Control**
   - Use low-volume, highly relevant first contact.
   - Human review is required before the first message to a new supplier until compliance and conversion are proven.
   - Automate follow-ups only after the first message is approved and only inside strict daily limits.
   - Stop automatically on opt-out, complaint, bounce, no-interest reply or poor-fit classification.
   - SMS should be secondary, not the default. Use it only where the number is published for business contact or there is a reasonable prior basis, and always include identity and opt-out wording.

The goal is not "message everyone". The goal is "find suppliers most likely to love the free supplier workspace, then make the first interaction useful enough that they invite their buyers."

### Supplier Lead Pipeline

Add a supplier acquisition CRM inside admin.

Lead states:

- discovered
- enriched
- scored
- needs_human_review
- approved_for_contact
- contacted
- replied
- onboarded
- referred_importer
- do_not_contact
- rejected

Required fields for every lead:

- company_name
- country
- city
- product_categories
- discovery_source
- discovery_source_url
- platform_profile_url
- company_website
- public_contact_source_url
- public_contact_captured_at
- public_email
- public_phone
- public_wechat
- preferred_language
- lead_score
- fit_reason
- compliance_basis
- contact_method_allowed
- last_contacted_at
- opt_out_at
- do_not_contact
- assigned_owner

Automation should be strict:

- duplicate detection by company name, website, email, phone and platform profile;
- suppression list checked before any send;
- per-channel daily send limits;
- message template approval;
- automatic unsubscribe and STOP handling;
- bounced email handling;
- audit event for every sourced contact, approval, send, reply and opt-out.

### Supplier Outreach Delivery Stack

Use:

- **Resend for email**
- **Twilio for SMS**
- **Sentinel for delivery, automation and error monitoring**

Email should run through Resend because it is the main scalable outreach and transactional channel.

Resend requirements:

- authenticated sending domain with SPF, DKIM and DMARC configured;
- separate outreach sender/subdomain from critical transactional mail;
- `Reply-To` routes into Ship Hoppa Inbox;
- unsubscribe handling and suppression list before every send;
- bounce, complaint and delivery webhooks;
- template versioning for English and Simplified Chinese;
- per-domain, per-category and per-country send limits;
- no supplier bank, cargo value or private importer data in marketing emails.

SMS should run through Twilio because it is a secondary urgency and invite channel, not the primary discovery channel.

Twilio requirements:

- verified sender or messaging service per supported country;
- webhook signature verification;
- delivery status callbacks;
- inbound STOP/START handling;
- phone number normalization and country validation;
- per-country compliance settings;
- no SMS to a supplier unless the number is a public business contact, a referral contact, or the supplier has opted in;
- no bank details, shipment value or private importer data in SMS.

Delivery records should be stored in an `OutboundMessage` or equivalent model:

- recipient_type: supplier, importer, courier, broker, admin
- recipient_id
- channel: email, sms, wechat, contact_form
- provider: resend, twilio, manual, other
- provider_message_id
- template_key
- template_version
- campaign_id
- subject
- body_snapshot
- status: queued, sent, delivered, opened, clicked, replied, bounced, complained, failed, opted_out
- failure_code
- sentinel_error_code
- sent_at
- delivered_at
- replied_at
- opt_out_at
- source_lead_id
- compliance_basis

Automation should never "fire and forget". Every message should have a provider record, audit event, opt-out path and Sentinel watch.

### Five Supplier Growth Upgrades

These are required before supplier acquisition scales hard.

1. **Supplier Verification**
   - Verify business legitimacy before a supplier can invite importers at scale or handle sensitive order data.
   - Check website/domain match, factory/export address, duplicate profiles, public business registration signals, export capability, high-risk categories, suspicious bank-detail changes and complaint history.
   - Give every supplier a verification state: unverified, basic_checked, verified, restricted, rejected.
   - Let low-risk suppliers create one free buyer order page quickly, but require stronger verification before bulk importer invites, payment workflows, bank-detail sharing or high-volume outreach.

2. **Deliverability Infrastructure**
   - Resend handles email; Twilio handles SMS.
   - Use separate outreach and transactional sending identities so supplier acquisition does not damage critical shipment notifications.
   - Maintain suppression lists, bounce handling, complaint handling, unsubscribe/STOP handling, daily send caps, domain warmup, template versioning and Sentinel monitoring.

3. **Chinese Supplier Onboarding**
   - Create a Simplified Chinese supplier landing page.
   - Support mobile-first setup, WeChat QR, no-card signup, one-order demo and a guided "create buyer status page" flow.
   - Target setup time: under 2 minutes for the first buyer order page.
   - Supplier should feel they are getting a free professional overseas-order tool, not being dragged into freight software.

4. **Claim Your Supplier Profile**
   - Ship Hoppa can create private draft supplier profiles from permitted public business data.
   - The supplier must claim, correct and approve the profile before Ship Hoppa treats it as supplier-owned or public.
   - Draft profiles must not imply endorsement, partnership or verified status.
   - Claimed profiles should unlock reusable company details, pickup addresses, packing contacts, export documents, buyer invite links and attribution.

5. **Growth Feedback Loop**
   - Track every supplier lead from discovery source to shipment revenue.
   - Capture source, category, region, message version, contact channel, reply, signup, buyer invite, importer claim, shipment created, revenue and opt-out/complaint rate.
   - Use this to automatically find better categories, cities, templates and channels.
   - The system should reduce bad outreach over time, not just send more of it.

### Safe Supplier Discovery Sources

Use a blended source strategy so growth is not dependent on one marketplace:

- **Marketplace research:** Alibaba, 1688, Made-in-China, Global Sources and category marketplaces, with platform terms respected.
- **Supplier-owned surfaces:** supplier websites, contact pages, catalogues, QR codes and export sales pages.
- **Trade events:** Canton Fair, industry expos, exhibitor lists and booth QR capture.
- **Partner networks:** China warehouses, inspection companies, sourcing agents, forwarders, export agents and local trucking partners.
- **Inbound engine:** Chinese-language supplier page, WeChat articles, QR flyers, product category landing pages and supplier referral links.
- **Customer-led invites:** importers invite their existing suppliers into the free workspace.
- **Supplier-led invites:** suppliers invite overseas customers after creating a free order page.

The fastest safe path is:

1. Build a targeted list from high-fit public business sources.
2. Enrich only company-approved public business contact channels.
3. Score for category, region and overseas buyer pain.
4. Send a useful free-order-page offer.
5. Let the supplier invite importers from inside Ship Hoppa.

### Outreach Compliance Guardrails

Ship Hoppa should treat supplier acquisition like a trust product.

Rules:

- Do not use address-harvesting software.
- Do not compile Alibaba site content into a private database without permission.
- Do not bypass CAPTCHAs, logins, rate limits or platform controls.
- Do not pretend to be a buyer.
- Do not imply Alibaba, Wise, OFX, carrier or forwarder partnership unless formally approved.
- Every outreach message must identify Ship Hoppa clearly.
- Every marketing email/SMS must include a simple opt-out.
- Opt-out must suppress the supplier across all channels.
- Keep evidence of contact source and consent/compliance basis.
- For Australian-linked messaging, assume ACMA spam rules apply.
- For US-linked messaging, assume CAN-SPAM requirements apply.
- For China-linked personal information, treat public business contacts carefully and provide a practical way to refuse further contact.

The product should prefer warm, useful acquisition loops over cold volume:

- importer invites supplier;
- supplier invites importer;
- warehouse partner invites supplier;
- inspection agent invites supplier;
- supplier creates free buyer status page;
- buyer claims the shipment.

### Supplier Offer

The outreach should not sound like freight software. It should sound like a sales-conversion tool for overseas buyers.

Positioning:

"Free order tracking and export handoff page for your overseas buyers."

Supplier benefits:

- look more professional to overseas buyers;
- reduce repetitive order-status questions;
- share production, packing and pickup readiness in one link;
- make it easier for buyers to pay, arrange pickup and ship;
- give buyers confidence after the order is agreed;
- increase repeat orders from overseas customers.

The supplier call to action should be very small:

- create a free supplier profile;
- create one test order;
- send one buyer a status link;
- upload packing/invoice data once.

### Outreach Channels

Use multiple channels so Alibaba is not the whole acquisition strategy:

- Alibaba supplier research;
- supplier websites found from Alibaba profiles;
- Made-in-China, Global Sources and 1688 research;
- Chinese export trade shows and exhibitor lists;
- sourcing agents and inspection companies;
- China warehouse partners;
- freight forwarders and export agents;
- LinkedIn for export sales managers;
- WeChat outreach where suppliers already prefer it;
- Chinese-language landing page and QR code;
- referrals from activated suppliers.

### Outreach Message

Short supplier message:

"We help Chinese suppliers give overseas buyers a free order status and export handoff page. Your buyer can see production status, packing documents, pickup readiness and shipping options in one link. It is free for suppliers. Would you like us to set up a free page for one Australia order?"

The first message should not mention every feature. It should offer one obvious thing: a free buyer-facing order page.

### Product-Led Supplier Funnel

1. Supplier lands on Chinese supplier page.
2. Supplier creates a free profile or uses a no-account setup link.
3. Supplier adds one order:
   - buyer email;
   - product;
   - quantity;
   - production date;
   - packing status;
   - pickup address.
4. Ship Hoppa creates buyer-facing status page.
5. Buyer opens page and sees:
   - production status;
   - documents;
   - payment status;
   - pickup readiness;
   - shipping to Australia options.
6. Buyer can claim the shipment into Ship Hoppa.
7. Supplier gets attribution.

### Trust And Localization

For Chinese suppliers, the product should feel local and easy:

- Chinese-language supplier landing page;
- WeChat-friendly invite links and QR codes;
- simple mobile-first supplier portal;
- no credit card required;
- no fee for supplier workspace;
- clear statement that supplier cannot see buyer-private shipping cost, landed cost or platform fees;
- clear statement that Ship Hoppa does not interfere with Alibaba Trade Assurance payments.

### China-First Experiment Plan

Run a controlled experiment before scaling.

Week 1:

- choose 3 product categories;
- manually shortlist 100 suppliers;
- enrich and score leads using the supplier discovery pipeline;
- create Chinese supplier landing page;
- create one-click supplier order page demo.

Week 2:

- send 50 highly targeted supplier messages;
- require human approval for every first contact;
- measure deliverability, replies, opt-outs and complaints;
- onboard 5-10 suppliers manually;
- create first buyer status pages.

Week 3:

- measure supplier activation;
- measure buyer page opens;
- interview suppliers and buyers;
- improve supplier onboarding.

Week 4:

- double down on the highest-response category and region;
- add WeChat/QR collateral;
- start referral loop from activated suppliers.
- only then increase daily outreach limits for the best-performing segment.

Success target:

- 10 active suppliers;
- 25 buyer order links created;
- 5 importers claiming a Ship Hoppa workspace;
- 1-2 shipments entering the import automation flow.
- zero spam complaints.

## Audit: What The First Plan Got Right And What Needed Improvement

The first plan correctly moved the centre of the product from `Booking` to `Shipment`. That is the right foundation.

The plan needed to be improved in four areas:

1. **Too much navigation before enough automation**
   - A customer should not need to understand eight tabs to get value.
   - The default experience should be a command centre that says what is happening, what is blocked and what needs approval.

2. **Too much model-first sequencing**
   - Adding models is necessary, but the first build slice must prove the end-to-end loop:
   - email or document in -> shipment created -> missing facts detected -> partner chased -> approval generated -> shipment updated.

3. **Not enough automation rules**
   - The plan listed features, but it did not define when the system acts automatically, when it asks the customer, and when it escalates to admin.
   - That decision ladder is the heart of friction-free software.

4. **Partner workflow was still too passive**
   - The importer should not manually chase suppliers, couriers or brokers.
   - Ship Hoppa should infer partner contacts from emails, generate scoped links and ask partners for missing information automatically where safe.

The improved plan below keeps the same architecture but makes the product simpler: one live shipment workspace, one action queue, one inbox intake layer and automated partner chasing.

## Automation And Simplicity Standard

Every feature must pass these tests before it is considered good enough:

- **Can this be inferred from an email, PDF, spreadsheet, prior shipment or partner response instead of asking the user?**
- **Can this be prefilled from the company profile or previous import history?**
- **Can the system make a safe decision automatically based on confidence and risk?**
- **If approval is needed, can it be one card with one clear action?**
- **If the user does nothing, can Ship Hoppa still chase the right party automatically?**
- **Can the user understand the status without knowing freight jargon?**

If a workflow fails these tests, it should be redesigned before more UI is added.

## Complexity Strategy: Powerful System, Simple Surface

Simplicity must not mean fewer capabilities. Ship Hoppa needs to become serious operating software, with enough depth to manage real imports, containers, customs, local delivery, partner uploads, payments and exceptions.

The product should handle complexity in layers:

1. **Default layer: simple**
   - Shows what is happening, what is blocked and what needs approval.
   - Uses plain language.
   - Avoids exposing every operational object at once.

2. **Workflow layer: guided**
   - When the user opens a shipment, the app shows the full workflow in sections:
     - journey;
     - documents;
     - money;
     - customs;
     - delivery;
     - messages;
     - space options;
     - audit trail.
   - Nothing important is removed; it is placed where the user naturally needs it.

3. **Power layer: complete**
   - Admin and advanced users can see the full operational model:
     - source messages;
     - extracted facts;
     - automation runs;
     - partner requests;
     - carrier schedules;
     - container capacity;
     - release holds;
     - invoices;
     - audit history.
   - This layer is for control, troubleshooting and scale.

The design goal is not to reduce complexity. The design goal is to make the system absorb complexity so the user does less work.

## Automation Decision Ladder

The software should not automate everything blindly. It should automate based on risk and confidence.

### Auto-Accept

Use when the fact is low-risk and high-confidence.

Examples:

- match an email to a shipment using PO number, supplier and container reference;
- attach a packing list to the right shipment;
- update ETA from a trusted carrier or forwarder email;
- mark a supplier photo as received;
- send a reminder for missing documents;
- create a draft delivery job from saved delivery preferences.

### Ask Customer Approval

Use when the decision affects money, timing, release, legal risk or customer preference.

Examples:

- pay duty/GST or an invoice;
- accept a sailing change;
- approve destination trucking;
- approve freight release;
- approve listing spare FCL space;
- approve a material invoice variance.

### Admin Review

Use when confidence is low or the issue is operationally risky.

Examples:

- unknown supplier or unclear shipment match;
- biosecurity risk;
- customs query;
- cargo compatibility uncertainty;
- late cargo near cutoff;
- conflicting ETA or invoice amounts;
- unusual delivery requirements.

This ladder should be encoded in the backend, shown in the admin automation queue and logged in audit events.

## Plain Language Rule

Customer-facing text should avoid freight jargon unless it is necessary. Where jargon is necessary, translate it.

Use:

- "Goods ready date" instead of "cargo ready date latest".
- "Arrive at warehouse by" instead of "warehouse receipt cutoff".
- "Port deadline" instead of "CY cutoff" or "gate-in cutoff".
- "Final delivery" instead of "last mile".
- "Delivery hold" instead of "release hold".
- "Needs review" instead of "admin review".
- "Money to approve" instead of "payment queue".
- "Ship Hoppa service fee - Priority" instead of hidden platform/rush fee language.

Internal APIs can use precise logistics terms. The UI should translate them.

## Current Software Position

The current app already has useful building blocks:

- `Booking`: importer request, cargo, supplier, cutoff and matching fields.
- `Container`: open container, filling, sailing and source-of-truth data.
- `SailingOption`: carrier schedule and deadline source data.
- `ShipmentDocument` and `DocumentRequirement`: document centre foundation.
- `ShipmentEvent`: tracking timeline foundation.
- `SupplierAccessLink`: supplier portal foundation.
- `Invoice`, `PaymentRecord` and `ReleaseHold`: payment and release foundation.
- `CustomsProfile`: customs and landed-cost foundation.
- `AdminTask`, `Notification` and `AuditEvent`: operations and automation foundation.

The main change is hierarchy:

Current centre:

`Booking -> Container -> Operations`

Target centre:

`ImportWorkspace -> Shipment -> Automation -> Space Products`

MCL booking and FCL spare-space recovery become offshoots of the shipment automation system.

## Target Information Architecture

### Customer Portal

The customer portal should not feel like operations software on first load. It should feel like a clean command centre with the full operating depth available inside each shipment.

Navigation is not a feature budget. The goal is not to remove functions; the goal is to put each function where the customer expects to find it.

Primary navigation should become:

1. **Today**
   - Default landing page.
   - Shows only what matters now:
     - shipments moving normally;
     - approvals needed;
     - documents or details missing;
     - delivery/release blockers;
     - better sailing or space opportunities.
   - This page should answer: "What do I need to do today?"

2. **Imports**
   - Live shipments.
   - ETA, status, current location, next action, release blockers and landed cost.
   - Each shipment opens into a visual workspace.

3. **Inbox**
   - Forwarded emails and attached files.
   - Shows what has been read, matched, extracted or needs review.
   - Later supports connected Outlook/Gmail inboxes.
   - The user should not live here; it is mainly there for trust and correction.

4. **Approvals**
   - The most important customer workflow.
   - Pay duty/GST, approve destination trucking, accept a better sailing, release freight, approve spare-space listing.
   - Approval cards must include the amount, reason, consequence and source document.

5. **Money**
   - Invoice-style breakdowns, landed cost, duty/GST, freight, local charges, delivery and service fees.
   - Every line should show whether it is estimated, confirmed, invoiced, approved or paid.

6. **Space**
   - One space workspace with two clear product paths:
     - find shared MCL space;
     - recover unused FCL space.
   - The system should recommend which applies based on shipment size and container data.
   - Both products remain fully functional and visible.

7. **Company**
   - Saved company profile, delivery locations, customs defaults, suppliers, team members and approval rules.
   - Users should not re-enter this data per shipment.

Shipment detail pages should contain secondary sections:

- Journey
- Documents
- Money
- Customs
- Delivery
- Messages
- Space options

This gives enough separation for clarity without making the top-level app feel like a logistics control panel. The functional depth still exists; it is reached through the relevant shipment or workspace.

### Customer Portal Sections Inside A Shipment

Each shipment should have one visual page with these cards:

1. **Where it is**
   - Map, ETA, current stage and route.

2. **What is needed**
   - Missing documents, missing values, supplier tasks, customs details and delivery details.

3. **Money**
   - Landed cost estimate, invoices, duty/GST and payment approvals.

4. **Delivery**
   - Saved destination, delivery method, window, equipment needs and proof of delivery.

5. **Space**
   - MCL buying option if the shipment is too small for FCL.
   - FCL recovery option if the container has safe spare capacity.

6. **Audit trail**
   - Source emails, documents and automation decisions.
   - This can be collapsed by default.

### Old Tab Mapping

The current app can be migrated without throwing work away:

- Current **Book** becomes **Space -> Find shared MCL space**.
- Current **Sailings** becomes part of **Imports** and **Space**.
- Current **Tracking** becomes the shipment **Where it is** card.
- Current **Docs** becomes the shipment **Documents** section.
- Current **Money** becomes the shipment **Money** section.
- Current **Customs** becomes the shipment **Customs** section.
- Current **Profile** becomes **Company**.

Do not remove useful work. Reframe it around the shipment.

### Admin Portal

Admin should be a full operating console, not a marketing page and not a manual data-entry maze. It needs all the operational depth, but the default view should prioritize exceptions and automation failures.

Primary admin navigation should become:

1. **Automation Queue**
   - The default admin page.
   - Emails that need matching, extracted facts that need review, stuck partner requests and automation failures.
   - Every item should show why the system could not safely continue.

2. **Shipments**
   - All active import jobs.
   - Status, ETA, blockers, next action and owner.

3. **Network**
   - Sailings, containers, trucking, warehouses and route data.
   - This replaces scattered container/sailing operational views.

4. **Partners**
   - Suppliers, couriers, brokers, forwarders, warehouses and destination agents.
   - Invite status, upload links and response history.

5. **Approvals and Payments**
   - Customer approvals, unpaid invoices, duty/GST payment queue, provider references.

6. **Customs and Release**
   - Customs status, biosecurity, broker handoff, release holds and delivery clearance.

7. **Audit**
   - Source documents, automation decisions, user actions, admin overrides.

Admin should support all operational functions, but every function should serve one of three jobs:

- review exceptions the system could not confidently solve;
- configure rules and partners so the same problem is automated next time;
- override risky workflows with a clear audit trail.

## Launchpad Asset Wiring Plan

Ship Hoppa should not rebuild common platform infrastructure from scratch. It should become a shipping/import automation product that wires into proven Launchpad assets through tenant/spoke adapters.

Principle:

- Launchpad owns shared infrastructure capabilities.
- Ship Hoppa owns shipping-specific data, workflows, UI language, operational rules and customer experience.
- Shared assets should be wired in through clean adapter contracts, not copied blindly.
- Healthcare-specific Launchpad logic must not be reused; only the reusable platform patterns and modules should come across.

### Core Assets To Wire In Early

**Sentinel**

Use Sentinel for coded error reporting, health checks, cron check-ins, incident routing, SMS cooldowns and admin automation queue creation.

Ship Hoppa use cases:

- shipment automation failures;
- supplier discovery failures;
- Resend/Twilio failures;
- stale ETA or sailing data;
- bank-detail change alerts;
- payment/release mismatches;
- customs/biosecurity blockers;
- failed background jobs.

**Admin Dashboard**

Use Launchpad's admin shell pattern as the base for Ship Hoppa admin.

Ship Hoppa admin modules:

- Automation Queue
- Shipments
- Supplier Discovery
- Network
- Partners
- Approvals and Payments
- Customs and Release
- Growth
- Program Health
- Audit

The admin dashboard should be operational, not marketing-heavy.

**Email Manager**

Use Email Manager as the core communication intake and drafting layer.

Ship Hoppa use cases:

- Outlook/Gmail import inbox;
- forwarded supplier emails;
- Alibaba/marketplace order emails;
- courier invoices;
- broker updates;
- carrier/forwarder confirmations;
- partner follow-up drafts;
- missing-data requests;
- learning from human-edited replies.

Initial mode should stay review-first for outbound replies. It can still automate ingestion, classification, matching, extraction, drafting and task creation.

**Knowledge Service (KS)**

Use KS as the evidence and memory layer.

Ship Hoppa knowledge packs:

- customs and biosecurity rules;
- duty/GST calculation notes;
- route and lane operating rules;
- warehouse cutoffs and SOPs;
- supplier onboarding rules;
- partner runbooks;
- carrier/forwarder documentation;
- Incoterms and document requirements;
- internal pricing and release policies.

KS should answer with citations/source references. It should not be the judgement layer for risky decisions.

**Consensus**

Use Consensus as the AI judgement and review layer for high-risk or ambiguous decisions.

Ship Hoppa use cases:

- HS code and customs-risk suggestions;
- supplier verification risk;
- bank-detail change review;
- payment/release conflict review;
- ETA contingency recommendation;
- better sailing recommendation;
- shipment exception classification;
- outreach compliance review;
- landed-cost variance explanation.

Consensus should produce an audit envelope: evidence used, models/rules considered, confidence, recommended action and whether customer/admin approval is required.

**Finance, Bookkeeping, Billing And Accounting**

Use Launchpad finance patterns for payments, bookkeeping, reconciliation and accounting sync.

Ship Hoppa use cases:

- customer invoices;
- supplier pay requests;
- FX quote records;
- payment approvals;
- outside-app mark-as-paid;
- duty/GST payment tracking;
- release holds;
- Xero reconciliation;
- revenue attribution by supplier lead, lane, container and customer.

Stripe/billing can handle Ship Hoppa subscriptions, platform fees, account plans or future paid automation tiers. Supplier Pay remains separate from stock finance.

**CMS, Landing Pages, SEO Engine And AI Citation**

Use Payload/CMS and Launchpad marketing assets for acquisition.

Ship Hoppa use cases:

- main automation homepage;
- FCL unused-space page;
- MCL/LCL space page;
- Chinese supplier landing page;
- supplier category landing pages;
- lane pages such as China to Australia, Vietnam to Australia, India to Australia;
- city/category pages such as Foshan furniture exporters or Ningbo hardware suppliers;
- knowledge/blog content for importers;
- AI Citation tracking for import/shipping questions in AI search engines;
- SEO Engine monitoring, keyword tracking, meta audits, competitor monitoring and content recommendations.

CMS should let marketing move quickly without changing the app. The product app should remain stable and operational.

**SEO Engine Supplier Acquisition Autopilot**

The SEO Engine should not only publish content. It should help Ship Hoppa find, attract and convert high-fit suppliers with minimal human intervention.

Core idea:

`SEO demand signal -> supplier segment -> landing page -> supplier discovery run -> compliant contact/enrichment -> free supplier workspace -> importer invite -> shipment/revenue attribution`

The SEO Engine should feed two growth paths:

1. **Inbound supplier growth**
   - Identify high-intent supplier categories, cities and lanes.
   - Generate CMS briefs for pages such as:
     - Foshan furniture exporters shipping to Australia;
     - Shenzhen electronics suppliers selling to US buyers;
     - Ningbo hardware exporters needing overseas order tracking;
     - China suppliers who want easier overseas buyer payments and pickup handoff.
   - Create Chinese-language supplier pages that offer the free supplier workspace.
   - Create category/city pages that explain the buyer order-status page, production tracker, packing upload, pickup handoff and importer invite flow.
   - Track which pages create supplier signups, buyer invites, importer claims and shipments.

2. **Outbound supplier discovery**
   - Use SEO keyword/category data to choose supplier discovery segments.
   - Run scheduled supplier discovery against permitted public sources, supplier-owned websites, approved directories, trade event lists, partner referrals and marketplace APIs/partnership feeds where allowed.
   - Enrich leads with company website, city, product category, export signals, public business contact channel and compliance basis.
   - Score suppliers by likely value, export readiness, bulky-goods fit, Australia/US buyer relevance and likelihood of inviting importers.
   - Create a private draft supplier profile and a tailored free-workspace offer.
   - Send outreach only through allowed channels after duplicate, suppression, source and compliance checks pass.
   - Track replies, signups, buyer invites, shipment creation, revenue, opt-outs and complaints.

Automation modes:

- **Review-first**: humans approve first sends, sources and templates while the system learns.
- **Guarded autopilot**: proven source/template/category combinations can send within strict daily limits after automated compliance checks.
- **Exception-only admin**: humans handle blocked sources, complaints, unusual contact methods, poor-fit leads, high-volume unlocks and compliance warnings.

The system should optimise for useful supplier onboarding, not bulk spam. It should automatically reduce or stop segments with poor replies, complaints, opt-outs or low importer conversion.

SEO Engine outputs should create or update:

- `SEOOpportunity`;
- `SupplierDiscoveryRun`;
- `SupplierLead`;
- `SupplierProfileClaim`;
- `OutboundMessage`;
- `GrowthAttributionEvent`;
- CMS landing pages and briefs;
- Sentinel alerts for failed discovery, stale source data, blocked crawling, deliverability problems or compliance failures.

**CRM, Referrals And Growth Attribution**

Use CRM/referrals patterns for importer, supplier and partner timelines.

Ship Hoppa use cases:

- supplier lead pipeline;
- importer lifecycle;
- partner timeline;
- supplier-sourced importer attribution;
- referral links;
- campaign/source tracking;
- importer claim tracking;
- shipment revenue attribution.

**Forms**

Use Forms for configurable intake where hardcoded product UI is unnecessary.

Ship Hoppa use cases:

- supplier onboarding forms;
- courier onboarding forms;
- warehouse access forms;
- broker intake forms;
- customs data collection;
- destination delivery access forms;
- trade show lead capture.

Core shipment workflows should still use purpose-built UI when speed and clarity matter.

**Program Health And Hub/Spoke Monitoring**

Ship Hoppa should expose clean heartbeats back to Launchpad:

- app version;
- module status;
- cron status;
- error-code counts;
- unresolved P0/P1 incidents;
- provider health;
- queue depth;
- data freshness.

Launchpad can monitor the whole company portfolio while Ship Hoppa operators see shipment-specific actions locally.

**Module Registry, Options And Guard**

Use Launchpad's module registry pattern so Ship Hoppa capabilities can be turned on, configured and monitored without hard-coding everything.

Ship Hoppa use cases:

- enable/disable Supplier Pay;
- enable/disable supplier discovery;
- enable route/map features by rollout stage;
- set automation limits by company;
- gate high-risk Consensus features;
- expose per-module status in Program Health.

**Tenant, Brand And Company Onboarding**

Use Launchpad tenant/brand/company-onboarding patterns for importer workspaces and internal setup.

Ship Hoppa use cases:

- company profile;
- default warehouses;
- preferred brokers;
- approval limits;
- connected inbox;
- brand/domain settings;
- billing details;
- default lanes;
- automation preferences.

**Audit Writer And Source Audit**

Use Launchpad audit patterns as a hard requirement.

Ship Hoppa use cases:

- every extracted fact has a source;
- every automation decision has a rule, confidence and outcome;
- every admin override records who, when and why;
- every payment/release decision is traceable;
- every supplier outreach/contact record has source and compliance basis.

**Metrics, Funnel And Monday Briefing**

Use Launchpad metric patterns for operating rhythm.

Ship Hoppa use cases:

- active shipments;
- blocked shipments;
- average days saved;
- landed-cost variance;
- supplier response time;
- document completion time;
- booking cutoff misses prevented;
- supplier leads -> importer claims -> shipments;
- revenue by lane, supplier source and customer.

**Segmentation, Engagement, Retention And Referrals**

Use Launchpad lifecycle patterns once the core import workflow is stable.

Ship Hoppa use cases:

- importers with repeat lanes;
- suppliers likely to invite more buyers;
- dormant importers;
- FCL buyers with spare space;
- LCL/MCL buyers ready to consolidate;
- partner referral loops;
- win-back campaigns based on actual import behaviour.

### Assets To Use Carefully Or Later

**Commerce Operations**

Borrow patterns for product, inventory, cart, shipping and fulfilment health, but do not turn Ship Hoppa into a normal ecommerce store.

Useful pieces:

- inventory/location thinking for container capacity and warehouse receipt;
- fulfilment-status patterns for delivery jobs;
- checkout/payment-health patterns.

**AI Content Generation**

Use through SEO/CMS workflows with human review, not as uncontrolled publishing.

**AB Testing**

Use for landing pages and onboarding flows once traffic exists.

**Social Listening**

Useful later for supplier/importer acquisition intelligence, not core v1.

**Learning Loop**

Use once the first workflows are stable. It should propose automation improvements from repeated admin edits, not silently change rules.

### Launchpad Integration Boundaries

Do not wire everything directly into customer actions on day one.

Rules:

- customer-facing actions require clear Ship Hoppa UI;
- Launchpad assets can power the background automation;
- every automation output must map back to a Ship Hoppa object: Shipment, SupplierLead, SupplierWorkspace, PurchaseOrder, Invoice, ReleaseHold, SourceMessage, OutboundMessage or AdminTask;
- high-risk actions create approvals, not silent changes;
- every integration writes audit events;
- privacy-sensitive context passed to shared assets must be scoped and redacted.

## Systematicly Project Storage Lessons

Systematicly has a useful project pattern: each complex workflow is a durable, resumable workspace with phase data, generated artefacts, file storage, collaboration, version history and an append-only state/payment ledger.

Ship Hoppa should borrow that structure for imports.

### Saved Import Projects

An import should be saved as a project, not treated as a disposable booking form.

`ImportProject` should be the durable container for:

- purchase orders;
- supplier details;
- production milestones;
- payments;
- documents;
- shipments;
- sailings/containers;
- customs profile;
- landed cost;
- delivery jobs;
- partner messages;
- approvals;
- audit trail.

A project may contain one shipment or several related shipments.

Examples:

- one supplier order split across two sailings;
- one production order that becomes an FCL container;
- one importer season/order campaign made of multiple purchase orders;
- one supplier-created buyer handoff page that later becomes a full shipment.

### Systematicly Storage Pattern To Copy

Systematicly's project storage gives Ship Hoppa a practical template:

- `projects` table for project identity, owner, title, status and current phase;
- `phase_data` JSONB table for flexible per-step data while the product evolves;
- `generated_content` style records for generated outputs, summaries and packs;
- `project_files` table for file inventory and primary file storage;
- `project_collaborators` and pending invitations for controlled sharing;
- `kv_store` as a recovery/resume layer for session-shaped JSON while workflows are still changing;
- append-only event ledgers for money and entitlement state;
- version log entries for who changed what and when;
- R2 archive snapshots for durable backup.

Ship Hoppa should adapt this into import language:

- `ImportProject` maps to Systematicly `projects`;
- `ImportProjectStepData` maps to `phase_data`;
- `ImportProjectFile` maps to `project_files`;
- `ImportProjectCollaborator` maps to `project_collaborators`;
- `ImportProjectEvent` maps to append-only ledgers;
- `ImportProjectSnapshot` maps to R2 archive snapshots.

The important lesson: a saved project is not only one row. It is project identity, step data, files, collaborators, versions, events and snapshots working together.

### Phase Data Without Losing Structure

Use a workflow registry similar to Systematicly's project workflow registry.

Each import project has:

- workflow_type: standard_import, supplier_handoff, fcl_spare_space, mcl_shared_space, customs_only, delivery_only
- workflow_version
- current_step
- status
- step_data / phase_data
- completed_steps
- blocked_steps
- next_action

This keeps the UX simple while allowing different import types to share the same storage model.

### Autosave And Rehydrate

Every meaningful user, partner or automation action should autosave the project.

Requirements:

- no user should lose a half-completed import plan;
- forms can be resumed;
- partner data updates rehydrate into the main customer view;
- extracted facts stay attached to their source;
- every project can be reconstructed from database records and files;
- every workflow step can be revisited without blank fields.

### Project Files And Data Room

Systematicly separates project files by project and folder. Ship Hoppa should do the same.

Suggested file structure:

- `orders/`
- `supplier_invoices/`
- `commercial_invoices/`
- `packing_lists/`
- `photos/`
- `qc_reports/`
- `booking_confirmations/`
- `warehouse_receipts/`
- `customs/`
- `payments/`
- `delivery/`
- `claims/`
- `exports/`
- `snapshots/`

Production storage should follow the Systematicly pattern: Railway as the main operational platform, Railway Postgres as the everyday persistent store, local filesystem only as a fast disposable cache, and Cloudflare R2 as the highly secure backup/archive store.

Local dev storage is acceptable only behind the same storage interface. The API shape should already look like durable object storage.

### File Storage Requirement

File storage means the system has a reliable way to store the actual files attached to an import project: PDFs, spreadsheets, photos, reports and proofs.

Systematicly's current pattern is the reference:

- everyday project file storage can live in Railway Postgres through a `project_files` table;
- local filesystem is only a cache and should be assumed disposable on deploy;
- R2 is archive/backup, not the live interactive file browser;
- file access goes through backend routes and permission checks;
- every file is addressed by `{project_id}/{folder}/{filename}`;
- every backup copy is timestamped so versions are preserved.

The database stores searchable metadata:

- project_id;
- shipment_id;
- folder;
- filename;
- file type;
- size;
- checksum;
- storage provider;
- storage key;
- upload source;
- extracted facts;
- approval/rejection status.

The file-byte store stores the actual file:

- commercial invoice PDF;
- packing list spreadsheet;
- supplier photos;
- QC report;
- booking confirmation;
- customs documents;
- delivery proof;
- claim evidence.

This is required for scale because import files can be large, long-lived and legally important. It also makes it easier to move between Railway Postgres, Cloudflare R2, S3, Vercel Blob or another provider without changing the product experience.

### Railway And R2 Storage Architecture

Preferred production shape, copied from the Systematicly approach:

- Railway runs the backend services, workers, queues and primary Postgres database.
- Railway Postgres stores operational records, project/session state, phase/step data, file metadata, file bytes where appropriate, audit events, extracted facts, workflow state and provider references.
- Local filesystem cache can improve speed, but it must never be treated as durable.
- The file-storage adapter writes file bytes through a provider interface so the backend can change storage mode without changing the app.
- Cloudflare R2 receives a durable append-only backup/archive copy of every important import file.
- R2 backup/archive is used for legal records, disaster recovery, claims packs, customer exports and long-term retention.
- R2 should not be the default interactive read path. The app should read from primary storage; R2 restore should be an admin/recovery process unless a one-off migration flag is enabled.
- R2 credentials should be scoped as tightly as possible. The ideal backup key can write objects but cannot list, read, modify or delete them.

File writes should be treated as a two-step durable operation:

1. Store the file through the active storage provider.
2. Attempt timestamped R2 backup/archive replication.

R2 backup failure should not block the customer action, but it must create a Sentinel alert and retry path. This matches Systematicly: the live app continues, but backup health is visible.

Do not design the product so that files are trapped in one provider. The `ImportProjectFile` record should always know the active storage provider, storage key, checksum, R2 archive key and backup status.

### Version History And Snapshots

Borrow Systematicly's version-log idea.

Track:

- who changed what;
- which workflow step changed;
- source document/message;
- before/after summary;
- automation or human action;
- timestamp;
- rollback/restore reference where possible.

Create snapshots at major milestones:

- order confirmed;
- production complete;
- cargo received;
- container/sailing booked;
- departed;
- arrived;
- customs cleared;
- delivered;
- landed cost finalised.

Snapshots should be useful for audits, claims, disputes and customer support.

### Collaboration And Permissions

Borrow Systematicly's project collaborator pattern, but adapt it to import operations.

Internal collaborator roles:

- owner;
- operations;
- finance;
- warehouse;
- viewer;
- external accountant/bookkeeper.

Permissions:

- can_view;
- can_edit_order;
- can_edit_shipping;
- can_approve_payment;
- can_view_costs;
- can_manage_partners;
- can_export;
- can_invite;
- can_delete/archive.

External partners still use scoped partner links rather than full project access by default.

### Append-Only Ledgers

Systematicly's per-project event-ledger pattern is important. Ship Hoppa should use append-only ledgers for money, release and major workflow state.

Use append-only events for:

- payment status;
- invoice issue/void/adjustment;
- Supplier Pay approval;
- release-hold creation/waiver;
- shipment state transitions;
- project access/billing;
- insurance/claim events.

Never overwrite the history of money or release decisions.

### Project Templates And Cloning

A repeat importer should be able to create the next import from a previous one.

Support:

- "Create similar import";
- saved supplier/order templates;
- saved SKU import profiles;
- saved lane preferences;
- saved customs broker and warehouse preferences;
- saved approval rules;
- recurring import schedules.

This is one of the biggest simplicity gains for repeat customers.

### Export And Portability

Every import project should be exportable.

Exports:

- shipment summary PDF;
- document ZIP;
- landed-cost spreadsheet;
- audit trail CSV;
- customs/broker handoff pack;
- claim pack;
- project JSON export for support/admin restore.

### Soft Delete And Archive

Use soft deletion for accounts and projects where possible.

Import projects should support:

- active;
- archived;
- cancelled;
- deleted_pending_retention;
- deleted.

Hard delete should respect legal, accounting and customs record-retention requirements.

## Order-To-Arrival Automation Backbone

Maximum automation requires a control system underneath the simple UI.

Ship Hoppa should manage the whole chain as one lifecycle:

`Order agreed -> Deposit/payment -> Production -> QC -> Packing -> Pickup -> Warehouse/CFS receipt -> Cutoff check -> Container/sailing -> Export docs -> Departed -> In transit -> Arrival -> Customs/biosecurity -> Destination charges -> Release -> Local delivery -> Delivered -> Actual landed cost`

### Shipment State Machine

Every shipment should have one canonical state and one next best action.

Core states:

- draft_order
- order_confirmed
- deposit_due
- deposit_paid
- production_in_progress
- qc_required
- qc_booked
- qc_passed
- packing_required
- cargo_ready
- pickup_scheduled
- picked_up
- warehouse_received
- measured_and_checked
- variance_pending
- shipping_plan_ready
- customer_approval_required
- container_or_lcl_booked
- export_docs_required
- waiting_sailing
- departed_origin
- in_transit
- eta_changed
- arrived_port
- customs_pending
- biosecurity_pending
- destination_charges_due
- release_blocked
- released
- delivery_scheduled
- delivered
- landed_cost_finalised
- closed

Every state transition should define:

- trigger event;
- required source;
- required confidence;
- allowed automation action;
- customer approval requirement;
- admin review requirement;
- rollback path;
- notification rules;
- Sentinel checks.

The customer should never need to understand the state machine. They see plain-language status and the next action.

### Master Data And Entity Resolution

The app must automatically understand that messy real-world records refer to the same thing.

Resolve and deduplicate:

- supplier names across invoices, emails, marketplace orders and websites;
- importer company names and contacts;
- shipment references;
- purchase order numbers;
- invoice numbers;
- product/SKU names;
- container numbers;
- vessel/voyage names;
- warehouse addresses;
- bank accounts;
- broker/courier/forwarder contacts.

Entity matching should use deterministic rules first, then AI-assisted suggestions with evidence.

Never silently merge high-risk entities such as bank accounts, suppliers, invoices or release holds.

### Source-Of-Truth Hierarchy

Automation needs a clear conflict rule when sources disagree.

Suggested hierarchy:

1. Admin-confirmed or customer-approved record
2. Direct carrier/forwarder/partner confirmation
3. Supplier portal or partner portal update
4. Connected inbox email from a verified sender
5. Uploaded document with extracted facts
6. Manual customer entry
7. Estimated schedule, tariff, route or landed-cost model

When a lower-confidence source conflicts with a higher-confidence source, the system should not overwrite silently. It should create a review item explaining the conflict.

Examples:

- supplier says cargo ready Friday, invoice says shipment date next Tuesday;
- forwarder ETA conflicts with visibility provider ETA;
- commercial invoice value differs from payment amount;
- supplier bank details differ from previously verified bank account;
- measured CBM differs from supplier-declared CBM.

### Product And SKU Import Memory

Ship Hoppa should learn how each company imports each product.

For each recurring product/SKU, store:

- supplier;
- product name and aliases;
- HS code suggestions and past decisions;
- duty rate history;
- GST treatment;
- biosecurity flags;
- packaging type;
- carton/pallet dimensions;
- weight and CBM history;
- inspection requirement;
- typical production lead time;
- typical origin pickup needs;
- landed cost history;
- variance history.

This is how the second shipment becomes much easier than the first.

### Partner Capability And SLA Engine

Partners should not be generic contacts. The system should know what each partner can do and how reliable they are.

Track:

- supplier response speed;
- warehouse receipt hours and cutoff rules;
- broker document requirements;
- courier service areas;
- trucking equipment;
- port/depot capabilities;
- inspection company regions;
- forwarder lanes;
- payment terms;
- average turnaround time;
- failure rate;
- escalation contacts.

This lets Ship Hoppa ask the right partner automatically and avoid partners who cannot solve the current job.

### Contingency And Better-Option Engine

Automation should not only follow the plan. It should look for a better plan.

Detect:

- supplier production delay;
- cargo missing current cutoff;
- better sailing option;
- cheaper or faster local trucking option;
- warehouse congestion;
- customs or biosecurity hold risk;
- ETA slipping;
- payment delay that may block release;
- FCL spare-space opportunity;
- MCL consolidation opportunity;
- delivery appointment risk.

For each issue, the system should produce a decision card:

- what changed;
- best option;
- backup option;
- cost impact;
- time impact;
- risk;
- approve/decline/ask Ship Hoppa.

### Integration Connections

Ship Hoppa should integrate into the customer's current flow wherever possible.

Priority integrations:

- Microsoft 365/Outlook/Exchange and Google Workspace/Gmail for shipment emails;
- Xero/QuickBooks/MYOB for invoices, bills, payments and reconciliation;
- Shopify/WooCommerce and common inventory systems for SKU/import demand context;
- CSV/spreadsheet import for companies without formal systems;
- Wise/OFX for Supplier Pay quotes;
- Resend for email;
- Twilio for SMS;
- carrier/forwarder/visibility APIs for schedules, cutoffs, ETAs and tracking;
- broker/warehouse/courier partner portals via secure links before formal APIs.

Every integration should degrade gracefully to email forwarding and document upload.

### Email Ingestion

Email ingestion means Ship Hoppa can receive, read, classify and act on shipping-related emails and attachments with the customer's permission.

It should support:

- a forwarding address such as `imports@shiphoppa.com` or a customer-specific forwarding address;
- connected Microsoft 365/Outlook/Exchange inboxes where the customer authorizes access;
- connected Google Workspace/Gmail inboxes where the customer authorizes access;
- IMAP/forwarding fallback for other major providers where API access is limited;
- China-relevant provider support through forwarding, IMAP or partner-specific connectors where available, including Tencent/QQ enterprise mail, Alibaba Mail and NetEase/163-style business inboxes;
- shipment mailbox rules so the app reads only relevant import emails where possible;
- attachment extraction for invoices, packing lists, photos, booking confirmations and broker documents;
- matching emails to the right import project, supplier, purchase order, shipment or invoice;
- extracting facts such as ready date, invoice amount, bank details, vessel/voyage, ETA, cutoff, container number and delivery address;
- creating missing-data requests, approval cards or admin review tasks automatically.

The customer should be able to keep working the way they already work: forward the supplier email, CC Ship Hoppa, or connect their shipping mailbox. Ship Hoppa turns that messy inbox traffic into structured import records.

Email ingestion must include:

- consent and mailbox scope;
- source-message storage;
- attachment storage;
- duplicate detection;
- sender verification;
- confidence scoring;
- audit trail;
- opt-out and privacy controls;
- Sentinel checks for failed parsing, stale inbox sync and unmatched messages.

Provider priority:

1. Microsoft 365 / Outlook / Exchange.
2. Google Workspace / Gmail.
3. Forwarding-address intake for any provider.
4. IMAP where the provider supports it safely.
5. China-market business email providers through forwarding first, then provider-specific connectors if usage justifies it.

### Actual Landed Cost And Margin Feedback

The system should not stop at estimates.

For every shipment, reconcile:

- supplier invoice;
- FX/payment cost;
- international freight;
- platform/service fee;
- origin pickup;
- inspection;
- warehouse/CFS charges;
- customs duty;
- GST;
- broker fees;
- port/depot charges;
- destination trucking;
- insurance;
- storage/demurrage/detention;
- adjustments and credits.

Then compare:

- estimated vs actual landed cost;
- planned vs actual ETA;
- supplier quoted dimensions vs measured dimensions;
- expected vs actual duties/charges;
- product margin impact.

This is how Ship Hoppa becomes the import operating system, not just a booking tool.

### Customs Source Strategy

There are official customs and tariff sources in most countries, but there is not one clean global customs API that answers every landed-cost and import-compliance question.

Reasons:

- HS codes are internationally harmonized only at the first six digits; countries extend and interpret them differently;
- duty depends on destination country, origin country, trade agreement, product classification, customs value and concessions;
- GST/VAT/import tax rules sit beside customs duty and vary by country;
- biosecurity, product safety, anti-dumping, licensing and sanctions rules often live in separate agencies;
- official sources are often HTML, PDFs, spreadsheets or portals rather than complete APIs;
- customs brokers and importers remain responsible for declarations and classification decisions.

Ship Hoppa should still use official government sources wherever possible.

Build a `CustomsSourceConnector` layer by country:

- Australia: ABF working tariff, ABF GST/import tax rules, BICON biosecurity checks, ATO GST deferral references;
- United States: USITC HTS, CBP rulings, Partner Government Agency flags;
- China: export-side tariff/document guidance, GACC references, supplier export document requirements and origin-side compliance data where relevant;
- United Kingdom: UK Trade Tariff and HMRC import VAT/duty guidance;
- European Union: TARIC and Access2Markets;
- New Zealand: Customs tariff and MPI biosecurity sources;
- Canada: CBSA tariff and CFIA/other agency requirements;

Launch-country connector priority:

1. Australia import connector.
2. United States import connector.
3. China origin/export connector.

Other countries should use the same connector interface later, but should not distract from completing these three launch-country packs first.

For each customs result, store:

- source country;
- source agency;
- source URL or dataset version;
- retrieved_at;
- HS/classification basis;
- duty rate;
- tax treatment;
- biosecurity/product-risk flags;
- confidence;
- broker_review_required;
- customer-facing explanation.

Customer-facing rule:

- show duty/GST/landed cost as a calculated estimate until a broker, admin or official declaration confirms it;
- use plain language for why the estimate changed;
- keep the official source link and source timestamp behind the explanation.

### Insurance, Claims And Exception Recovery

Add insurance and claims as a later but planned workflow.

Track:

- insurance required/waived;
- insured value;
- insurer/provider;
- policy reference;
- claim trigger;
- damaged/missing cargo photos;
- survey report;
- claim amount;
- claim status;
- recovery outcome.

Claims should reuse documents, photos, shipment events, packing lists, commercial invoices and delivery proof already in the system.

### Authority, Compliance And Approval Boundaries

Automation should act quickly, but only inside authority limits.

Rules:

- customs, tariff and biosecurity outputs are estimates or broker-prepared items unless reviewed by the appointed broker/admin;
- Supplier Pay requires customer approval before funds move;
- outside-app mark-as-paid can be accepted from authorized finance users, but high-risk rules can request optional proof or admin review;
- supplier bank-detail changes always create a high-risk review item;
- release of freight requires payment/document/customs holds to clear or be waived by authorized admin;
- customers approve material cost increases, sailing changes, delivery bookings and customs submissions where required;
- the app can chase partners automatically, but should not invent missing facts.

Every approval should answer:

- what action will happen;
- who is responsible;
- how much it costs;
- what deadline it protects;
- what happens if the user does nothing;
- what source evidence supports it.

## Friction-Free UX Requirements

These requirements apply to every customer-facing workflow.

### One Input, Many Outputs

When a customer provides one document or email, the system should use it everywhere it can.

Example:

- A commercial invoice should update goods value, supplier, cargo description, HS-code suggestion, landed-cost estimate, document checklist and customs profile.
- A booking confirmation should update carrier, vessel, voyage, ETD, ETA, cutoffs, route map and tracking timeline.
- A courier invoice should update delivery job cost, money tab, payment approval and delivery audit trail.

### Ask The Best Person, Not The Importer By Default

If information is missing, the system should decide who is most likely to know it.

Examples:

- Packing dimensions -> supplier.
- Proof of delivery -> courier.
- Duty note -> broker.
- Terminal availability -> forwarder or carrier source.
- Delivery access requirements -> importer warehouse contact.

The importer should only be asked when they are the right person or when approval is needed.

### Prefill Before Asking

Every form should start with the best known answer.

Sources:

- company profile;
- previous shipments;
- supplier history;
- source emails;
- document extraction;
- carrier/forwarder data;
- partner portal responses.

If confidence is low, show "We think this is X. Please confirm." Do not show a blank field unless the system genuinely knows nothing.

### Actions Must Be Decision Cards

Every approval should have:

- the action in plain English;
- the amount, date or operational impact;
- why the action is needed;
- what happens if the user approves;
- what happens if the user does nothing;
- the source document or message;
- approve, reject and ask Ship Hoppa buttons.

### Advanced Detail Is Always Available

Simple UX must not hide the audit trail. Every automated output should let the user or admin open:

- source email;
- source document;
- extracted facts;
- confidence;
- automation rule used;
- human overrides;
- related partner messages.

## Data Model Evolution

Add these core models while keeping the existing models:

### Organization

Represents the importing company.

Fields:

- company name
- billing details
- ABN or tax identifiers
- default delivery locations
- default customs broker preference
- approval rules
- connected inbox settings

### User

Represents people inside the organization.

Fields:

- role: owner, operations, finance, warehouse, viewer
- approval limits
- notification preferences

### ImportWorkspace

Represents the company's import operating space.

Fields:

- organization_id
- default lanes
- default suppliers
- default warehouses
- automation settings

### ImportProject

Represents a saved, resumable import job.

Fields:

- organization_id
- owner_user_id
- workflow_type: standard_import, supplier_handoff, fcl_spare_space, mcl_shared_space, customs_only, delivery_only
- workflow_version
- title
- description
- status: active, archived, cancelled, deleted_pending_retention, deleted
- current_step
- next_action
- blocked_reason
- summary
- created_at
- updated_at
- archived_at
- deleted_at
- linked_purchase_order_ids
- linked_shipment_ids
- linked_supplier_workspace_id

`Shipment` remains the physical/logistics movement. `ImportProject` is the saved customer workspace around the job.

### ImportProjectStepData

Stores flexible workflow-step data while the product is evolving.

Fields:

- import_project_id
- step_key
- step_number
- data
- status: not_started, in_progress, complete, blocked, skipped
- source_references
- updated_at

This is the Ship Hoppa equivalent of Systematicly phase data.

### ImportProjectVersion

Stores version history.

Fields:

- import_project_id
- version_number
- changed_by
- action
- step_key
- source_reference
- before_summary
- after_summary
- created_at

### ImportProjectSnapshot

Stores milestone snapshots for audit, claims, disputes and restore.

Fields:

- import_project_id
- snapshot_type: order_confirmed, production_complete, cargo_received, sailing_booked, departed, arrived, customs_cleared, delivered, landed_cost_finalised, manual
- snapshot_data
- file_manifest
- created_by
- created_at
- storage_key

### ImportProjectCollaborator

Stores internal project access.

Fields:

- import_project_id
- user_id
- role: owner, operations, finance, warehouse, viewer, external_accountant
- status: pending, accepted, revoked
- invited_by
- invited_at
- accepted_at
- can_view
- can_edit_order
- can_edit_shipping
- can_approve_payment
- can_view_costs
- can_manage_partners
- can_export
- can_invite
- can_archive

### ImportProjectFile

Stores file metadata for the project data room.

Fields:

- import_project_id
- shipment_id
- folder
- filename
- content_type
- size_bytes
- storage_provider
- storage_key
- backup_provider
- backup_storage_key
- archive_storage_key
- archive_created_at
- backup_status: pending, complete, failed, not_required
- checksum
- uploaded_by
- source_message_id
- document_id
- created_at

Storage behavior should mirror Systematicly:

- primary read/write path uses Railway Postgres or the configured primary file store;
- local disk can cache but must not be authoritative;
- R2 archive keys should be timestamped so a changed file does not overwrite prior evidence;
- R2 is backup/archive by default, not the customer-facing file browser.

### ImportProjectEvent

Append-only event ledger for major project state.

Fields:

- import_project_id
- event_type
- event_reference
- actor_type: user, partner, system, admin
- actor_id
- metadata
- occurred_at

### Shipment

This becomes the central object.

Fields:

- organization_id
- reference number
- purchase order reference
- supplier
- origin
- destination
- cargo summary
- status
- ETA
- current stage
- total landed cost estimate
- release status
- automation confidence
- linked booking_id, container_id, customs_profile_id, invoice_id

Existing `Booking` becomes a child object of `Shipment`, used when the shipment needs container space.

### ShipmentStateTransition

Stores the lifecycle history and controls the next automation step.

Fields:

- shipment_id
- from_state
- to_state
- trigger_type: source_message, document_upload, partner_update, payment_update, tracking_update, admin_override, system_rule
- trigger_reference
- confidence
- automation_decision: auto_accepted, approval_required, admin_review_required, blocked
- customer_visible_summary
- internal_reason
- occurred_at
- created_by

### EntityResolutionRecord

Stores matches and merge decisions across messy real-world data.

Fields:

- entity_type: supplier, importer, product, shipment, purchase_order, invoice, container, vessel, address, bank_account, partner_contact
- candidate_a
- candidate_b
- match_score
- match_evidence
- decision: auto_matched, suggested, rejected, merged, split
- risk_level
- reviewed_by
- reviewed_at

High-risk entities such as bank accounts, invoices and release holds should never be silently merged.

### ProductImportProfile

Stores import memory for recurring products/SKUs.

Fields:

- organization_id
- supplier_id
- sku
- product_name
- product_aliases
- hs_code_history
- duty_rate_history
- gst_treatment
- biosecurity_flags
- packaging_type
- carton_dimensions
- pallet_dimensions
- weight_history
- cbm_history
- inspection_required_default
- typical_production_days
- typical_origin_pickup_needs
- landed_cost_history
- variance_history
- last_imported_at

### PurchaseOrder

Represents the product purchase before it becomes a shipment.

Fields:

- organization_id
- supplier_id
- marketplace_source: alibaba, direct_supplier, other
- marketplace_order_reference
- purchase_order_number
- product_summary
- product_specs
- quantity
- unit_price
- total_value
- currency
- incoterm
- deposit_terms
- balance_terms
- agreed_ship_date
- production_due_date
- quality_terms
- trade_assurance_used
- order_status
- linked_shipment_ids

### MarketplaceOrder

Stores optional marketplace-specific order data. This is not required for direct supplier workflows.

Fields:

- marketplace: alibaba, direct_supplier, agent, trading_company, 1688, global_sources, made_in_china, other
- external_order_id
- trade_assurance_status
- supplier_profile_url
- product_url
- order_url
- buyer_account_reference
- agreed_terms_snapshot
- messages_snapshot_reference
- payment_method
- protection_notes
- last_synced_at
- sync_method: email_forward, document_upload, browser_extension, official_api, manual

### ProductionMilestone

Tracks the pre-shipping production workflow.

Fields:

- purchase_order_id
- milestone_type: deposit_paid, production_started, sample_ready, sample_approved, production_complete, qc_booked, qc_passed, qc_failed, balance_due, goods_ready
- due_date
- completed_at
- owner: supplier, buyer, inspector, ship_hoppa
- status
- evidence_document_id
- notes

### QualityInspection

Tracks optional QC before goods are released for shipment.

Fields:

- purchase_order_id
- inspection_required
- inspection_provider
- inspection_date
- inspection_location
- report_document_id
- result: pending, passed, failed, rework_required, waived
- defects_summary
- buyer_approval_required

### SourceMessage

Stores inbound emails or partner-submitted messages.

Fields:

- source_type: forwarded_email, connected_inbox, supplier_portal, courier_portal, broker_portal, admin_upload
- from, to, subject, received_at
- raw body
- attachments
- matched shipment
- extraction status
- confidence

### OutboundMessage

Stores every email, SMS, contact-form message or partner invite sent by Ship Hoppa.

Fields:

- recipient_type: importer, supplier, courier, broker, warehouse, forwarder, admin
- recipient_id
- channel: email, sms, wechat, contact_form
- provider: resend, twilio, manual, other
- provider_message_id
- template_key
- template_version
- campaign_id
- subject
- body_snapshot
- status: queued, sent, delivered, opened, clicked, replied, bounced, complained, failed, opted_out
- failure_code
- sentinel_error_code
- compliance_basis
- suppression_checked_at
- sent_at
- delivered_at
- replied_at
- opt_out_at
- related_supplier_lead_id
- related_shipment_id

### ExtractedFact

Stores facts pulled from emails, PDFs and spreadsheets.

Fields:

- source_message_id
- shipment_id
- fact_type: ETD, ETA, invoice_total, invoice_currency, invoice_due_date, HS_code, supplier_address, supplier_bank_details, cargo_volume, duty_amount
- value
- confidence
- needs_review
- accepted_by

### AutomationRun

Stores every automation attempt.

Fields:

- automation_type: match_message, extract_document, chase_partner, generate_approval, update_eta, invoice_reconcile, bank_details_check, supplier_pay_quote, delivery_prepare, space_detect
- input_reference
- output_reference
- confidence
- decision: auto_accepted, customer_approval_required, admin_review_required, failed
- reason
- created_tasks
- created_approvals
- audit_event_id

### AutomationRule

Stores company or system rules that allow the product to get smarter without hard-coding every workflow.

Fields:

- organization_id
- rule_type: auto_accept_fact, auto_chase_partner, payment_approval_limit, delivery_preference, customs_review_required, spare_space_threshold
- conditions
- action
- risk_level
- active

Examples:

- auto-accept ETA updates from a trusted forwarder when the shipment reference matches;
- auto-request supplier photos 72 hours before goods-ready date;
- require finance approval for any payment over a set amount;
- auto-prepare courier delivery for cartons under a set size;
- always admin-review biosecurity risk flags.

### MissingDataRequest

Represents a specific piece of information the system needs from a person or partner.

Fields:

- shipment_id
- requested_from_role
- requested_from_contact
- field_needed
- plain_language_question
- due_at
- status
- reminder_count
- source_message_id

The user should not have to work out what is missing. The system should ask the right party directly.

### ApprovalRequest

The customer-facing action queue.

Types:

- approve_payment
- approve_supplier_payment
- approve_trucking
- accept_sailing_change
- approve_customs_submission
- approve_spare_space_listing
- approve_release
- approve_invoice_variance

### PartnerProfile

Represents suppliers, couriers, brokers, forwarders, warehouses and destination agents.

Fields:

- partner_type
- contact details
- organization relationship
- upload permissions
- preferred communication method

### PartnerCapability

Stores what a partner can do and how reliable they are.

Fields:

- partner_id
- capability_type: supplier_production, origin_pickup, inspection, warehouse_receipt, customs_brokerage, port_drayage, local_delivery, freight_forwarding, payment_support
- service_regions
- service_lanes
- equipment
- cutoff_rules
- operating_hours
- escalation_contacts
- average_response_hours
- average_completion_hours
- failure_rate
- cost_model
- active

### ContingencyOption

Stores a better option, backup plan or exception recovery path.

Fields:

- shipment_id
- issue_type: production_delay, cutoff_miss, sailing_change, eta_slip, customs_hold, biosecurity_risk, payment_delay, release_block, trucking_risk, spare_space_opportunity
- option_type: approve_change, book_next_sailing, change_trucker, request_partner_update, pay_charge, split_shipment, hold_for_review
- plain_language_summary
- cost_impact
- time_impact_days
- risk_level
- source_evidence
- approval_request_id
- status: proposed, approved, rejected, expired, applied

### SEOOpportunity

Represents a supplier/importer acquisition opportunity found by the SEO Engine.

Fields:

- target_country: australia, united_states, china
- audience: supplier, importer, fcl_owner, mcl_buyer, partner
- category
- city
- lane
- keyword_cluster
- search_intent
- source: seo_engine, ai_citation, competitor_gap, supplier_discovery, admin_seed, partner_signal
- opportunity_score
- page_type: supplier_landing, lane_page, category_page, city_page, knowledge_article, comparison_page
- cms_page_id
- status: discovered, brief_ready, page_drafted, published, monitoring, paused, rejected
- related_supplier_discovery_run_id
- created_at
- updated_at

SEO opportunities should become either inbound pages, outbound discovery runs or both.

### SupplierDiscoveryRun

Represents an automated supplier-finding job driven by SEO, admin seed data or growth feedback.

Fields:

- seo_opportunity_id
- target_country
- target_city
- product_category
- lane
- source_set: supplier_websites, directories, trade_show, partner_referrals, marketplace_api, admin_seed, mixed
- query_terms
- source_rules
- run_status: queued, running, completed, paused, failed, blocked
- leads_found
- leads_enriched
- leads_rejected
- leads_approved_for_contact
- compliance_review_required
- sentinel_error_code
- started_at
- completed_at

Discovery runs should be repeatable and auditable. Every lead they create must store the source URL and contact basis.

### SupplierLead

Represents a potential supplier account before it becomes a partner or supplier workspace.

Fields:

- company_name
- country
- city
- product_categories
- discovery_source: alibaba, made_in_china, global_sources, trade_show, supplier_website, partner_referral, importer_invite, supplier_referral, other
- discovery_source_url
- platform_profile_url
- company_website
- public_contact_source_url
- public_contact_captured_at
- public_email
- public_phone
- public_wechat
- preferred_language
- exports_to_regions
- overseas_buyer_signals
- bulky_goods_fit
- lead_score
- fit_reason
- compliance_basis
- contact_method_allowed: email, sms, wechat, contact_form, phone, none
- outreach_status: discovered, enriched, scored, needs_human_review, approved_for_contact, contacted, replied, onboarded, referred_importer, do_not_contact, rejected
- last_contacted_at
- next_follow_up_at
- opt_out_at
- do_not_contact
- assigned_owner
- notes

Supplier lead safeguards:

- every contact method requires a source URL or referral source;
- every first outreach requires human approval until the channel and template are proven;
- duplicate and suppression checks run before any message;
- opt-out suppresses all future outreach across every channel;
- conversion attribution links supplier leads to supplier workspaces, invited importers and shipments.

### SupplierVerification

Tracks supplier trust and risk before unlocking sensitive automation.

Fields:

- supplier_id
- supplier_lead_id
- verification_status: unverified, basic_checked, verified, restricted, rejected
- website_domain_match
- public_address_match
- export_capability_score
- duplicate_profile_score
- bank_detail_risk
- complaint_count
- restricted_reason
- verified_by
- verified_at
- next_review_at

Verification should be automated where possible but reviewable by admins.

### SupplierProfileClaim

Tracks supplier ownership of a draft profile.

Fields:

- supplier_lead_id
- supplier_workspace_id
- claim_token
- claim_status: draft_created, invited, claimed, corrected, rejected, expired
- invited_contact_method
- invited_at
- claimed_at
- corrected_fields
- approved_public_fields

Draft supplier profiles must remain private until claimed or explicitly approved.

### GrowthAttributionEvent

Tracks the growth loop from source to revenue.

Fields:

- event_type: lead_discovered, lead_enriched, lead_contacted, lead_replied, supplier_signed_up, buyer_invited, importer_claimed, shipment_created, invoice_issued, revenue_recognised, opt_out, complaint
- supplier_lead_id
- supplier_workspace_id
- importer_organization_id
- shipment_id
- campaign_id
- source
- channel
- template_key
- category
- region
- value_usd
- occurred_at

Growth attribution should feed the supplier scoring model and SEO/content priorities.

### SupplierWorkspace

Represents the optional free supplier-side experience.

Fields:

- supplier_id
- company_name
- country
- city
- contact_people
- export_capability
- default pickup_address
- default packing_contact
- default invoice_currency
- default bank_detail_profile
- product_categories
- overseas_customer_links
- importer_invite_links
- referral_source_supplier_id
- invited_importers_count
- converted_importers_count
- attributed_shipments_count
- active_purchase_orders
- completed_shipments
- performance_metrics
- claimed_account
- free_plan_status

Supplier workspace capabilities:

- confirm order details;
- confirm production milestones;
- upload pro forma invoices and commercial invoices;
- upload packing lists;
- upload product photos and QC photos;
- confirm goods-ready dates;
- confirm pickup address and warehouse hours;
- share bank details safely;
- see what the overseas buyer still needs from them;
- receive a professional buyer-facing order/shipping status page.
- invite overseas buyers into Ship Hoppa with prefilled order and shipping details.
- track buyer invite status at a high level without seeing buyer-private commercial data.

Supplier workspace restrictions:

- supplier cannot see importer landed cost;
- supplier cannot see Ship Hoppa platform/service fees;
- supplier cannot see other importers or other suppliers;
- supplier cannot see FCL owner commercial details;
- supplier cannot alter buyer-approved payment amounts without review.

### DeliveryJob

Represents local trucking, courier freight, pallet freight or FCL drayage.

Fields:

- shipment_id
- mode: courier, pallet_freight, local_truck, port_drayage, live_unload, warehouse_delivery
- pickup location
- delivery location
- required equipment
- delivery window
- quote
- booking status
- proof of delivery

### IntegrationConnection

Stores connected systems and their health.

Fields:

- organization_id
- provider: outlook, gmail, xero, quickbooks, myob, shopify, woocommerce, inventory_system, wise, ofx, resend, twilio, carrier_api, visibility_provider, customs_broker, other
- connection_status: not_connected, pending, connected, degraded, revoked, failed
- scopes
- last_sync_at
- last_success_at
- last_error_code
- health_status
- owner_user_id
- external_account_reference

### SupplierPayRequest

Represents a customer-approved payment to an overseas supplier.

This is not stock finance. The importer funds and approves the payment. Ship Hoppa automates the workflow around invoice capture, FX quote, supplier verification, approval and shipment cost tracking.

Fields:

- shipment_id
- supplier_id
- source_message_id
- source_document_id
- invoice_reference
- invoice_amount
- invoice_currency
- due_date
- beneficiary_name
- beneficiary_bank_details
- bank_details_changed
- fraud_review_status
- fx_provider: wise, ofx, manual, other
- fx_quote_id
- fx_rate
- provider_fee
- estimated_local_currency_cost
- estimated_arrival_date
- approval_request_id
- payment_status
- provider_reference

### FXQuote

Stores payment-provider quote data for supplier payments.

Fields:

- supplier_pay_request_id
- provider
- provider_mode: live, sandbox, manual
- source_currency
- target_currency
- source_amount
- target_amount
- rate
- fee
- funding_fee
- recipient_fee
- total_estimated_cost
- comparison_rank
- recommended
- recommendation_reason
- expires_at
- estimated_delivery
- provider_quote_reference

### PaymentProof

Stores evidence for payments made outside Ship Hoppa.

Fields:

- shipment_id
- invoice_id
- supplier_pay_request_id
- payment_type: supplier_invoice, freight_invoice, duty_gst, customs_brokerage, destination_delivery, other
- paid_amount
- paid_currency
- paid_at
- paid_by
- payment_method: bank_transfer, card, wise, ofx, other
- reference_number
- proof_document_id
- bank_account_last_digits
- reconciliation_status: pending_review, matched, variance, rejected
- variance_amount
- reviewed_by
- reviewed_at
- notes

Outside-app payment should be friction-free. If an authorized user says they paid, the app should accept that statement by default, update the shipment and keep a clear audit trail.

Proof upload is optional unless a risk rule requires it.

Require or request proof only when:

- payment amount is high;
- supplier bank details recently changed;
- payment affects freight release;
- there is a duplicate-payment risk;
- the invoice amount, currency or supplier does not match known shipment data;
- finance/admin rules require evidence;
- there is a dispute, claim or audit request.

### LandedCostActual

Stores the final actual cost of a shipment and variance from estimate.

Fields:

- shipment_id
- estimated_total
- actual_total
- currency
- supplier_invoice_amount
- fx_cost
- international_freight
- platform_fee
- origin_pickup
- inspection
- warehouse_charges
- customs_duty
- gst
- broker_fees
- port_charges
- destination_trucking
- insurance
- storage_demurrage_detention
- adjustments
- variance_amount
- variance_reason
- finalised_at

### InsurancePolicy

Stores cargo insurance details.

Fields:

- shipment_id
- insurance_required
- waived_by
- insured_value
- currency
- provider
- policy_reference
- premium
- coverage_notes
- document_id

### ClaimRecord

Stores damage, loss or delay claims.

Fields:

- shipment_id
- insurance_policy_id
- claim_type: damage, loss, shortage, delay, other
- claim_status: draft, submitted, under_review, approved, rejected, paid, closed
- claim_amount
- evidence_document_ids
- photo_document_ids
- survey_report_document_id
- submitted_at
- resolved_at
- recovery_amount

### SpaceOpportunity

Represents MCL or FCL space logic.

Fields:

- shipment_id
- opportunity_type: buy_shared_space, sell_spare_fcl_space
- available_cbm
- cargo compatibility
- cutoff feasibility
- estimated saving or recovery
- approval status

## Plan Of Attack

Build the backbone first, then attach every product surface to it. Do not build isolated feature tabs that later need to be reconnected.

### 1. Platform Backbone

Create the durable operating system layer:

- Railway backend, workers and Postgres;
- Systematicly-style saved import projects;
- project step data, files, collaborators, versions and snapshots;
- shipment, organization, source message, approval, task and audit models;
- file storage with Railway primary storage and R2 append-only archive backup;
- provider adapter contracts for email, payments, customs, carrier data, CMS/SEO and accounting;
- Sentinel error codes, health checks and admin automation queue.

This is the foundation everything else plugs into.

### 2. Convert The Current App Into Modules

Move the existing booking, cutoff, sailing, matching, documents, tracking, invoices, customs and admin work into the new shipment/project backbone.

The current MCL booking product becomes:

- `Space -> Find shared MCL space`;
- powered by existing cargo and supplier data;
- no repeated data entry;
- same cutoff/matching engine;
- same invoice, document, tracking and approval systems.

FCL spare-space recovery becomes a second space module, not a separate app.

### 3. Build The Friction-Free Intake Loop

Make the first user experience simple:

- forward an email;
- upload a supplier invoice or packing list;
- invite a supplier;
- create a supplier order page;
- or start from an existing MCL/FCL shipment.

The system should create or update the `ImportProject`, extract facts, match documents, identify missing data and show the next approval.

### 4. Build The Shipment Workspace

Create the main customer workspace:

- Today;
- Imports;
- Inbox;
- Approvals;
- Money;
- Space;
- Company.

Each shipment should show production, journey, documents, money, customs, delivery, messages and space opportunities in one coherent workspace.

### 5. Add Partner Portals And Automation

Let suppliers, couriers, warehouses, brokers and accountants contribute directly without seeing data they should not see.

Automate reminders, missing-data requests, document chasing, pickup readiness, payment approvals, customs handoff and delivery preparation.

### 6. Add Money, Customs And Delivery Depth

Build the final-product finance and logistics workflows:

- Supplier Pay with live quote comparison;
- mark-as-paid outside Ship Hoppa;
- invoice reconciliation;
- duty/GST/VAT estimates from official source connectors;
- broker review where needed;
- release holds;
- destination trucking and proof of delivery.

### 7. Add Growth Automation

Wire SEO Engine, CMS, supplier discovery, outreach and attribution into the same platform backbone.

The growth engine should create:

- SEO opportunities;
- supplier discovery runs;
- supplier leads;
- private draft supplier profiles;
- free supplier workspaces;
- importer invite links;
- revenue attribution.

The system starts review-first and graduates proven categories/templates/sources into guarded autopilot.

### 8. Harden, Test And Scale

Before production scale:

- end-to-end tests for order to delivery;
- provider failure tests;
- Sentinel alert tests;
- permission and data-isolation tests;
- file backup and restore checks;
- payment and supplier bank-detail risk checks;
- customs estimate and broker-review checks;
- growth automation suppression, opt-out and deliverability checks.

The test standard is not "page loads". The standard is: an import can be created, saved, resumed, paid, shipped, tracked, cleared, delivered, audited and cloned.

## Build Phases

### Phase -2: Launchpad Platform Wiring

Goal: turn Ship Hoppa into a serious platform by wiring in Launchpad infrastructure before scaling acquisition and automation.

Backend:

- Add Launchpad-style module registry or adapter map for Ship Hoppa modules.
- Add Sentinel error-code registry with `SH-` codes.
- Add program health endpoints for app, queues, providers, crons and data freshness.
- Add saved import project storage:
  - `ImportProject`;
  - `ImportProjectStepData`;
  - `ImportProjectVersion`;
  - `ImportProjectSnapshot`;
  - `ImportProjectCollaborator`;
  - `ImportProjectFile`;
  - `ImportProjectEvent`.
- Add `OutboundMessage`.
- Add `SEOOpportunity`.
- Add `SupplierDiscoveryRun`.
- Add `SupplierVerification`.
- Add `SupplierProfileClaim`.
- Add `GrowthAttributionEvent`.
- Add adapter contracts for:
  - Email Manager -> SourceMessage, OutboundMessage, AdminTask;
  - KS -> cited shipping/customs/supplier knowledge;
  - Consensus -> high-risk decision review;
  - Finance -> invoice, payment, Supplier Pay and reconciliation;
  - CMS/SEO -> landing page inventory, keyword opportunities and supplier discovery segments;
  - CRM/referrals -> supplier/importer timelines and attribution.

Frontend:

- Base `/admin` on the Launchpad admin shell pattern.
- Add Program Health to admin.
- Add Supplier Discovery and Growth views.
- Add SEO Opportunity and Discovery Run views.
- Add saved import projects list, resume, archive and "create similar import".
- Keep customer-facing Ship Hoppa UI separate from Launchpad program controls.

Automation:

- Wire Resend for email delivery and webhooks.
- Wire Twilio for SMS, inbound STOP handling and Sentinel alerts.
- Wire Email Manager initially in review-first mode.
- Wire KS for retrieval and cited operational answers.
- Wire Consensus for high-risk review only.
- Wire SEO Engine to supplier discovery in review-first mode, then guarded autopilot for proven source/template/category combinations.

Success criteria:

- Admin can see Ship Hoppa module health in one place.
- Import projects can be saved, resumed, versioned, archived and cloned.
- SEO opportunities can create CMS briefs, supplier discovery runs, supplier leads and growth attribution events.
- Sentinel creates admin tasks for operational errors.
- Resend/Twilio outbound messages are tracked and suppressible.
- Supplier leads have verification, claim and attribution records.
- Launchpad assets are connected through adapters without leaking healthcare-specific logic into Ship Hoppa.

### Phase -1: Supplier-Agnostic Production Control

Goal: take over immediately after product purchase terms are agreed, without forcing the buyer or supplier to change behaviour.

This phase must work whether the buyer used Alibaba or not.

Ship Hoppa should support these intake paths:

1. **Forward supplier or marketplace emails**
   - Buyer forwards supplier emails, Alibaba emails, pro formas, invoices, order confirmations, Trade Assurance emails, payment requests or production updates to Ship Hoppa.
   - Lowest friction and works first.

2. **Upload order documents**
   - Buyer uploads purchase order, supplier invoice, pro forma invoice, Trade Assurance order, purchase contract, product specs or packing details.
   - Useful when email forwarding is incomplete.

3. **Supplier portal**
   - Buyer invites a supplier to confirm order terms, production dates, packaging, photos and ready dates directly.
   - Works for non-Alibaba suppliers and long-term supplier relationships.

4. **Marketplace wire-ins later**
   - Alibaba, 1688, Global Sources, Made-in-China or other marketplaces can be added as optional connectors.
   - Browser helpers or official APIs must respect platform terms and user authorization.
   - Do not rely on brittle scraping as a core business workflow.

Backend:

- Add `PurchaseOrder`.
- Add `MarketplaceOrder`.
- Add `ProductionMilestone`.
- Add `QualityInspection`.
- Extend `SourceMessage` matching to recognize supplier names, purchase order references, invoice references, marketplace order references, product URLs and Trade Assurance emails where present.
- Create a purchase order automatically from source messages, supplier emails, marketplace emails or uploads.
- Link purchase orders to shipments when goods are ready or shipping is being planned.

Frontend:

- Add purchase handoff inside **Imports** or **Today**:
  - "Forward your supplier order email";
  - "Upload PO / supplier invoice";
  - "Invite supplier to confirm production";
  - "Connect Alibaba order" as an optional marketplace path;
  - "Review extracted purchase terms";
  - "Track production";
  - "Prepare shipping".
- Show a plain-language order terms check:
  - product;
  - quantity;
  - price;
  - currency;
  - incoterm;
  - ready date;
  - payment terms;
  - quality terms;
  - marketplace/protection status when relevant.

Automation:

- Extract purchase terms from supplier emails, marketplace emails, POs, pro formas and supplier invoices.
- Create missing-data requests for supplier if specs, packaging, ready date or bank details are missing.
- Generate Supplier Pay requests for deposit or balance payments.
- Create QC milestone if order value, category or company rules require inspection.
- Trigger shipment planning before the goods-ready date.

Success criteria:

- User can forward a supplier order email and Ship Hoppa creates a purchase order.
- User can optionally wire in an Alibaba order without making Alibaba mandatory.
- User can see the production/payment/shipping path without re-entering details.
- Supplier can confirm ready date and upload packing details through a secure link.
- Shipment planning starts automatically before goods are ready.

### Phase -0.5: Free Supplier Workspace

Goal: make Ship Hoppa useful to suppliers even before the overseas buyer is deeply onboarded.

The supplier workspace should help Chinese suppliers and other origin suppliers manage overseas customer orders more professionally, without charging them.

Supplier value:

- fewer repetitive buyer questions;
- clearer production and payment milestones;
- easier packing list and invoice sharing;
- cleaner pickup and shipping coordination;
- professional order status page for overseas customers;
- easier handoff from production to logistics;
- better chance that overseas customers choose Ship Hoppa-supported shipping.
- a simple way to invite overseas buyers into a better post-order workflow.

Backend:

- Add `SupplierWorkspace`.
- Allow supplier profiles to be created from partner links, buyer invites or admin invites.
- Let suppliers reuse company, address, contact and bank-detail profiles across buyer orders.
- Add importer invite links generated from supplier orders.
- Add attribution for supplier-sourced importer signups, shipments and active accounts.
- Add permissions so suppliers only see their own tasks and buyer-approved order data.
- Track supplier responsiveness and data completeness.

Frontend:

- Create free supplier workspace:
  - active orders;
  - tasks due;
  - production milestones;
  - invoice and packing uploads;
  - pickup details;
  - buyer-facing status link.
  - invite buyer button.
  - buyer invite status.
- Keep it simple and multilingual-ready.
- Start with English, but design copy and labels so Chinese localization can be added cleanly.

Automation:

- When a buyer forwards a supplier order, infer supplier contact and send a secure invite.
- When a supplier creates or updates an overseas order, generate a buyer invite link with order details prefilled.
- When a buyer accepts a supplier invite, create/import the buyer workspace and link the order to their organization.
- If supplier claims the workspace, future orders can be prefilled.
- Automatically ask supplier for missing production, packing, photo, pickup or bank-detail data.

Success criteria:

- A supplier can use Ship Hoppa for free with no importer pricing visibility.
- Supplier can manage an overseas order from production through pickup readiness.
- Supplier can invite an overseas buyer into Ship Hoppa from that order.
- Buyer arrives in a prefilled import workspace rather than a blank signup flow.
- Buyer receives cleaner status updates without manually chasing the supplier.
- Ship Hoppa receives structured production and packing data earlier.
- Ship Hoppa can attribute importer activation back to the supplier.

### Phase 0: Prove The Friction-Free Loop

Goal: build the smallest end-to-end automation loop before expanding the whole platform.

This phase proves the product promise:

`Email or document in -> shipment created -> missing data detected -> partner chased -> approval generated -> shipment updated`

Backend:

- Add `Shipment` as a thin wrapper around existing bookings and operational data.
- Add `SourceMessage` for dev/manual inbound email simulation.
- Add simple extraction for shipment reference, supplier, origin, destination, ETA, invoice amount and cargo description.
- Add `MissingDataRequest`.
- Add `ApprovalRequest`.
- Add `AutomationRun` audit records.

Frontend:

- Add a **Today** page.
- Show:
  - active shipments;
  - approvals needed;
  - missing data being chased;
  - automation items needing review.
- Add a simple inbound-message demo flow for local testing.

Success criteria:

- A user can paste or upload one forwarded freight email.
- The app creates or updates a shipment.
- The app shows what it extracted and what is missing.
- The app generates one partner request and one approval card.

### Phase 1: Reframe The App Around Shipments

Goal: make the current app feel like shipping automation software, not only a booking tool.

Backend:

- Add `Shipment` model.
- Link every booking to a shipment.
- Add `GET /shipments`.
- Add `GET /shipments/{id}`.
- Add `GET /shipments/{id}/workspace` to return shipment, booking, container, documents, events, invoice, customs, release status and next approvals in one payload.
- Create shipments automatically when a booking is created.

Frontend:

- Make **Today** the default tab and **Imports** the main shipment list.
- Turn the current tracking view into a shipment detail page.
- Move the current booking flow into **Space -> Find shared MCL space**.
- Keep profile, docs, money, customs, sailings and tracking, but make them shipment-oriented.

Success criteria:

- A user logs in and sees shipments first.
- A shipment has ETA, current status, cost, documents, release blockers and next actions.
- The old booking flow still works, but it creates or links to a shipment.

### Phase 2: Build The Inbox Intake Layer

Goal: customers can forward existing freight emails and documents instead of manually entering everything.

Backend:

- Add `SourceMessage`, `SourceAttachment` and `ExtractedFact`.
- Add `POST /inbound/messages` for manual/dev ingestion.
- Add `POST /shipments/{id}/source-messages`.
- Add deduplication by message id, sender, subject and attachment hash.
- Store original documents with immutable `storage_key`.
- Add extraction statuses: received, parsed, matched, needs_review, accepted.

Frontend:

- Add **Inbox** tab.
- Show cards for each email or document:
  - received from
  - matched shipment
  - extracted facts
  - confidence
  - needs review
- Add admin review for unmatched messages.

Automation:

- v1 can use simple deterministic parsing and manual review.
- v2 can add document AI extraction for invoices, packing lists and booking confirmations.
- v3 can connect Outlook and Gmail.

Success criteria:

- A forwarded booking confirmation can create or update a shipment.
- A forwarded commercial invoice can attach to the shipment and propose goods value.
- An unmatched email appears in admin review instead of disappearing.

### Phase 3: Build The Approval Queue

Goal: customers approve important decisions instead of hunting through tabs.

Backend:

- Add `ApprovalRequest`.
- Generate approval requests from:
  - invoice ready to pay
  - duty/GST estimate ready
  - destination truck ready to book
  - better sailing found
  - customs details missing
  - release ready
  - spare FCL space detected
- Add endpoints:
  - `GET /approvals`
  - `POST /approvals/{id}/approve`
  - `POST /approvals/{id}/reject`
  - `POST /approvals/{id}/request-review`

Frontend:

- Add **Approvals** tab.
- Show each approval as a visual decision card:
  - what is being approved
  - amount or impact
  - due date
  - source documents
  - risk level
  - approve/reject buttons

Success criteria:

- User can approve a payment from one card.
- User can approve destination trucking from one card.
- User can accept or reject a better sailing option from one card.

### Phase 4: Partner Collaboration Without New Accounts

Goal: suppliers, couriers, brokers and warehouses feed data into Ship Hoppa directly.

Backend:

- Generalize `SupplierAccessLink` into `PartnerAccessLink`.
- Add partner roles:
  - supplier
  - courier
  - customs_broker
  - freight_forwarder
  - warehouse
  - destination_agent
- Add scoped permissions so partners only see what they need.
- Add endpoints:
  - `POST /partner-links`
  - `GET /partner/{token}`
  - `POST /partner/{token}/documents`
  - `POST /partner/{token}/status`
  - `POST /partner/{token}/invoice`

Frontend:

- Keep the supplier portal, but broaden it into a partner portal.
- Partner portal should be plain and task-based:
  - confirm ready date
  - upload invoice
  - upload packing list
  - upload photos
  - upload proof of delivery
  - update delivery status

Success criteria:

- A supplier can upload documents without an account.
- A courier can upload an invoice and proof of delivery without seeing importer pricing.
- A broker can upload a duty note and customs status update.

### Phase 5: Destination Trucking And Release Automation

Goal: local delivery from port, depot, warehouse or terminal becomes seamless.

Backend:

- Add `DeliveryJob`.
- Add delivery profile fields to `Organization`:
  - default delivery address
  - warehouse hours
  - dock access
  - forklift available
  - tail-lift required
  - contact person
  - delivery instructions
- Add delivery decision logic:
  - cartons -> courier
  - pallets -> pallet freight
  - larger freight -> local truck
  - FCL -> port drayage or live unload
  - complex -> admin review
- Link release checks to delivery jobs.
- Block delivery booking until release blockers are clear or waived.

Frontend:

- Add delivery details to shipment view.
- Add delivery approval card.
- Add delivery status to tracking map and timeline.

Success criteria:

- Customer only enters delivery details once.
- The system prepares the right delivery method.
- Freight is not released for delivery while customs, payment or document holds are active.

### Phase 6: MCL Space As A Module

Goal: keep the current shared-container booking flow, but make it a module powered by shipment data.

Backend:

- Keep current `Booking`, `Container`, cutoff engine and matching algorithm.
- Add `SpaceOpportunity` for `buy_shared_space`.
- Allow shipments to request shared space using known shipment data.
- Matching should use existing feasibility, cutoff, capacity and pricing logic.

Frontend:

- Rename the current booking journey to **MCL Space**.
- Pre-fill form fields from organization, shipment, supplier and extracted facts.
- Show "Find shared space" from a shipment detail page.

Success criteria:

- A shipment can become an MCL booking without re-entering supplier and cargo data.
- MCL result still shows best option plus alternatives.
- Existing tests for booking, cutoff and matching continue to pass.

### Phase 7: FCL Recovery As A Module

Goal: let FCL users recover unused container space without making them manage other importers.

Backend:

- Add `SpaceOpportunity` for `sell_spare_fcl_space`.
- Detect spare CBM from FCL shipment/container data.
- Add owner approval before listing any spare capacity.
- Use existing cargo compatibility and cutoff engine.
- Add payout records later, separate from importer invoices.

Frontend:

- Add "Recover unused space" action on FCL shipment pages.
- Show:
  - total container size
  - currently booked
  - protected buffer
  - recoverable CBM
  - estimated recovery
  - risk controls

Success criteria:

- FCL owner approves listing spare capacity.
- Added cargo cannot load if it fails cutoff or compatibility.
- Owner cargo remains priority.

### Phase 8: Payment, Duty And Landed Cost Automation

Goal: make the money tab a trusted finance workflow.

Supplier Pay is included in this phase. Stock finance is explicitly out of scope for now.

Supplier Pay means:

- customer-approved supplier invoice payments;
- payment tracking whether paid through Ship Hoppa or outside the app;
- invoice extraction from email or upload;
- supplier bank detail verification;
- FX quote comparison or provider quote retrieval;
- payment approval card;
- payment status sync into the shipment;
- landed-cost update after approval/payment.

Supplier Pay provider rule:

- do not hard-code one provider as "cheapest";
- retrieve live quotes for each payment where provider APIs allow it;
- compare total landed payment cost, including FX rate, provider fee, funding fee, receiving fee where known, estimated arrival date and compliance/KYC requirements;
- recommend the cheapest acceptable option first;
- offer both providers when Wise and OFX are both competitive or when one is better for speed and the other is better for larger/relationship-priced transfers;
- keep outside-app mark-as-paid for customers who still pay by bank transfer, Wise, OFX, Alibaba, broker, bank or another method.

Wise should be treated as the first API-shaped provider because it has public API documentation and transparent quote/fee concepts. OFX should remain in the provider set because it may be competitive for business, volume, AP automation, account management and larger transfers. The final decision for each payment should come from live quote comparison, not a static preference.

Supplier Pay does not mean:

- Ship Hoppa pays for stock before the importer funds it;
- credit underwriting;
- repayment schedules;
- inventory finance;
- lending against goods;
- taking supplier-payment credit risk.

Backend:

- Add normalized cost lines:
  - freight
  - platform/service fee
  - pickup
  - destination trucking
  - customs brokerage
  - duty
  - GST
  - port charges
  - warehouse charges
  - adjustments
- Add invoice reconciliation:
  - expected amount
  - actual amount
  - variance
  - source document
  - needs approval
- Add `SupplierPayRequest`.
- Add `FXQuote`.
- Add `PaymentProof`.
- Add supplier bank-detail history and bank-detail-change warnings.
- Add supplier payment approval requests.
- Add mark-as-paid flow for payments made outside Ship Hoppa.
- Add optional proof-of-payment upload and reconciliation states.
- Allow authorized users to mark paid without proof unless a risk rule requires evidence.
- Support partial payments, overpayments, underpayments and currency variance.
- Add payment approval queue.
- Add production-shaped provider adapters for Wise, OFX, manual bank transfer and future licensed providers.
- Add quote comparison and quote-expiry handling from the first implementation.
- Add provider sandbox/manual fallback behind the same adapter interface when live credentials are not ready.

Frontend:

- Keep invoice layout with fee types left and prices right.
- Add status labels:
  - estimated
  - confirmed
  - invoice received
  - approved
  - paid
- Add plain-language explanations for duty, GST, customs and biosecurity.
- Add Supplier Pay approval cards:
  - supplier invoice amount;
  - supplier currency;
  - estimated local currency cost;
  - FX rate;
  - provider fee;
  - estimated arrival date;
  - bank-detail-change warning;
  - source invoice;
  - approve, reject or ask Ship Hoppa.
- Add "Mark as paid outside Ship Hoppa" option:
  - paid amount;
  - paid currency;
  - payment date;
  - payment method;
  - reference number;
  - optional proof upload;
  - notes.
- If proof is not required, the fastest path should be: amount, date, method, mark paid.
- Show reconciliation state:
  - pending review;
  - matched;
  - variance;
  - rejected.

Success criteria:

- User can see total landed cost by shipment.
- User can approve payment without digging through documents.
- Payment status controls release status.
- User can approve a supplier payment from one card.
- User can mark a supplier invoice as paid outside the app without being forced to upload proof.
- User can optionally upload proof for their own records.
- Supplier payment updates shipment landed cost and audit trail.
- Any changed supplier bank details are flagged before approval.
- Outside-app payments marked by an authorized user can clear payment holds unless a risk rule requires review or proof.

### Phase 9: External Integrations

Goal: replace manual data entry with real source-of-truth integrations over time.

Integration order:

1. Email forwarding address.
2. Manual/admin upload and extraction review.
3. Supplier purchase-order, invoice and production-control intake.
4. Microsoft 365/Outlook/Exchange connected inbox.
5. Google Workspace/Gmail connected inbox.
6. IMAP/forwarding support for other major providers where safe.
7. Railway primary backend, worker and Postgres setup.
8. Systematicly-style file storage adapter: Railway Postgres primary, local cache optional, R2 append-only archive.
9. Railway Postgres database migrations and repositories.
10. Stripe or payment provider.
11. Wise, OFX or another licensed FX/payment provider for Supplier Pay, through live quote comparison where available.
12. Optional marketplace connectors such as Alibaba official API/partnership access if available and approved.
13. Carrier/forwarder schedules and cutoffs.
14. Track and trace provider.
15. Courier/trucking quote and booking providers.
16. Accounting integrations such as Xero or QuickBooks.

Do not build temporary workflows that must be thrown away later. Build the final workflow shape first, with provider adapters that can run in live, sandbox or manual mode depending on credential and compliance readiness.

Stock finance and pay-for-stock credit products are not part of this integration phase.

## Technical Architecture Plan

### Backend

Current FastAPI backend can stay.

Needed upgrades:

- Move from in-memory `Store` to database-backed repositories.
- Add database migrations.
- Add background jobs for email parsing, reminders, extraction and status refresh.
- Add file storage provider abstraction.
- Add event log as first-class source of truth.
- Add tenant scoping by organization.
- Add role-based access control.

### Frontend

Current React/Vite frontend can stay for now.

Needed upgrades:

- Reframe default navigation around Today, shipments and approvals.
- Create reusable shipment workspace components.
- Keep full functionality, but place it in the correct workspace instead of one giant mixed tab.
- Support both simple default views and full-detail drilldowns.
- Keep workflows visual:
  - shipment cards
  - approval cards
  - route maps
  - invoice sheets
  - document step cards
  - capacity ledgers
  - partner request cards
  - automation review cards

### Automation Layer

Add an internal automation service with these functions:

- match source messages to shipments
- extract shipment facts
- generate missing-data tasks
- generate approval requests
- chase partners
- calculate duties, GST and landed cost
- detect delivery needs
- detect MCL/FCL space opportunities
- detect better sailing options
- create audit events for every automation decision

### Health Checks And Monitoring

Health checks and operational monitors should use Sentinel.

Sentinel should watch:

- inbound messages not processed;
- extraction jobs stuck or failing;
- low-confidence extraction rate;
- unmatched source messages;
- partner requests ignored past deadline;
- approval requests overdue;
- payment approvals stuck;
- Supplier Pay quote expired before approval;
- outside-app payment proof awaiting review when proof was required by rule;
- outside-app payment amount/currency variance;
- supplier bank details changed;
- customs or release holds stale;
- ETA not verified recently;
- delivery job not booked before release window;
- route or sailing data stale;
- failed background jobs;
- API availability and latency.

Sentinel alerts should create admin automation queue items, not just technical alerts. The operator should see what needs to happen next.

### Sentinel Error Code Registry

Mirror the Launchpad Sentinel pattern, but use a Ship Hoppa-specific prefix.

Format:

`SH-XYYY`

- `SH` = Ship Hoppa
- `X` = domain
- `YYY` = category + specific error

Severity:

- `P0`: critical money, release, data, security or production outage
- `P1`: urgent operational failure that blocks shipments or customer trust
- `P2`: important issue that needs review but has a workaround
- `P3`: informational or low-risk issue

Each error definition should include:

- code
- category
- severity
- user_safe_message
- internal_message
- retryable
- creates_admin_task
- sends_sms_alert
- runbook_url

Error-code domains:

- `SH-1xxx`: customer, supplier and partner access
- `SH-2xxx`: shipments, bookings, cutoffs, matching and space opportunities
- `SH-3xxx`: system, database, cron, extraction, email and SMS
- `SH-4xxx`: external integrations
- `SH-5xxx`: supplier discovery, outreach, compliance and growth automation
- `SH-6xxx`: payments, Supplier Pay, FX, invoices and release holds
- `SH-7xxx`: customs, duties, GST, biosecurity and landed cost
- `SH-8xxx`: tracking, sailing data, maps, ETA and route rendering

Initial registry:

- `SH-3101`: database connection failed, P0, retryable
- `SH-3201`: background job failed, P1, retryable
- `SH-3202`: cron missed scheduled run, P1, not retryable
- `SH-3301`: source message extraction failed, P1, retryable
- `SH-3302`: low-confidence extraction spike, P2, not retryable
- `SH-3401`: Resend API error, P1, retryable
- `SH-3402`: Resend rate limited, P2, retryable
- `SH-3403`: Resend domain not configured, P0, not retryable
- `SH-3501`: Twilio API error, P1, retryable
- `SH-3502`: Twilio not configured, P2, not retryable
- `SH-3503`: Twilio webhook verification failed, P1, not retryable
- `SH-4101`: carrier or forwarder schedule sync failed, P1, retryable
- `SH-4102`: visibility provider ETA sync failed, P2, retryable
- `SH-4201`: Wise/OFX quote failed, P1, retryable
- `SH-4202`: FX quote expired before approval, P2, not retryable
- `SH-5101`: supplier discovery source blocked or unavailable, P2, retryable
- `SH-5102`: supplier lead enrichment failed, P2, retryable
- `SH-5103`: outreach suppression check failed, P0, not retryable
- `SH-5104`: opt-out processing failed, P0, retryable
- `SH-5105`: spam complaint received, P1, not retryable
- `SH-5106`: outbound campaign exceeded daily limit, P1, not retryable
- `SH-6101`: supplier bank details changed, P0, not retryable
- `SH-6102`: payment approval stuck, P1, not retryable
- `SH-6103`: invoice/release mismatch, P0, not retryable
- `SH-7101`: customs estimate failed, P2, retryable
- `SH-7102`: biosecurity flag requires review, P1, not retryable
- `SH-8101`: route rendering failed, P2, retryable
- `SH-8102`: ETA stale past threshold, P2, retryable
- `SH-8103`: map label or route validation failed, P3, retryable

Sentinel implementation pattern:

- use one `createReporter(SH_ERROR_CODES)` helper;
- log structured JSON for Railway/Vercel log drains;
- tag errors with `sentinel.error_code`, `sentinel.category`, `sentinel.severity` and `sentinel.retryable`;
- send Twilio SMS alerts for P0/P1 only;
- dedupe SMS alerts per error code with a cooldown, default 10 minutes;
- create an Admin Task for operational errors, not just a developer alert;
- never send sensitive importer, supplier, cargo value, bank or personal data in SMS/log context;
- log IDs, provider references and last-four phone/bank fragments only where useful.

## Minimum Lovable Product

The first strong version should do this:

1. Customer forwards one shipment email or uploads one document.
2. Ship Hoppa creates a shipment record.
3. The system extracts supplier, cargo, origin, destination, ETA and invoice values.
4. Missing fields become plain-language tasks.
5. The system identifies the right supplier, courier, broker or warehouse contact from the email where possible.
6. The right partner gets a secure upload link or request.
7. Customer sees one shipment card with status, ETA, documents, money, delivery and next action.
8. Customer can approve a payment or delivery job.
9. Customer can approve a Supplier Pay request when a supplier invoice is matched.
10. If the shipment is small, the app offers MCL shared space.
11. If the shipment is FCL with spare room, the app offers FCL recovery.
12. Admin sees only exceptions the system could not safely resolve.
13. Sentinel raises automation queue items when processing, partner, payment, ETA or release health checks fail.

## Immediate Implementation Order

1. Add `Shipment`, `Organization`, `SourceMessage`, `MissingDataRequest`, `ApprovalRequest` and `AutomationRun` as the minimum automation spine.
2. Add `PurchaseOrder`, optional `MarketplaceOrder`, `ProductionMilestone` and `QualityInspection` for supplier-agnostic production control.
3. Add `SupplierWorkspace` and supplier-generated importer invite links.
4. Create shipments automatically from existing bookings so the current MCL flow remains usable.
5. Add `GET /shipments/{id}/workspace` so the UI can load the full shipment context in one request.
6. Add customer **Today** view as the default command centre.
7. Add purchase/shipment workspace cards for production, journey, documents, money, customs, delivery, messages and space options.
8. Move current booking flow into **Space -> Find shared MCL space** with prefilled shipment data.
9. Add manual/dev inbound message upload so email-first supplier and marketplace behaviour can be tested before live inbox integration.
10. Add extraction and matching review in admin **Automation Queue**.
11. Add approval cards for supplier payment, trucking, sailing change and spare-space listing.
12. Add Supplier Pay request, FX quote comparison and outside-app mark-as-paid models with live/sandbox/manual provider modes.
13. Generalize supplier portal into partner portal.
14. Add `DeliveryJob` and destination trucking approval.
15. Add `SpaceOpportunity` for MCL and FCL modules.
16. Add automation rules for auto-accept, customer approval and admin review.
17. Add Sentinel health checks and automation queue alerts.
18. Move storage/database off in-memory state before production use; no production workflow should depend on volatile prototype storage.
19. Add `SEOOpportunity`, `SupplierDiscoveryRun`, `SupplierLead`, `OutboundMessage` and `GrowthAttributionEvent` so acquisition automation has the same project-grade backbone as shipments.
20. Connect SEO Engine to CMS briefs, supplier discovery segments, compliant outreach, free supplier workspaces and importer-invite attribution.

## Non-Negotiables

- Production-grade architecture from the first build; staged delivery is fine, throwaway workflows are not.
- Email-first onboarding.
- Supplier-agnostic production control.
- Free supplier workspace as an importer acquisition channel.
- SEO Engine must feed supplier discovery, supplier landing pages and growth attribution, not only passive content reports.
- Alibaba and other marketplaces are optional wire-ins, not mandatory workflows.
- One shipment record as the source of truth.
- Full operating depth remains available.
- Simple default experience, complete detail on drilldown.
- Partners can contribute without full accounts.
- Ship Hoppa chases missing information automatically.
- Customer sees approvals, not admin clutter.
- Every automation decision is auditable.
- Payments and legal/compliance actions require approval until rules are proven.
- Supplier Pay only for now; no stock finance or pay-for-stock credit product.
- Supplier Pay should compare live provider quotes and recommend the lowest acceptable total cost.
- Supplier bank-detail changes are always flagged before payment approval.
- Customs, duty, GST/VAT and biosecurity calculations should prefer official government sources, with broker/admin review where certainty is not high enough.
- MCL and FCL recovery are product modules, not separate apps.
- Sentinel is the health-check and automation-monitoring layer.
- The system should always reduce work for the importer.
- Growth automation should minimise human work while respecting source permissions, opt-outs, suppression lists, deliverability health and compliance limits.
