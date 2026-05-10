export type CargoCategory =
  | 'tiles_stone'
  | 'furniture'
  | 'homewares'
  | 'bathroom_fittings'
  | 'lighting'
  | 'hardware'
  | 'garden'
  | 'automotive'
  | 'other'

export type ServiceLevel = 'standard' | 'express'

export type DeliveryMode = 'ship_hoppa_pickup' | 'self_delivery'

export type DeliveryPlanMethod = 'ship_hoppa_trucker' | 'importer_trucker' | 'warehouse_pickup'

export type DeliveryPlanStatus = 'blocked_by_release' | 'ready_to_book' | 'booked' | 'delivered'

export type AccountIntegrationProvider = 'alibaba' | 'email_inbox' | 'accounting' | 'supplier_pay' | 'object_storage'

export type AccountIntegrationStatus = 'not_connected' | 'connected' | 'needs_attention' | 'coming_soon'

export type FeasibilityStatus = 'feasible' | 'tight' | 'misses_cutoff' | 'admin_review'

export type SourceType =
  | 'manual_admin'
  | 'forwarder_confirmation'
  | 'carrier_api'
  | 'visibility_provider'
  | 'warehouse_event'

export type SourceConfidence = 'estimated' | 'verified' | 'confirmed'

export interface RouteWaypoint {
  lat: number
  lng: number
}

export type DocumentType =
  | 'commercial_invoice'
  | 'packing_list'
  | 'supplier_photos'
  | 'product_specs'
  | 'fumigation_ispm'
  | 'shipping_instructions'
  | 'house_bill'
  | 'arrival_notice'
  | 'delivery_order'

export type DocumentStatus = 'required' | 'uploaded' | 'approved' | 'rejected' | 'waived'

export type ChecklistStatus = 'incomplete' | 'in_review' | 'complete'

export type ShipmentEventStage =
  | 'booking_submitted'
  | 'booking_confirmed'
  | 'pickup_scheduled'
  | 'picked_up'
  | 'warehouse_received'
  | 'measured'
  | 'variance_approved'
  | 'loaded'
  | 'container_committed'
  | 'departed'
  | 'transshipped'
  | 'arrived'
  | 'customs_cleared'
  | 'freight_released'
  | 'delivered'

export type SourceMessageType = 'forwarded_email' | 'connected_inbox' | 'supplier_portal' | 'courier_portal' | 'broker_portal' | 'admin_upload'

export type ExtractionStatus = 'pending' | 'matched' | 'needs_review' | 'failed'

export type PaymentStatus = 'not_invoiced' | 'issued' | 'part_paid' | 'paid' | 'overdue' | 'void'

export type ReleaseStatus = 'blocked' | 'ready' | 'released'

export type ReleaseHoldStatus = 'active' | 'cleared' | 'waived'

export type ReleaseHoldType =
  | 'unpaid_invoice'
  | 'missing_documents'
  | 'customs_hold'
  | 'warehouse_variance'
  | 'admin_hold'

export type CustomsStatus = 'documents_required' | 'submitted' | 'queried' | 'cleared' | 'held'

export type CustomsBrokerPreference = 'ship_hoppa_broker' | 'importer_broker' | 'undecided'

export type ProductionMilestoneStatus = 'pending' | 'in_progress' | 'complete' | 'blocked' | 'waived'

export type SupplierPayRequestStatus =
  | 'draft'
  | 'quote_ready'
  | 'approval_required'
  | 'approved'
  | 'rejected'
  | 'marked_paid_outside_app'
  | 'paid'
  | 'cancelled'

export type ContainerStatus =
  | 'open'
  | 'filling'
  | 'committed'
  | 'loading'
  | 'shipped'
  | 'arrived'
  | 'unpacked'

export interface Coordinates {
  lat: number
  lng: number
}

export interface Lane {
  id: string
  name: string
  origin_region: string
  destination_region: string
  destination_port: string
  container_type: string
  practical_cbm_limit: number
  road_weight_limit_kg: number
  max_shippers_per_container: number
  base_container_cost_usd: number
  platform_fee_per_booking_usd: number
  cbm_release_threshold: number
  weight_release_threshold: number
  cutoff_days_before_sailing: number
  cargo_restrictions: string[]
}

export interface Booking {
  id: string
  importer_id: string
  lane_id: string | null
  container_id: string | null
  supplier_name: string | null
  supplier_city: string
  supplier_province: string | null
  supplier_country: string
  delivery_city: string
  delivery_postcode: string | null
  delivery_country: string
  cargo_description: string | null
  cargo_category: CargoCategory
  cbm_estimate: number
  weight_kg_estimate: number
  cargo_ready_date_earliest: string
  cargo_ready_date_latest: string
  service_level: ServiceLevel
  delivery_mode: DeliveryMode
  pickup_address: string | null
  pickup_contact_name: string | null
  pickup_contact_phone: string | null
  pickup_window_start: string | null
  pickup_window_end: string | null
  number_of_packages: number | null
  package_type: string | null
  package_length_cm: number | null
  package_width_cm: number | null
  package_height_cm: number | null
  warehouse_receipt_cutoff: string | null
  latest_supplier_ready_date: string | null
  feasibility_status: FeasibilityStatus | null
  feasibility_reason: string | null
  preferred_sailing_option_id: string | null
  preferred_container_id: string | null
  checklist_status: ChecklistStatus
  tracking_status: ShipmentEventStage
  payment_status: PaymentStatus
  release_status: ReleaseStatus
  exception_count: number
  status: string
  match_score: number | null
  match_confidence: string | null
  admin_review_required: boolean
  quoted_cost_usd: number | null
  cbm_cost_usd: number | null
  platform_fee_usd: number | null
  urgency_fee_usd: number
  pickup_fee_usd: number
  total_cost_usd: number | null
  paid: boolean
}

export interface Container {
  id: string
  lane_id: string
  status: ContainerStatus
  bookings: string[]
  current_cbm: number
  current_weight_kg: number
  remaining_cbm: number
  remaining_weight_kg: number
  fill_percentage_cbm: number
  fill_percentage_weight: number
  shipper_count: number
  target_sailing_date: string
  carrier_cutoff_date: string
  warehouse_receipt_cutoff_date: string | null
  shipping_instructions_cutoff_date: string | null
  vgm_cutoff_date: string | null
  carrier_name: string | null
  carrier_service_id: string | null
  sailing_option_id: string | null
  vessel_name: string | null
  voyage_number: string | null
  container_cost_usd: number | null
  cost_per_cbm_usd: number | null
  estimated_departure: string | null
  estimated_arrival: string | null
  sailing_source_type: SourceType
  sailing_source_name: string
  sailing_source_reference: string | null
  sailing_source_last_verified_at: string | null
  sailing_source_confidence: SourceConfidence
  route_waypoints: RouteWaypoint[]
  route_geometry_source_type: SourceType
  route_geometry_source_name: string
  route_geometry_confidence: SourceConfidence
}

export interface Warehouse {
  id: string
  lane_id: string
  name: string
  city: string
  country: string
  address: string
  contact_name: string
  contact_phone: string
  contact_email: string
  operating_hours: string
}

export interface ConfirmBookingResponse {
  booking: Booking
  warehouse: Warehouse
  supplier_instructions: string
}

export interface Notification {
  id: string
  recipient_type: string
  recipient_id: string
  trigger: string
  message: string
  created_at: string
  scheduled_for: string | null
  read: boolean
}

export interface AuditEvent {
  id: string
  actor_role: 'importer' | 'admin' | 'system'
  actor_id: string
  event_type: string
  entity_type: string
  entity_id: string
  message: string
  metadata: Record<string, unknown>
  created_at: string
}

export interface AccountProfile {
  id: string
  owner_actor_id: string
  importer_company_name: string
  importer_contact_name: string
  importer_email: string
  importer_phone: string | null
  delivery_city: string
  delivery_postcode: string | null
  delivery_country: string
  default_supplier_city: string | null
  default_supplier_province: string | null
  default_supplier_country: string | null
  default_delivery_mode: DeliveryMode
  importer_abn: string | null
  created_at: string
  updated_at: string
}

export interface AccountIntegration {
  id: string
  owner_actor_id: string
  provider: AccountIntegrationProvider
  display_name: string
  category: string
  status: AccountIntegrationStatus
  connection_mode: string
  prompt_when: string[]
  last_verified_at: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface DeliveryPlan {
  id: string
  booking_id: string
  delivery_method: DeliveryPlanMethod
  destination_address: string
  destination_contact_name: string
  destination_contact_phone: string | null
  delivery_window_start: string | null
  delivery_window_end: string | null
  equipment_required: string[]
  status: DeliveryPlanStatus
  trucking_quote_usd: number
  courier_invoice_storage_key: string | null
  proof_of_delivery_storage_key: string | null
  notes: string | null
  booked_at: string | null
  delivered_at: string | null
  created_at: string
  updated_at: string
}

export interface MatchResult {
  booking: Booking
  container: Container | null
  lane: Lane | null
  warehouse: Warehouse | null
  notification: Notification
  lcl_estimate_usd: number | null
  saving_usd: number | null
  saving_percent: number | null
}

export interface CarrierOption {
  sailing_option_id: string
  service_id: string
  carrier_name: string
  service_name: string
  departure_port?: string
  arrival_port?: string
  sailing_date: string
  eta: string
  transit_days: number
  direct_or_transhipment: string
  total_all_in_usd: number
  carrier_gate_in_cutoff_date: string
  shipping_instructions_cutoff_date: string
  vgm_cutoff_date: string
  source_type: SourceType
  source_name: string
  source_reference: string | null
  last_verified_at: string
  confidence: SourceConfidence
  route_waypoints: RouteWaypoint[]
  route_geometry_source_type: SourceType
  route_geometry_source_name: string
  route_geometry_confidence: SourceConfidence
  score: number
  components: {
    cost: number
    schedule: number
    transit: number
    depot_proximity: number
    reliability: number
  }
}

export interface ReleaseCheckResult {
  container_id: string
  released: boolean
  reasons: string[]
  selected_carrier: CarrierOption | null
}

export interface DashboardSummary {
  lanes: number
  bookings: number
  containers: number
  committed_containers: number
  open_revenue_usd: number
  outstanding_payments_usd: number
  notifications: Notification[]
  audit_events: AuditEvent[]
  category_density_defaults: Record<string, number>
}

export interface DocumentRequirement {
  id: string
  booking_id: string
  document_type: DocumentType
  label: string
  required: boolean
  reason: string
  status: DocumentStatus
  created_at: string
  updated_at: string
}

export interface ShipmentDocument {
  id: string
  booking_id: string
  document_type: DocumentType
  file_name: string
  storage_key: string
  mime_type: string
  size_bytes: number
  status: DocumentStatus
  uploaded_by_role: 'importer' | 'admin' | 'system'
  uploaded_by_id: string
  notes: string | null
  reviewed_by: string | null
  reviewed_at: string | null
  review_note: string | null
  created_at: string
  updated_at: string
}

export interface BookingChecklistResponse {
  booking_id: string
  checklist_status: ChecklistStatus
  requirements: DocumentRequirement[]
  documents: ShipmentDocument[]
  missing_document_types: DocumentType[]
}

export interface ShipmentEvent {
  id: string
  booking_id: string
  container_id: string | null
  stage: ShipmentEventStage
  label: string
  source_type: SourceType
  source_name: string
  confidence: SourceConfidence
  occurred_at: string | null
  estimated_at: string | null
  notes: string | null
  photos: string[]
  created_at: string
}

export interface SailingSearchResult {
  sailing_option_id: string
  container_id: string | null
  lane_id: string
  carrier_name: string
  service_name: string
  departure_port: string
  arrival_port: string
  etd: string
  eta: string
  transit_days: number
  warehouse_receipt_cutoff_date: string
  carrier_gate_in_cutoff_date: string
  available_cbm: number
  available_weight_kg: number
  source_confidence: SourceConfidence
  source_name: string
  total_all_in_usd: number
  route_waypoints: RouteWaypoint[]
  route_geometry_source_type: SourceType
  route_geometry_source_name: string
  route_geometry_confidence: SourceConfidence
}

export interface SupplierAccessLink {
  id: string
  booking_id: string
  token: string
  active: boolean
  expires_at: string | null
  last_used_at: string | null
  created_at: string
}

export interface SupplierBookingSummary {
  id: string
  supplier_name: string | null
  supplier_city: string
  cargo_description: string | null
  cargo_category: CargoCategory
  cbm_estimate: number
  weight_kg_estimate: number
  cargo_ready_date_latest: string
  delivery_mode: DeliveryMode
  pickup_address: string | null
  pickup_contact_name: string | null
  pickup_contact_phone: string | null
  pickup_window_start: string | null
  pickup_window_end: string | null
  warehouse_receipt_cutoff: string | null
  latest_supplier_ready_date: string | null
  status: string
}

export interface SupplierPortalResponse {
  booking: SupplierBookingSummary
  supplier_instructions: string
  checklist: BookingChecklistResponse
  events: ShipmentEvent[]
}

export interface InvoiceLineItem {
  id: string
  invoice_id: string
  label: string
  amount_usd: number
  source: string
}

export interface Invoice {
  id: string
  booking_id: string
  status: PaymentStatus
  line_items: InvoiceLineItem[]
  subtotal_usd: number
  total_usd: number
  issued_at: string
  due_date: string
  paid_at: string | null
  provider_reference: string | null
  created_at: string
  updated_at: string
}

export interface ReleaseHold {
  id: string
  booking_id: string
  hold_type: ReleaseHoldType
  status: ReleaseHoldStatus
  reason: string
  created_at: string
  cleared_at: string | null
  waived_by: string | null
  waiver_reason: string | null
}

export interface ReleaseStatusResponse {
  booking_id: string
  release_status: ReleaseStatus
  can_release: boolean
  holds: ReleaseHold[]
}

export interface CustomsProfile {
  id: string
  booking_id: string
  incoterm: string
  goods_value_usd: number
  currency: string
  hs_code: string | null
  importer_abn: string | null
  broker_preference: CustomsBrokerPreference
  biosecurity_flags: string[]
  customs_status: CustomsStatus
  duty_estimate_usd: number
  gst_estimate_usd: number
  brokerage_fee_usd: number
  landed_cost_estimate_usd: number
  customs_entry_number: string | null
  duty_paid_usd: number | null
  gst_paid_usd: number | null
  broker_notes: string | null
  updated_at: string
}

export interface BrokerAccessLink {
  id: string
  booking_id: string
  token: string
  active: boolean
  expires_at: string | null
  last_used_at: string | null
  created_at: string
}

export interface BrokerBookingSummary {
  id: string
  importer_company_name: string | null
  importer_abn: string | null
  supplier_country: string
  delivery_country: string
  delivery_city: string
  cargo_description: string | null
  cargo_category: CargoCategory
  cbm_estimate: number
  weight_kg_estimate: number
  cargo_ready_date_latest: string
  status: string
}

export interface BrokerCustomsSummary {
  incoterm: string
  goods_value_usd: number
  currency: string
  hs_code: string | null
  biosecurity_flags: string[]
  customs_status: CustomsStatus
  duty_estimate_usd: number
  gst_estimate_usd: number
  landed_cost_estimate_usd: number
  customs_entry_number: string | null
  duty_paid_usd: number | null
  gst_paid_usd: number | null
  broker_notes: string | null
  updated_at: string
}

export type BrokerSubmittableStatus = 'submitted' | 'queried' | 'cleared'

export interface BrokerClearanceUpdate {
  customs_status: BrokerSubmittableStatus
  customs_entry_number?: string | null
  duty_paid_usd?: number | null
  gst_paid_usd?: number | null
  broker_notes?: string | null
}

export interface BrokerPortalResponse {
  booking: BrokerBookingSummary
  customs: BrokerCustomsSummary
  holds: ReleaseHold[]
  documents: ShipmentDocument[]
  events: ShipmentEvent[]
}

export interface WarehouseAccessLink {
  id: string
  booking_id: string
  token: string
  active: boolean
  expires_at: string | null
  last_used_at: string | null
  created_at: string
}

export interface WarehouseBookingSummary {
  id: string
  importer_company_name: string | null
  supplier_country: string
  supplier_city: string
  cargo_description: string | null
  cargo_category: CargoCategory
  cbm_estimate: number
  weight_kg_estimate: number
  number_of_packages: number | null
  cargo_ready_date_latest: string
  delivery_mode: DeliveryMode
  warehouse_receipt_cutoff: string | null
  warehouse_name: string | null
  cbm_actual: number | null
  weight_kg_actual: number | null
  received_at_warehouse: string | null
  status: string
}

export interface WarehouseReceiptUpdate {
  actual_cbm: number
  actual_weight_kg: number
  notes?: string | null
}

export interface WarehousePortalResponse {
  booking: WarehouseBookingSummary
  documents: ShipmentDocument[]
  events: ShipmentEvent[]
}

export interface CarrierAccessLink {
  id: string
  booking_id: string
  token: string
  active: boolean
  expires_at: string | null
  last_used_at: string | null
  created_at: string
}

export type CarrierEventStage = 'loaded' | 'departed' | 'arrived'

export interface CarrierBookingSummary {
  id: string
  importer_company_name: string | null
  container_id: string | null
  container_number: string | null
  vessel_name: string | null
  voyage_number: string | null
  carrier_name: string | null
  estimated_departure: string | null
  estimated_arrival: string | null
  baseline_estimated_arrival: string | null
  target_sailing_date: string | null
  carrier_cutoff_date: string | null
  cargo_description: string | null
  cargo_category: CargoCategory
  cbm_estimate: number
  weight_kg_estimate: number
  status: string
}

export interface CarrierEtaUpdate {
  estimated_arrival: string
  note?: string | null
}

export interface CarrierEventUpdate {
  stage: CarrierEventStage
  label?: string | null
  notes?: string | null
}

export interface CarrierPortalResponse {
  booking: CarrierBookingSummary
  documents: ShipmentDocument[]
  events: ShipmentEvent[]
}

export interface ImportProject {
  id: string
  title: string
  current_step: string
  next_action: string | null
  summary: string
  linked_purchase_order_ids: string[]
  linked_shipment_ids: string[]
}

export interface ImportProjectStepData {
  id: string
  step_key: string
  step_number: number
  data: Record<string, unknown>
  status: string
  source_references: string[]
  updated_at: string
}

export interface ApprovalRequest {
  id: string
  request_type: string
  status: 'pending' | 'approved' | 'rejected' | 'expired'
  title: string
  plain_language_summary: string
  amount_usd: number | null
  related_import_project_id: string | null
  related_booking_id: string | null
  source_reference: string | null
  created_at: string
  decided_at: string | null
  decided_by: string | null
}

export interface PurchaseOrder {
  id: string
  import_project_id: string
  booking_id: string | null
  order_reference: string
  buyer_company_name: string
  supplier_name: string
  product_summary: string
  incoterm: string
  currency: string
  goods_value: number
  deposit_amount: number
  balance_amount: number
  production_due_date: string | null
  cargo_ready_target_date: string | null
  status: string
  created_at: string
  updated_at: string
}

export interface ProductionMilestone {
  id: string
  purchase_order_id: string
  milestone_type: string
  label: string
  due_date: string | null
  completed_at: string | null
  owner: string
  status: ProductionMilestoneStatus
  notes: string | null
  buyer_approval_required: boolean
}

export interface QualityInspection {
  id: string
  purchase_order_id: string
  inspection_required: boolean
  inspection_date: string | null
  inspection_location: string | null
  result: string
  defects_summary: string | null
  buyer_approval_required: boolean
}

export interface SupplierPayRequest {
  id: string
  purchase_order_id: string
  import_project_id: string
  booking_id: string | null
  payment_stage: string
  supplier_name: string
  amount: number
  currency: string
  status: SupplierPayRequestStatus
  approval_request_id: string | null
  selected_quote_id: string | null
  marked_paid_at: string | null
  paid_outside_app_by: string | null
  proof_storage_key: string | null
  notes: string | null
  bank_details_changed: boolean
  created_at: string
  updated_at: string
}

export interface SupplierPayQuote {
  id: string
  supplier_pay_request_id: string
  provider: 'wise' | 'ofx' | 'manual_bank_transfer'
  amount: number
  source_currency: string
  target_currency: string
  fx_rate: number
  provider_fee: number
  estimated_total: number
  expires_at: string | null
  status: string
  selected: boolean
  source_name: string
}

export interface SourceMessage {
  id: string
  source_type: SourceMessageType
  from_address: string
  to_addresses: string[]
  subject: string
  body: string
  received_at: string
  attachments: string[]
  matched_import_project_id: string | null
  matched_shipment_id: string | null
  extraction_status: ExtractionStatus
  confidence: SourceConfidence
  created_at: string
}

export interface AutomationRun {
  id: string
  automation_type: string
  input_reference: string
  output_reference: string | null
  confidence: SourceConfidence
  decision: string
  reason: string
  created_tasks: string[]
  created_approvals: string[]
  audit_event_id: string | null
  created_at: string
}

export interface ImportProjectWorkspaceResponse {
  project: ImportProject
  steps: ImportProjectStepData[]
  versions: unknown[]
  events: unknown[]
  files: unknown[]
  bookings: Booking[]
  purchase_orders: PurchaseOrder[]
  production_milestones: ProductionMilestone[]
  quality_inspections: QualityInspection[]
  supplier_pay_requests: SupplierPayRequest[]
  supplier_pay_quotes: SupplierPayQuote[]
  source_messages: SourceMessage[]
  automation_runs: AutomationRun[]
  approvals: ApprovalRequest[]
}

export interface BookingPayload {
  importer_company_name: string
  importer_contact_name: string
  importer_email: string
  importer_phone?: string
  supplier_name?: string
  supplier_city: string
  supplier_province?: string
  supplier_country: string
  delivery_city: string
  delivery_postcode?: string
  delivery_country: string
  cargo_description?: string
  cargo_category: CargoCategory
  cbm_estimate: number
  weight_kg_estimate: number
  number_of_packages?: number
  package_type?: string
  package_length_cm?: number
  package_width_cm?: number
  package_height_cm?: number
  cargo_ready_date_earliest: string
  cargo_ready_date_latest: string
  service_level: ServiceLevel
  delivery_mode: DeliveryMode
  pickup_address?: string
  pickup_contact_name?: string
  pickup_contact_phone?: string
  pickup_window_start?: string
  pickup_window_end?: string
  preferred_sailing_option_id?: string
  preferred_container_id?: string
}
