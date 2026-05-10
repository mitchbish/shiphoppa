import type {
  AccountIntegration,
  AccountIntegrationProvider,
  AccountIntegrationStatus,
  AccountProfile,
  AuditEvent,
  Booking,
  BookingPayload,
  BookingChecklistResponse,
  BrokerAccessLink,
  BrokerClearanceUpdate,
  BrokerPortalResponse,
  WarehouseAccessLink,
  WarehousePortalResponse,
  WarehouseReceiptUpdate,
  CarrierAccessLink,
  CarrierEtaUpdate,
  CarrierEventUpdate,
  CarrierPortalResponse,
  TruckerAccessLink,
  TruckerPortalResponse,
  TruckerStatusUpdate,
  CarrierOption,
  Container,
  ConfirmBookingResponse,
  ContingencyOption,
  ClaimRecord,
  CustomsProfile,
  DocumentType,
  DashboardSummary,
  InsurancePolicy,
  DeliveryJob,
  DeliveryJobCreatePayload,
  DeliveryJobUpdatePayload,
  DeliveryPlan,
  LandedCostActual,
  MarketplaceOrder,
  PartnerCapability,
  PartnerProfile,
  GrowthAttributionEvent,
  GrowthAttributionEventType,
  GrowthAttributionSummary,
  PaymentProof,
  Invoice,
  ImportProject,
  ImportProjectWorkspaceResponse,
  MatchResult,
  Notification,
  ProductionMilestone,
  PurchaseOrder,
  ReleaseCheckResult,
  ReleaseStatusResponse,
  SailingSearchResult,
  SourceMessage,
  SourceMessageType,
  SentinelSubscriber,
  SupplierLead,
  SupplierProfileClaim,
  SupplierProfileClaimResponse,
  SupplierVerificationStatus,
  ShipmentDocument,
  ShipmentEvent,
  ShipmentEventStage,
  ShipmentSummary,
  ShipmentWorkspace,
  SupplierAccessLink,
  SupplierPayRequest,
  SupplierPortalResponse,
} from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.DEV ? 'http://localhost:8000' : '')
const IMPORTER_TOKEN = import.meta.env.VITE_IMPORTER_TOKEN ?? (import.meta.env.DEV ? 'shiphoppa-importer-dev' : '')
const ADMIN_TOKEN = import.meta.env.VITE_ADMIN_TOKEN ?? (import.meta.env.DEV ? 'shiphoppa-admin-dev' : '')

function tokenFor(path: string, method: string) {
  // Importer-readable automation endpoints (informational, per-shipment)
  if (path.startsWith('/automation/shipment-state/') || path.startsWith('/automation/missing-data/')) {
    return IMPORTER_TOKEN
  }
  if (
    path === '/summary' ||
    path === '/bookings' && method === 'GET' ||
    path.startsWith('/containers') ||
    path.startsWith('/ops') ||
    path.startsWith('/audit-events') ||
    path.startsWith('/documents') ||
    path.startsWith('/supplier-links') ||
    path.startsWith('/broker-links') ||
    path.startsWith('/warehouse-links') ||
    path.startsWith('/carrier-links') ||
    path.startsWith('/trucker-links') ||
    path.startsWith('/invoices') ||
    path.startsWith('/release-holds') ||
    path.startsWith('/automation') ||
    path.startsWith('/admin-tasks') ||
    path.startsWith('/sentinel/') ||
    path.startsWith('/growth/') ||
    path.startsWith('/partners') ||
    (path.includes('/events') && method !== 'GET') ||
    (path.includes('/customs-profile') && method !== 'GET')
  ) {
    return ADMIN_TOKEN
  }
  return IMPORTER_TOKEN
}

function idempotencyKey() {
  return globalThis.crypto?.randomUUID?.() ?? `key-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const method = init?.method ?? 'GET'
  const token = tokenFor(path, method)
  if (!API_BASE_URL || !token) {
    throw new Error('Ship Hoppa is missing its API deployment settings.')
  }
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  }
  if (method !== 'GET') {
    headers['Idempotency-Key'] = idempotencyKey()
  }
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      ...headers,
      ...init?.headers,
    },
    ...init,
  })

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const message = body?.detail ?? `${response.status} ${response.statusText}`
    throw new Error(Array.isArray(message) ? message.join(', ') : message)
  }

  return response.json() as Promise<T>
}

export function getSummary() {
  return request<DashboardSummary>('/summary')
}

export function getContainers() {
  return request<Container[]>('/containers')
}

export function getBookings() {
  return request<Booking[]>('/bookings')
}

export function getAccountProfile() {
  return request<AccountProfile>('/account/profile')
}

export function updateAccountProfile(payload: Partial<AccountProfile>) {
  return request<AccountProfile>('/account/profile', {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function getAccountIntegrations() {
  return request<AccountIntegration[]>('/account/integrations')
}

export function updateAccountIntegration(
  provider: AccountIntegrationProvider,
  payload: { status?: AccountIntegrationStatus; notes?: string; last_verified_at?: string },
) {
  return request<AccountIntegration>(`/account/integrations/${provider}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function createBooking(payload: BookingPayload) {
  return request<MatchResult>('/bookings', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function confirmBooking(bookingId: string) {
  return request<ConfirmBookingResponse>(`/bookings/${bookingId}/confirm`, {
    method: 'POST',
  })
}

export function getCarrierOptions(containerId: string) {
  return request<CarrierOption[]>(`/containers/${containerId}/carrier-options`)
}

export function commitContainer(containerId: string, option?: CarrierOption) {
  return request<ReleaseCheckResult>(`/containers/${containerId}/commit`, {
    method: 'POST',
    body: JSON.stringify({
      sailing_option_id: option?.sailing_option_id,
      carrier_service_id: option?.service_id,
      sailing_date: option?.sailing_date,
    }),
  })
}

export function runReleaseChecks() {
  return request<ReleaseCheckResult[]>('/ops/release-checks', {
    method: 'POST',
  })
}

export function getChecklist(bookingId: string) {
  return request<BookingChecklistResponse>(`/bookings/${bookingId}/checklist`)
}

export function uploadDocument(bookingId: string, documentType: DocumentType, fileName?: string) {
  return request<ShipmentDocument>(`/bookings/${bookingId}/documents`, {
    method: 'POST',
    body: JSON.stringify({
      document_type: documentType,
      file_name: fileName ?? `${documentType}.pdf`,
      mime_type: 'application/pdf',
      notes: 'Demo upload from Ship Hoppa workspace',
    }),
  })
}

export function approveDocument(documentId: string) {
  return request<ShipmentDocument>(`/documents/${documentId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ reason: 'Approved in operations console' }),
  })
}

export function rejectDocument(documentId: string) {
  return request<ShipmentDocument>(`/documents/${documentId}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reason: 'Needs replacement' }),
  })
}

export function getEvents(bookingId: string) {
  return request<ShipmentEvent[]>(`/bookings/${bookingId}/events`)
}

export function addEvent(bookingId: string, stage: ShipmentEventStage, label: string) {
  return request<ShipmentEvent>(`/bookings/${bookingId}/events`, {
    method: 'POST',
    body: JSON.stringify({
      stage,
      label,
      occurred_at: new Date().toISOString(),
      source_type: 'manual_admin',
      source_name: 'Ship Hoppa ops',
      confidence: 'verified',
    }),
  })
}

export function getSailings() {
  return request<SailingSearchResult[]>('/sailings')
}

export function createSupplierLink(bookingId: string) {
  return request<SupplierAccessLink>('/supplier-links', {
    method: 'POST',
    body: JSON.stringify({ booking_id: bookingId }),
  })
}

export function getSupplierPortal(token: string) {
  return request<SupplierPortalResponse>(`/supplier/${token}`)
}

export function supplierReady(token: string, readyDate: string) {
  return request<SupplierPortalResponse>(`/supplier/${token}/ready`, {
    method: 'POST',
    body: JSON.stringify({ cargo_ready_date_latest: readyDate }),
  })
}

export function uploadSupplierDocument(token: string, documentType: DocumentType) {
  return request<ShipmentDocument>(`/supplier/${token}/documents`, {
    method: 'POST',
    body: JSON.stringify({
      document_type: documentType,
      file_name: `supplier-${documentType}.pdf`,
      mime_type: 'application/pdf',
      notes: 'Demo supplier upload',
    }),
  })
}

export function createBrokerLink(bookingId: string) {
  return request<BrokerAccessLink>('/broker-links', {
    method: 'POST',
    body: JSON.stringify({ booking_id: bookingId }),
  })
}

export function getBrokerPortal(token: string) {
  return request<BrokerPortalResponse>(`/broker/${token}`)
}

export function submitBrokerClearance(token: string, payload: BrokerClearanceUpdate) {
  return request<BrokerPortalResponse>(`/broker/${token}/clearance`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function uploadBrokerDocument(
  token: string,
  documentType: DocumentType,
  fileName: string,
  notes?: string,
) {
  return request<ShipmentDocument>(`/broker/${token}/documents`, {
    method: 'POST',
    body: JSON.stringify({
      document_type: documentType,
      file_name: fileName,
      mime_type: 'application/pdf',
      notes: notes ?? null,
    }),
  })
}

export function createWarehouseLink(bookingId: string) {
  return request<WarehouseAccessLink>('/warehouse-links', {
    method: 'POST',
    body: JSON.stringify({ booking_id: bookingId }),
  })
}

export function getWarehousePortal(token: string) {
  return request<WarehousePortalResponse>(`/warehouse/${token}`)
}

export function submitWarehouseReceipt(token: string, payload: WarehouseReceiptUpdate) {
  return request<WarehousePortalResponse>(`/warehouse/${token}/receipt`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function uploadWarehouseDocument(
  token: string,
  documentType: DocumentType,
  fileName: string,
  notes?: string,
) {
  return request<ShipmentDocument>(`/warehouse/${token}/documents`, {
    method: 'POST',
    body: JSON.stringify({
      document_type: documentType,
      file_name: fileName,
      mime_type: 'application/pdf',
      notes: notes ?? null,
    }),
  })
}

export function createCarrierLink(bookingId: string) {
  return request<CarrierAccessLink>('/carrier-links', {
    method: 'POST',
    body: JSON.stringify({ booking_id: bookingId }),
  })
}

export function getCarrierPortal(token: string) {
  return request<CarrierPortalResponse>(`/carrier/${token}`)
}

export function submitCarrierEta(token: string, payload: CarrierEtaUpdate) {
  return request<CarrierPortalResponse>(`/carrier/${token}/eta`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function submitCarrierEvent(token: string, payload: CarrierEventUpdate) {
  return request<CarrierPortalResponse>(`/carrier/${token}/event`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function uploadCarrierDocument(
  token: string,
  documentType: DocumentType,
  fileName: string,
  notes?: string,
) {
  return request<ShipmentDocument>(`/carrier/${token}/documents`, {
    method: 'POST',
    body: JSON.stringify({
      document_type: documentType,
      file_name: fileName,
      mime_type: 'application/pdf',
      notes: notes ?? null,
    }),
  })
}

export function createTruckerLink(bookingId: string) {
  return request<TruckerAccessLink>('/trucker-links', {
    method: 'POST',
    body: JSON.stringify({ booking_id: bookingId }),
  })
}

export function getTruckerPortal(token: string) {
  return request<TruckerPortalResponse>(`/trucker/${token}`)
}

export function submitTruckerStatus(token: string, payload: TruckerStatusUpdate) {
  return request<TruckerPortalResponse>(`/trucker/${token}/status`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function uploadTruckerPod(token: string, fileName: string, notes?: string) {
  return request<ShipmentDocument>(`/trucker/${token}/pod`, {
    method: 'POST',
    body: JSON.stringify({
      document_type: 'delivery_order',
      file_name: fileName,
      mime_type: 'application/pdf',
      notes: notes ?? null,
    }),
  })
}

export function getInvoice(bookingId: string) {
  return request<Invoice>(`/bookings/${bookingId}/invoice`)
}

export function markInvoicePaid(invoiceId: string) {
  return request<Invoice>(`/invoices/${invoiceId}/mark-paid`, {
    method: 'POST',
  })
}

export function getReleaseStatus(bookingId: string) {
  return request<ReleaseStatusResponse>(`/bookings/${bookingId}/release-status`)
}

export function waiveReleaseHold(holdId: string) {
  return request<ReleaseStatusResponse | unknown>(`/release-holds/${holdId}/waive`, {
    method: 'POST',
    body: JSON.stringify({ reason: 'Waived by admin for demo' }),
  })
}

export function getCustomsProfile(bookingId: string) {
  return request<CustomsProfile>(`/bookings/${bookingId}/customs-profile`)
}

export function updateCustomsProfile(bookingId: string, payload: Partial<CustomsProfile>) {
  return request<CustomsProfile>(`/bookings/${bookingId}/customs-profile`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function getDeliveryPlan(bookingId: string) {
  return request<DeliveryPlan>(`/bookings/${bookingId}/delivery-plan`)
}

export function updateDeliveryPlan(bookingId: string, payload: Partial<DeliveryPlan>) {
  return request<DeliveryPlan>(`/bookings/${bookingId}/delivery-plan`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function bookDeliveryPlan(deliveryPlanId: string) {
  return request<DeliveryPlan>(`/delivery-plans/${deliveryPlanId}/book`, {
    method: 'POST',
  })
}

export function markDeliveryDelivered(deliveryPlanId: string) {
  return request<DeliveryPlan>(`/delivery-plans/${deliveryPlanId}/mark-delivered`, {
    method: 'POST',
  })
}

export function getImportProjectWorkspace(bookingId: string) {
  return request<ImportProjectWorkspaceResponse>(`/bookings/${bookingId}/import-project`)
}

export function listImportProjects(includeDeleted = false) {
  const suffix = includeDeleted ? '?include_deleted=true' : ''
  return request<ImportProject[]>(`/import-projects${suffix}`)
}

export function createImportProject(payload: {
  title: string
  description?: string
  workflow_type?: string
  summary?: string
  next_action?: string
}) {
  return request<ImportProject>('/import-projects', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateImportProject(
  projectId: string,
  payload: Partial<{
    title: string
    description: string
    summary: string
    status: string
    current_step: string
    next_action: string
    blocked_reason: string
  }>,
) {
  return request<ImportProject>(`/import-projects/${projectId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function cloneImportProject(projectId: string, newTitle?: string) {
  const suffix = newTitle ? `?new_title=${encodeURIComponent(newTitle)}` : ''
  return request<ImportProject>(`/import-projects/${projectId}/clone${suffix}`, {
    method: 'POST',
  })
}

export function softDeleteImportProject(projectId: string) {
  return request<ImportProject>(`/import-projects/${projectId}`, {
    method: 'DELETE',
  })
}

export function createSourceMessage(payload: {
  source_type?: SourceMessageType
  from_address: string
  to_addresses?: string[]
  subject: string
  body?: string
  attachment_names?: string[]
}) {
  return request<SourceMessage>('/source-messages', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getSourceMessages() {
  return request<SourceMessage[]>('/source-messages')
}

// --- Landed cost ---

export type LandedCostLine = {
  category: string
  label: string
  amount_usd: number
  status: 'estimate' | 'actual'
}

export type LandedCostSummary = {
  booking_id: string
  lines: LandedCostLine[]
  total_landed_cost_usd: number
  paid_to_date_usd: number
  remaining_estimate_usd: number
  currency: string
}

export function getLandedCostSummary(bookingId: string) {
  return request<LandedCostSummary>(`/bookings/${bookingId}/landed-cost`)
}

// --- FCL spare-space ---

export type SpaceOpportunity = {
  id: string
  booking_id: string
  container_id: string | null
  opportunity_type: string
  total_container_cbm: number
  booked_cbm: number
  protected_buffer_cbm: number
  recoverable_cbm: number
  estimated_recovery_usd: number
  status: 'detected' | 'awaiting_owner_approval' | 'listed' | 'matched' | 'closed' | 'declined'
  owner_actor_id: string
  detected_at: string
  listed_at: string | null
  closed_at: string | null
  notes: string | null
}

export function getSpaceOpportunities(bookingId: string) {
  return request<SpaceOpportunity[]>(`/bookings/${bookingId}/space-opportunities`)
}

export function detectSpaceOpportunity(bookingId: string) {
  return request<SpaceOpportunity | null>(`/bookings/${bookingId}/space-opportunities/detect`, {
    method: 'POST',
  })
}

export function listSpaceOpportunity(opportunityId: string) {
  return request<SpaceOpportunity>(`/space-opportunities/${opportunityId}/list`, {
    method: 'POST',
  })
}

// --- Supplier invoice extractor ---

export type ParsedInvoice = {
  invoice_number: string | null
  proforma_number: string | null
  purchase_order_reference: string | null
  supplier_name: string | null
  issue_date: string | null
  due_date: string | null
  currency: string | null
  total_amount: number | null
  bank_name: string | null
  account_number_last4: string | null
  swift_code: string | null
  iban_last4: string | null
  beneficiary_name: string | null
  line_items: Array<{
    description: string
    quantity: number | null
    unit_price: number | null
    amount: number | null
  }>
  confidence: 'estimated' | 'verified' | 'confirmed'
  source_snippet: string | null
}

export type AppliedInvoiceResult = {
  matched_purchase_order_id: string | null
  supplier_pay_request_id: string | null
  approval_request_id: string | null
}

export type ParseInvoiceResponse = {
  parsed: ParsedInvoice
  applied?: AppliedInvoiceResult
}

export function parseInvoiceText(text: string, options?: { booking_id?: string; apply?: boolean }) {
  return request<ParseInvoiceResponse>('/invoices/parse-text', {
    method: 'POST',
    body: JSON.stringify({ text, booking_id: options?.booking_id, apply: options?.apply ?? false }),
  })
}

export function extractInvoiceFromMessage(messageId: string, options?: { booking_id?: string; apply?: boolean }) {
  const params = new URLSearchParams()
  if (options?.apply) params.set('apply', 'true')
  if (options?.booking_id) params.set('booking_id', options.booking_id)
  const qs = params.toString()
  return request<ParseInvoiceResponse>(
    `/source-messages/${messageId}/extract-invoice${qs ? '?' + qs : ''}`,
    { method: 'POST' },
  )
}

export type ParsePdfResponse = ParseInvoiceResponse & {
  filename: string
  warning?: string
}

// --- Quality inspection ---

export type QualityInspectionRecord = {
  id: string
  purchase_order_id: string
  inspection_required: boolean
  inspection_provider: string | null
  inspection_date: string | null
  inspection_location: string | null
  report_document_id: string | null
  result: 'not_required' | 'pending' | 'booked' | 'passed' | 'failed' | 'rework_required' | 'waived'
  defects_summary: string | null
  buyer_approval_required: boolean
  created_at: string
  updated_at: string
}

export function getBookingInspections(bookingId: string) {
  return request<QualityInspectionRecord[]>(`/bookings/${bookingId}/quality-inspections`)
}

export function bookInspection(
  inspectionId: string,
  payload: { provider: string; inspection_date: string; location: string },
) {
  return request<QualityInspectionRecord>(`/quality-inspections/${inspectionId}/book`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

// --- HS code suggestions ---

export type HsSuggestion = {
  hs_code: string
  description: string
  confidence: 'estimated' | 'verified' | 'confirmed'
  rationale: string
}

export type HsSuggestionsResponse = {
  booking_id: string
  current_hs_code: string | null
  suggestions: HsSuggestion[]
}

export function getHsSuggestions(bookingId: string) {
  return request<HsSuggestionsResponse>(`/bookings/${bookingId}/hs-suggestions`)
}

export function acceptHsSuggestion(bookingId: string) {
  return request<CustomsProfile>(
    `/bookings/${bookingId}/customs-profile/accept-hs-suggestion`,
    { method: 'POST' },
  )
}

export async function parseInvoicePdf(
  file: File,
  options?: { booking_id?: string; apply?: boolean },
): Promise<ParsePdfResponse> {
  if (!API_BASE_URL) throw new Error('Ship Hoppa is missing its API deployment settings.')
  const token = tokenFor('/invoices/parse-pdf', 'POST')
  if (!token) throw new Error('Ship Hoppa is missing its API deployment settings.')
  const formData = new FormData()
  formData.append('file', file)
  if (options?.booking_id) formData.append('booking_id', options.booking_id)
  if (options?.apply) formData.append('apply', 'true')
  const response = await fetch(`${API_BASE_URL}/invoices/parse-pdf`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Idempotency-Key': idempotencyKey(),
    },
    body: formData,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const message = body?.detail ?? `${response.status} ${response.statusText}`
    throw new Error(Array.isArray(message) ? message.join(', ') : message)
  }
  return response.json()
}

// --- Notifications ---

export function getNotifications() {
  return request<Notification[]>('/notifications')
}

export function markAllNotificationsRead() {
  return request<{ marked_read: number }>('/notifications/mark-all-read', { method: 'POST' })
}

export function markNotificationRead(notificationId: string) {
  return request<Notification>(`/notifications/${notificationId}/read`, { method: 'POST' })
}

export function createPurchaseOrder(payload: {
  booking_id: string
  order_reference: string
  buyer_company_name: string
  supplier_name: string
  product_summary: string
  goods_value: number
  deposit_amount: number
  balance_amount: number
  production_due_date?: string
  cargo_ready_target_date?: string
  inspection_required?: boolean
}) {
  return request<PurchaseOrder>('/purchase-orders', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function completeProductionMilestone(milestoneId: string, notes?: string) {
  return request<ProductionMilestone>(`/production-milestones/${milestoneId}/complete`, {
    method: 'POST',
    body: JSON.stringify({ notes: notes ?? 'Completed from the Ship Hoppa workflow.' }),
  })
}

export function markSupplierPayPaid(supplierPayRequestId: string, notes?: string) {
  return request<SupplierPayRequest>(`/supplier-pay-requests/${supplierPayRequestId}/mark-paid`, {
    method: 'POST',
    body: JSON.stringify({
      paid_by: 'Importer',
      notes: notes ?? 'Paid outside Ship Hoppa.',
    }),
  })
}

// --- Automation Engine ---

export type ShipmentStateResponse = {
  booking_id: string
  lifecycle_state: string
  next_action: string
}

export type MissingDataItem = {
  field: string
  label: string
  responsible_party: string
  urgency: string
  chase_channel: string
}

export type AutomationRunResult = {
  lifecycle_state: string
  next_action_label: string
  missing_data: MissingDataItem[]
  chase_messages_queued: number
  state_advanced: boolean
  approvals_created: number
  admin_tasks_created: number
}

export type AutomationRunAllResult = {
  shipments_processed: number
  total_chase_messages: number
  total_missing_items: number
  states: Record<string, string>
}

export type StaleCheckAlert = {
  booking_id: string
  alert: string
  message: string
  severity: string
}

export function getShipmentState(bookingId: string) {
  return request<ShipmentStateResponse>(`/automation/shipment-state/${bookingId}`)
}

export function getMissingData(bookingId: string) {
  return request<MissingDataItem[]>(`/automation/missing-data/${bookingId}`)
}

export function runBookingAutomation(bookingId: string) {
  return request<AutomationRunResult>(`/automation/run/${bookingId}`, {
    method: 'POST',
  })
}

export function runAllAutomation() {
  return request<AutomationRunAllResult>('/automation/run-all', {
    method: 'POST',
  })
}

export function getStaleChecks() {
  return request<StaleCheckAlert[]>('/automation/stale-checks')
}

// --- Admin Tasks ---

export type AdminTask = {
  id: string
  booking_id: string
  task_type: string
  title: string
  status: 'open' | 'done' | 'waived'
  due_at: string | null
  created_at: string
  updated_at: string
}

export type AdminTaskSummary = {
  total_open: number
  total_done: number
  total_waived: number
  by_type: Record<string, number>
}

export function getAdminTasks(params?: { status?: string; booking_id?: string }) {
  const query = new URLSearchParams()
  if (params?.status) query.set('status', params.status)
  if (params?.booking_id) query.set('booking_id', params.booking_id)
  const qs = query.toString()
  return request<AdminTask[]>(`/admin-tasks${qs ? '?' + qs : ''}`)
}

export function getAdminTaskSummary() {
  return request<AdminTaskSummary>('/admin-tasks/summary')
}

export function resolveAdminTask(taskId: string) {
  return request<AdminTask>(`/admin-tasks/${taskId}/resolve`, { method: 'POST' })
}

export function dismissAdminTask(taskId: string) {
  return request<AdminTask>(`/admin-tasks/${taskId}/dismiss`, { method: 'POST' })
}

// --- Approvals ---

export type ApprovalRequestRecord = {
  id: string
  request_type: string
  status: 'pending' | 'approved' | 'rejected' | 'expired'
  title: string
  plain_language_summary: string
  amount_usd: number | null
  due_at: string | null
  related_import_project_id: string | null
  related_booking_id: string | null
  source_reference: string | null
  created_at: string
  decided_at: string | null
  decided_by: string | null
  review_requested_by: string | null
  review_requested_at: string | null
  review_requested_reason: string | null
}

export function getApprovals() {
  return request<ApprovalRequestRecord[]>('/approvals')
}

export function approveApprovalRequest(approvalId: string, reason?: string) {
  return request<ApprovalRequestRecord>(`/approvals/${approvalId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ reason: reason ?? 'Approved' }),
  })
}

export function rejectApprovalRequest(approvalId: string, reason?: string) {
  return request<ApprovalRequestRecord>(`/approvals/${approvalId}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reason: reason ?? 'Rejected' }),
  })
}

export function requestApprovalReview(approvalId: string, reason: string) {
  return request<ApprovalRequestRecord>(`/approvals/${approvalId}/request-review`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  })
}

// --- Shipments aggregator ---

export function getShipments() {
  return request<ShipmentSummary[]>('/shipments')
}

export function getShipmentWorkspace(bookingId: string) {
  return request<ShipmentWorkspace>(`/shipments/${bookingId}/workspace`)
}

export function getSupplierPortalPreview(bookingId: string) {
  return request<SupplierPortalResponse>(`/bookings/${bookingId}/supplier-preview`)
}

// --- Sentinel SMS subscribers ---

export function getSentinelSubscribers() {
  return request<SentinelSubscriber[]>('/sentinel/subscribers')
}

export function createSentinelSubscriber(phone_number: string, label?: string) {
  return request<SentinelSubscriber>('/sentinel/subscribers', {
    method: 'POST',
    body: JSON.stringify({ phone_number, label }),
  })
}

export function confirmSentinelSubscriber(token: string) {
  return request<SentinelSubscriber>('/sentinel/subscribers/confirm', {
    method: 'POST',
    body: JSON.stringify({ token }),
  })
}

export function optOutSentinelSubscriber(phone_number: string) {
  return request<SentinelSubscriber>('/sentinel/subscribers/opt-out', {
    method: 'POST',
    body: JSON.stringify({ phone_number }),
  })
}

// --- Extraction preview (dry run) ---

export type ExtractedFactPreview = {
  field: string
  value: string
  confidence: 'verified' | 'estimated' | 'unverified'
  source_snippet: string
}

export type ExtractionPreviewResponse = {
  facts: ExtractedFactPreview[]
  extracted_count: number
  would_match_booking_id: string | null
}

export function extractFactsPreview(text: string, subject?: string) {
  return request<ExtractionPreviewResponse>('/automation/extract-preview', {
    method: 'POST',
    body: JSON.stringify({ text, subject }),
  })
}

// --- Partners + capabilities + contingencies (admin) ---

export function listPartners() {
  return request<PartnerProfile[]>('/partners')
}

export function createPartner(payload: Partial<PartnerProfile> & { partner_type: PartnerProfile['partner_type']; name: string }) {
  return request<PartnerProfile>('/partners', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updatePartner(partnerId: string, payload: Partial<PartnerProfile>) {
  return request<PartnerProfile>(`/partners/${partnerId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function listPartnerCapabilities(partnerId: string) {
  return request<PartnerCapability[]>(`/partners/${partnerId}/capabilities`)
}

export function createPartnerCapability(partnerId: string, payload: Partial<PartnerCapability> & { capability_type: PartnerCapability['capability_type'] }) {
  return request<PartnerCapability>(`/partners/${partnerId}/capabilities`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function listContingencyOptions(bookingId: string) {
  return request<ContingencyOption[]>(`/bookings/${bookingId}/contingency-options`)
}

export function createContingencyOption(bookingId: string, payload: Partial<ContingencyOption> & { issue_type: ContingencyOption['issue_type']; option_type: ContingencyOption['option_type']; plain_language_summary: string }) {
  return request<ContingencyOption>(`/bookings/${bookingId}/contingency-options`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateContingencyOption(optionId: string, payload: Partial<ContingencyOption>) {
  return request<ContingencyOption>(`/contingency-options/${optionId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

// --- Insurance + claims ---

export function getInsurancePolicy(bookingId: string) {
  return request<InsurancePolicy>(`/bookings/${bookingId}/insurance-policy`)
}

export function recordInsurancePolicy(bookingId: string, payload: Partial<InsurancePolicy>) {
  return request<InsurancePolicy>(`/bookings/${bookingId}/insurance-policy`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function listClaims(bookingId: string) {
  return request<ClaimRecord[]>(`/bookings/${bookingId}/claims`)
}

export function createClaim(bookingId: string, payload: Partial<ClaimRecord> & { claim_type: ClaimRecord['claim_type'] }) {
  return request<ClaimRecord>(`/bookings/${bookingId}/claims`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateClaim(claimId: string, payload: Partial<ClaimRecord>) {
  return request<ClaimRecord>(`/claims/${claimId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

// --- Marketplace orders ---

export function listMarketplaceOrders(params: { booking_id?: string; import_project_id?: string } = {}) {
  const search = new URLSearchParams()
  if (params.booking_id) search.set('booking_id', params.booking_id)
  if (params.import_project_id) search.set('import_project_id', params.import_project_id)
  const suffix = search.toString()
  return request<MarketplaceOrder[]>(`/marketplace-orders${suffix ? `?${suffix}` : ''}`)
}

export function recordMarketplaceOrder(payload: Partial<MarketplaceOrder> & { marketplace: MarketplaceOrder['marketplace'] }) {
  return request<MarketplaceOrder>('/marketplace-orders', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

// --- Payment proofs + landed cost ---

export function listPaymentProofs(bookingId: string) {
  return request<PaymentProof[]>(`/bookings/${bookingId}/payment-proofs`)
}

export function recordPaymentProof(bookingId: string, payload: Partial<PaymentProof> & {
  payment_type: PaymentProof['payment_type']
  paid_amount: number
  paid_currency: string
  paid_at: string
  paid_by: string
}) {
  return request<PaymentProof>(`/bookings/${bookingId}/payment-proofs`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function reconcilePaymentProof(proofId: string, payload: { reconciliation_status: PaymentProof['reconciliation_status']; variance_amount?: number; notes?: string }) {
  return request<PaymentProof>(`/payment-proofs/${proofId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function getLandedCostActual(bookingId: string) {
  return request<LandedCostActual>(`/bookings/${bookingId}/landed-cost-actual`)
}

export function recordLandedCostActual(bookingId: string, payload: Partial<LandedCostActual> & { actual_total_usd: number }) {
  return request<LandedCostActual>(`/bookings/${bookingId}/landed-cost-actual`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

// --- Delivery jobs ---

export function listDeliveryJobsForBooking(bookingId: string) {
  return request<DeliveryJob[]>(`/bookings/${bookingId}/delivery-jobs`)
}

export function createDeliveryJob(bookingId: string, payload: DeliveryJobCreatePayload) {
  return request<DeliveryJob>(`/bookings/${bookingId}/delivery-jobs`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateDeliveryJob(jobId: string, payload: DeliveryJobUpdatePayload) {
  return request<DeliveryJob>(`/delivery-jobs/${jobId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

// --- Supplier profile claim ---

export function listSupplierLeads() {
  return request<SupplierLead[]>('/growth/supplier-leads')
}

export function updateSupplierLeadVerification(
  leadId: string,
  payload: { verification_status: SupplierVerificationStatus; verification_notes?: string },
) {
  return request<SupplierLead>(`/growth/supplier-leads/${leadId}/verification`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function listGrowthAttributionEvents(filters: {
  event_type?: GrowthAttributionEventType
  source?: string
  channel?: string
  template_key?: string
  category?: string
  region?: string
  supplier_lead_id?: string
  shipment_id?: string
  since?: string
  until?: string
  limit?: number
} = {}) {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== '' && value !== null) {
      query.set(key, String(value))
    }
  }
  const suffix = query.toString() ? `?${query.toString()}` : ''
  return request<GrowthAttributionEvent[]>(`/growth/attribution-events${suffix}`)
}

export function getGrowthAttributionSummary(
  group_by: 'source' | 'channel' | 'category' | 'region' | 'event_type' | 'campaign' = 'source',
  filters: { event_type?: GrowthAttributionEventType; since?: string; until?: string } = {},
) {
  const query = new URLSearchParams({ group_by })
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== '' && value !== null) {
      query.set(key, String(value))
    }
  }
  return request<GrowthAttributionSummary>(`/growth/attribution-summary?${query.toString()}`)
}

export function createSupplierClaimLink(leadId: string) {
  return request<SupplierProfileClaim>(`/growth/supplier-leads/${leadId}/claim-link`, {
    method: 'POST',
  })
}

export function getSupplierClaim(token: string) {
  return request<SupplierProfileClaimResponse>(`/supplier-claim/${token}`)
}

export function acceptSupplierClaim(token: string, contact_email: string, contact_name: string) {
  return request<SupplierProfileClaimResponse>(`/supplier-claim/${token}/accept`, {
    method: 'POST',
    body: JSON.stringify({ contact_email, contact_name }),
  })
}

// --- Audit log (admin) ---

export type AuditEventFilters = {
  actor_id?: string
  actor_role?: 'importer' | 'admin' | 'system'
  event_type?: string
  entity_type?: string
  entity_id?: string
  since?: string
  until?: string
  limit?: number
}

export function getAuditEvents(filters: AuditEventFilters = {}) {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== null && value !== '') {
      params.set(key, String(value))
    }
  }
  const suffix = params.toString()
  return request<AuditEvent[]>(`/audit-events${suffix ? `?${suffix}` : ''}`)
}
