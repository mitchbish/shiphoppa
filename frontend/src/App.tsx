import { useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import {
  ArrowRight,
  Bell,
  CalendarClock,
  Check,
  ChevronRight,
  CircleDollarSign,
  CircleHelp,
  ClipboardCheck,
  Container as ContainerIcon,
  FileText,
  Gauge,
  Loader2,
  MapPin,
  PackageCheck,
  Receipt,
  RefreshCw,
  Scale,
  Ship,
  ShieldCheck,
  Truck,
  UserRound,
} from 'lucide-react'
import './App.css'
import {
  addEvent,
  approveDocument,
  bookDeliveryPlan,
  createBrokerLink,
  createCarrierLink,
  createSupplierLink,
  createTruckerLink,
  createWarehouseLink,
  commitContainer,
  getBrokerPortal,
  getCarrierPortal,
  getTruckerPortal,
  getWarehousePortal,
  submitBrokerClearance,
  submitCarrierEta,
  submitCarrierEvent,
  submitTruckerStatus,
  submitWarehouseReceipt,
  uploadBrokerDocument,
  uploadCarrierDocument,
  uploadTruckerPod,
  uploadWarehouseDocument,
  confirmBooking,
  createBooking,
  createPurchaseOrder,
  createSourceMessage,
  completeProductionMilestone,
  getAccountIntegrations,
  getAccountProfile,
  getChecklist,
  getBookings,
  getCarrierOptions,
  getContainers,
  getCustomsProfile,
  getDeliveryPlan,
  getEvents,
  getImportProjectWorkspace,
  getInvoice,
  getReleaseStatus,
  getSailings,
  getSummary,
  markInvoicePaid,
  markDeliveryDelivered,
  markSupplierPayPaid,
  runReleaseChecks,
  runAllAutomation,
  getShipmentState,
  getMissingData,
  getStaleChecks,
  getAdminTasks,
  getAdminTaskSummary,
  resolveAdminTask,
  dismissAdminTask,
  getApprovals,
  approveApprovalRequest,
  rejectApprovalRequest,
  getSourceMessages,
  getLandedCostSummary,
  getNotifications,
  markAllNotificationsRead,
  getSpaceOpportunities,
  detectSpaceOpportunity,
  listSpaceOpportunity,
  parseInvoiceText,
  parseInvoicePdf,
  getBookingInspections,
  bookInspection,
  getAuditEvents,
  getHsSuggestions,
  acceptHsSuggestion,
  supplierReady,
  updateAccountIntegration,
  updateAccountProfile,
  updateCustomsProfile,
  updateDeliveryPlan,
  uploadDocument,
  uploadSupplierDocument,
} from './api'
import type { AuditEventFilters } from './api'
import type {
  AdminTask,
  AdminTaskSummary,
  ApprovalRequestRecord,
  AutomationRunAllResult,
  HsSuggestionsResponse,
  LandedCostSummary,
  ParsedInvoice,
  QualityInspectionRecord,
  SpaceOpportunity,
  MissingDataItem as APIMissingDataItem,
  ShipmentStateResponse,
  StaleCheckAlert,
} from './api'
import type {
  AccountIntegration,
  AccountIntegrationProvider,
  AccountProfile,
  AuditEvent,
  Booking,
  BookingPayload,
  BookingChecklistResponse,
  BrokerAccessLink,
  BrokerClearanceUpdate,
  BrokerPortalResponse,
  BrokerSubmittableStatus,
  WarehouseAccessLink,
  WarehousePortalResponse,
  CarrierAccessLink,
  CarrierEventStage,
  CarrierPortalResponse,
  TruckerAccessLink,
  TruckerPortalResponse,
  TruckerStage,
  CargoCategory,
  CarrierOption,
  Container,
  CustomsProfile,
  DashboardSummary,
  DeliveryPlan,
  DeliveryPlanMethod,
  DeliveryMode,
  DocumentType,
  FeasibilityStatus,
  Invoice,
  ImportProjectWorkspaceResponse,
  MatchResult,
  ReleaseStatusResponse,
  SailingSearchResult,
  Notification,
  ShipmentEvent,
  SourceMessage,
  SupplierAccessLink,
  SupplierPortalResponse,
} from './types'

type View =
  | 'profile'
  | 'supplier'
  | 'integrations'
  | 'help'
  | 'inbox'
  | 'notifications'
  | 'production'
  | 'inspection'
  | 'supplier_pay'
  | 'order_docs'
  | 'book'
  | 'ship_docs'
  | 'handoff'
  | 'sailings'
  | 'tracking'
  | 'money'
  | 'customs'
  | 'delivery'
  | 'admin'
type WorkspaceMode = 'customer' | 'admin-login' | 'admin' | 'broker-portal' | 'warehouse-portal' | 'carrier-portal' | 'trucker-portal'
type AdminView = 'overview' | 'containers' | 'exceptions' | 'documents' | 'tracking' | 'payments' | 'customs' | 'automation' | 'audit'
type TrackingStage = ShipmentEvent['stage']
type MapPoint = { lat: number; lng: number }
type MapPlotPoint = { x: number; y: number }
type TileMapViewport = { zoom: number; xMin: number; xMax: number; yMin: number; yMax: number }
type MapTile = { x: number; y: number; z: number }
type CustomerPhaseId = 'order' | 'ship' | 'clear' | 'account'
type CustomerPhase = {
  id: CustomerPhaseId
  number: string
  label: string
  summary: string
  defaultView: View
  views: Array<{ view: View; label: string; icon: ReactNode }>
}
type PhaseStepStatus = 'ready' | 'attention' | 'idle'
type PhaseOverviewItem = {
  view: View
  icon: ReactNode
  title: string
  detail: string
  meta: string
  status: PhaseStepStatus
  statusLabel: string
  active?: boolean
}

interface CustomerProfile {
  importer_company_name: string
  importer_contact_name: string
  importer_email: string
  importer_phone: string
  delivery_city: string
  delivery_postcode: string
  delivery_country: string
}

interface SupplierLocation {
  city: string
  province: string
  country: string
  pickupAddress: string
}

const cargoOptions: { value: CargoCategory; label: string }[] = [
  { value: 'tiles_stone', label: 'Tiles & stone' },
  { value: 'furniture', label: 'Furniture' },
  { value: 'homewares', label: 'Homewares' },
  { value: 'bathroom_fittings', label: 'Bathroom fittings' },
  { value: 'lighting', label: 'Lighting' },
  { value: 'hardware', label: 'Hardware' },
  { value: 'garden', label: 'Garden' },
  { value: 'automotive', label: 'Automotive' },
  { value: 'other', label: 'Other' },
]

const packagingOptions = ['Cartons', 'Pallets', 'Crates', 'Wooden cases', 'Rolls', 'Bags', 'Mixed packaging']

const categoryDefaults: Record<CargoCategory, { cbm: number; weight: number }> = {
  tiles_stone: { cbm: 8, weight: 12000 },
  furniture: { cbm: 18, weight: 3600 },
  homewares: { cbm: 10, weight: 3500 },
  bathroom_fittings: { cbm: 9, weight: 7200 },
  lighting: { cbm: 12, weight: 1800 },
  hardware: { cbm: 5, weight: 6000 },
  garden: { cbm: 10, weight: 4000 },
  automotive: { cbm: 8, weight: 4800 },
  other: { cbm: 8, weight: 4000 },
}

const CONTAINER_CBM_LIMIT = 55
const CONTAINER_WEIGHT_LIMIT_KG = 20_000

const supplierLocations: SupplierLocation[] = [
  {
    city: 'Foshan',
    province: 'Guangdong',
    country: 'China',
    pickupAddress: 'Ship Hoppa Foshan CFS, No. 18 Jihua West Road, Chancheng District, Foshan, Guangdong, China',
  },
  {
    city: 'Guangzhou',
    province: 'Guangdong',
    country: 'China',
    pickupAddress: 'Guangzhou Supplier Dispatch Hub, No. 88 Huangpu East Road, Huangpu District, Guangzhou, Guangdong, China',
  },
  {
    city: 'Dongguan',
    province: 'Guangdong',
    country: 'China',
    pickupAddress: 'Dongguan Home Furnishings Warehouse, No. 26 Furniture Avenue, Houjie Town, Dongguan, Guangdong, China',
  },
  {
    city: 'Shenzhen',
    province: 'Guangdong',
    country: 'China',
    pickupAddress: 'Shenzhen Supplier Warehouse, No. 6 Baolong 3rd Road, Longgang District, Shenzhen, Guangdong, China',
  },
  {
    city: 'Zhongshan',
    province: 'Guangdong',
    country: 'China',
    pickupAddress: 'Zhongshan Lighting Consolidation Point, No. 12 Guzhen Industrial Road, Zhongshan, Guangdong, China',
  },
  {
    city: 'Yiwu',
    province: 'Zhejiang',
    country: 'China',
    pickupAddress: 'Yiwu Supplier Warehouse, No. 588 Chengxin Avenue, Yiwu, Zhejiang, China',
  },
  {
    city: 'Ningbo',
    province: 'Zhejiang',
    country: 'China',
    pickupAddress: 'Ningbo Export Warehouse, No. 99 Beilun Port Road, Ningbo, Zhejiang, China',
  },
  {
    city: 'Shanghai',
    province: 'Shanghai',
    country: 'China',
    pickupAddress: 'Shanghai Supplier Warehouse, No. 1688 Huqingping Highway, Qingpu District, Shanghai, China',
  },
  {
    city: 'Xiamen',
    province: 'Fujian',
    country: 'China',
    pickupAddress: 'Xiamen Export Warehouse, No. 188 Xiangyu Road, Huli District, Xiamen, Fujian, China',
  },
  {
    city: 'Qingdao',
    province: 'Shandong',
    country: 'China',
    pickupAddress: 'Qingdao Supplier Warehouse, No. 77 Qianwan Port Road, Huangdao District, Qingdao, Shandong, China',
  },
]

const today = new Date()
const dateFromNow = (days: number) => {
  const value = new Date(today)
  value.setDate(value.getDate() + days)
  return value.toISOString().slice(0, 10)
}

const PROFILE_STORAGE_KEY = 'ship-hoppa-customer-profile'

const defaultProfile: CustomerProfile = {
  importer_company_name: 'Bayside Build Co.',
  importer_contact_name: 'Alex Morgan',
  importer_email: 'alex@baysidebuild.example',
  importer_phone: '+61 400 555 010',
  delivery_city: 'Brisbane',
  delivery_postcode: '4101',
  delivery_country: 'Australia',
}

function readStoredProfile(): CustomerProfile {
  try {
    const stored = globalThis.localStorage?.getItem(PROFILE_STORAGE_KEY)
    if (!stored) return defaultProfile
    return { ...defaultProfile, ...JSON.parse(stored) }
  } catch {
    return defaultProfile
  }
}

function customerProfileFromAccount(profile: AccountProfile): CustomerProfile {
  return {
    importer_company_name: profile.importer_company_name,
    importer_contact_name: profile.importer_contact_name,
    importer_email: profile.importer_email,
    importer_phone: profile.importer_phone ?? '',
    delivery_city: profile.delivery_city,
    delivery_postcode: profile.delivery_postcode ?? '',
    delivery_country: profile.delivery_country,
  }
}

function bookingDefaultsFromAccountProfile(profile: AccountProfile): Partial<BookingPayload> {
  const defaults: Partial<BookingPayload> = {
    ...customerProfileFromAccount(profile),
    delivery_mode: profile.default_delivery_mode,
  }
  if (profile.default_supplier_city) defaults.supplier_city = profile.default_supplier_city
  if (profile.default_supplier_province) defaults.supplier_province = profile.default_supplier_province
  if (profile.default_supplier_country) defaults.supplier_country = profile.default_supplier_country
  return defaults
}

const initialForm: BookingPayload = {
  ...defaultProfile,
  supplier_name: 'Dongguan Home Furnishings',
  supplier_city: 'Dongguan',
  supplier_province: 'Guangdong',
  supplier_country: 'China',
  cargo_description: 'flat-pack vanities and bathroom cabinets',
  cargo_category: 'furniture',
  cbm_estimate: 17.28,
  weight_kg_estimate: 3800,
  number_of_packages: 24,
  package_type: 'Cartons',
  package_length_cm: 120,
  package_width_cm: 80,
  package_height_cm: 75,
  cargo_ready_date_earliest: dateFromNow(1),
  cargo_ready_date_latest: dateFromNow(5),
  service_level: 'standard',
  delivery_mode: 'ship_hoppa_pickup',
  pickup_address: 'Dongguan Home Furnishings Warehouse, No. 26 Furniture Avenue, Houjie Town, Dongguan, Guangdong, China',
  pickup_contact_name: 'Supplier dispatch desk',
  pickup_contact_phone: '+86 20 5555 0199',
  pickup_window_start: dateFromNow(2),
  pickup_window_end: dateFromNow(5),
}

const formatMoney = (value: number | null | undefined) =>
  value == null
    ? 'TBC'
    : new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        maximumFractionDigits: 0,
      }).format(value)

const formatPercent = (value: number) => `${Math.round(value * 100)}%`

const formatQuantity = (value: number, maximumFractionDigits = 2) =>
  new Intl.NumberFormat('en-US', { maximumFractionDigits }).format(value)

const formatMeasure = (value: number, unit: 'CBM' | 'kg') =>
  `${formatQuantity(value, unit === 'kg' ? 0 : 2)} ${unit}`

function calculateVolumeM3(
  packages: number | undefined,
  lengthCm: number | undefined,
  widthCm: number | undefined,
  heightCm: number | undefined,
) {
  if (!packages || !lengthCm || !widthCm || !heightCm) return null
  return Math.round(((packages * lengthCm * widthCm * heightCm) / 1_000_000) * 100) / 100
}

const formatDateShort = (value: string | null | undefined) => {
  if (!value) return 'TBC'
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(new Date(`${value.slice(0, 10)}T00:00:00`))
}

const formatDateFriendly = (value: string | null | undefined) => {
  if (!value) return 'TBC'
  return new Intl.DateTimeFormat('en-US', { weekday: 'short', month: 'short', day: 'numeric' }).format(
    new Date(`${value.slice(0, 10)}T00:00:00`),
  )
}

const formatDateInput = (daysFromToday: number) => dateFromNow(daysFromToday)

const statusLabels: Record<FeasibilityStatus, string> = {
  feasible: 'This sailing works',
  tight: 'Tight cutoff',
  misses_cutoff: 'Next available sailing',
  admin_review: 'Team review required',
}

const deliveryModeLabels: Record<DeliveryMode, string> = {
  ship_hoppa_pickup: 'Ship Hoppa pickup',
  self_delivery: 'Self-delivery',
}

const deliveryPlanMethodLabels: Record<DeliveryPlanMethod, string> = {
  ship_hoppa_trucker: 'Ship Hoppa trucker',
  importer_trucker: 'My own trucker',
  warehouse_pickup: 'Warehouse pickup',
}

const documentTypeLabels: Record<DocumentType, string> = {
  commercial_invoice: 'Commercial invoice',
  packing_list: 'Packing list',
  supplier_photos: 'Supplier photos',
  product_specs: 'Product specs',
  fumigation_ispm: 'Fumigation / ISPM 15 evidence',
  shipping_instructions: 'Shipping instructions',
  house_bill: 'House BL',
  arrival_notice: 'Arrival notice',
  delivery_order: 'Delivery order',
}

const orderDocumentTypes = new Set<DocumentType>(['commercial_invoice', 'supplier_photos', 'product_specs'])
const shipDocumentTypes = new Set<DocumentType>([
  'packing_list',
  'fumigation_ispm',
  'shipping_instructions',
  'house_bill',
  'arrival_notice',
  'delivery_order',
])

const biosecurityFlagLabels: Record<string, string> = {
  timber_packaging_ispm_15: 'Wooden packaging needs a treated-and-marked stamp',
  biosecurity_inspection_possible: 'Border inspection may be required',
}

const customsStatusLabels: Record<string, string> = {
  documents_required: 'Details still needed',
  submitted: 'With the broker',
  queried: 'Question from customs',
  cleared: 'Cleared',
  held: 'On hold',
}

const customsStatusHelp: Record<string, string> = {
  documents_required: 'We still need enough product and value information before the broker can finish the customs file.',
  submitted: 'The customs file has been sent to the broker or authorities and is waiting on a response.',
  queried: 'The broker or border team has asked a question that needs an answer before release.',
  cleared: 'Customs is clear, so this shipment can move to normal release checks.',
  held: 'The shipment is paused until customs or biosecurity clears the issue.',
}

const brokerPreferenceLabels: Record<string, string> = {
  ship_hoppa_broker: 'Ship Hoppa broker',
  importer_broker: 'Your own broker',
  undecided: 'Not chosen yet',
}

const incotermLabels: Record<string, string> = {
  FOB: 'Supplier gets goods to the origin port',
  EXW: 'Pickup from supplier premises',
  CIF: 'Supplier includes freight and insurance',
  CFR: 'Supplier includes freight to destination port',
}

const invoiceSourceLabels: Record<string, string> = {
  freight_share: 'Container share',
  platform_fee: 'Platform fee',
  urgency_fee: 'Priority handling',
  ship_hoppa_service_fee_standard: 'Standard timing - 7+ business days before cutoff',
  ship_hoppa_service_fee_priority: 'Priority timing - 3-6 business days before cutoff',
  ship_hoppa_service_fee_rush: 'Rush timing - 0-2 business days before cutoff',
  pickup_fee: 'Pickup',
  customs_brokerage: 'Customs estimate',
  destination_charge: 'Destination estimate',
}

const releaseHoldLabels: Record<string, string> = {
  unpaid_invoice: 'Payment still open',
  missing_documents: 'Documents still needed',
  customs_hold: 'Customs not cleared',
  warehouse_variance: 'Warehouse check needed',
  admin_hold: 'Team review needed',
}

const trackingStageLabels: Record<TrackingStage, string> = {
  booking_submitted: 'Booking received',
  booking_confirmed: 'Booking confirmed',
  pickup_scheduled: 'Pickup booked',
  picked_up: 'Picked up',
  warehouse_received: 'At Ship Hoppa warehouse',
  measured: 'Measured',
  variance_approved: 'Ready to load',
  loaded: 'Loaded into container',
  container_committed: 'Container locked in',
  departed: 'At sea',
  transshipped: 'Changing vessel',
  arrived: 'Arrived at destination port',
  customs_cleared: 'Customs cleared',
  freight_released: 'Released',
  delivered: 'Delivered',
}

const trackingStageProgress: Record<TrackingStage, number> = {
  booking_submitted: 6,
  booking_confirmed: 12,
  pickup_scheduled: 18,
  picked_up: 26,
  warehouse_received: 34,
  measured: 40,
  variance_approved: 46,
  loaded: 52,
  container_committed: 58,
  departed: 68,
  transshipped: 78,
  arrived: 88,
  customs_cleared: 93,
  freight_released: 97,
  delivered: 100,
}

const locationCoordinates: Record<string, MapPoint> = {
  brisbane: { lat: -27.3811, lng: 153.1674 },
  sydney: { lat: -33.8688, lng: 151.2093 },
  melbourne: { lat: -37.8136, lng: 144.9631 },
  foshan: { lat: 23.0215, lng: 113.1214 },
  guangzhou: { lat: 23.1291, lng: 113.2644 },
  dongguan: { lat: 23.0207, lng: 113.7518 },
  shenzhen: { lat: 22.5431, lng: 114.0579 },
  yantian: { lat: 22.5949, lng: 114.2767 },
  shekou: { lat: 22.4846, lng: 113.9129 },
  nansha: { lat: 22.8016, lng: 113.5255 },
  zhongshan: { lat: 22.5176, lng: 113.3928 },
  yiwu: { lat: 29.3069, lng: 120.0753 },
  ningbo: { lat: 29.8683, lng: 121.544 },
  shanghai: { lat: 31.2304, lng: 121.4737 },
  xiamen: { lat: 24.4798, lng: 118.0894 },
  qingdao: { lat: 36.0671, lng: 120.3826 },
  'hong kong': { lat: 22.308, lng: 114.225 },
  singapore: { lat: 1.2655, lng: 103.8409 },
  'port klang': { lat: 2.9994, lng: 101.3928 },
  'tanjung pelepas': { lat: 1.362, lng: 103.548 },
  'ho chi minh': { lat: 10.7769, lng: 106.7009 },
  'laem chabang': { lat: 13.0827, lng: 100.883 },
  jakarta: { lat: -6.1045, lng: 106.886 },
  dubai: { lat: 24.9857, lng: 55.0273 },
  'jebel ali': { lat: 24.9857, lng: 55.0273 },
  rotterdam: { lat: 51.948, lng: 4.142 },
  hamburg: { lat: 53.5461, lng: 9.9661 },
  felixstowe: { lat: 51.956, lng: 1.351 },
  antwerp: { lat: 51.2636, lng: 4.4011 },
  valencia: { lat: 39.4483, lng: -0.3167 },
  'los angeles': { lat: 33.7361, lng: -118.2639 },
  'long beach': { lat: 33.7542, lng: -118.2165 },
  oakland: { lat: 37.7955, lng: -122.2802 },
  'new york': { lat: 40.6681, lng: -74.0451 },
  newark: { lat: 40.684, lng: -74.148 },
  savannah: { lat: 32.1286, lng: -81.1518 },
  miami: { lat: 25.7781, lng: -80.1794 },
}

function formatBiosecurityFlags(flags: string[] | undefined) {
  if (!flags?.length) return 'No special border checks flagged yet'
  return flags.map((flag) => biosecurityFlagLabels[flag] ?? sourceLabel(flag)).join(', ')
}

function formatCustomsStatus(value: string | null | undefined) {
  return value ? customsStatusLabels[value] ?? sourceLabel(value) : 'Details still needed'
}

function customsStatusDescription(value: string | null | undefined) {
  return value ? customsStatusHelp[value] ?? 'We will show the next customs step here as the broker updates the file.' : customsStatusHelp.documents_required
}

function formatBrokerPreference(value: string | null | undefined) {
  return value ? brokerPreferenceLabels[value] ?? sourceLabel(value) : 'Not chosen yet'
}

function formatIncoterm(value: string | null | undefined) {
  return value ? incotermLabels[value] ?? value : 'Not confirmed yet'
}

function formatInvoiceSource(value: string) {
  return invoiceSourceLabels[value] ?? sourceLabel(value)
}

function integrationIcon(provider: AccountIntegrationProvider) {
  if (provider === 'alibaba') return <ArrowRight size={18} />
  if (provider === 'email_inbox') return <FileText size={18} />
  if (provider === 'accounting') return <Receipt size={18} />
  if (provider === 'supplier_pay') return <CircleDollarSign size={18} />
  return <ShieldCheck size={18} />
}

function integrationStatusClass(status: string) {
  if (status === 'connected') return 'green'
  if (status === 'needs_attention') return 'orange'
  if (status === 'coming_soon') return 'blue'
  return 'orange'
}

function serviceFeeCategory(urgencyFee: number | null | undefined) {
  if ((urgencyFee ?? 0) >= 150) return 'Rush - 0-2 business days before cutoff'
  if ((urgencyFee ?? 0) > 0) return 'Priority - 3-6 business days before cutoff'
  return 'Standard - 7+ business days before cutoff'
}

function serviceFeeTotal(booking: Booking) {
  return (booking.platform_fee_usd ?? 0) + booking.urgency_fee_usd
}

function formatReleaseHold(value: string) {
  return releaseHoldLabels[value] ?? sourceLabel(value)
}

function sourceLabel(value: string | null | undefined) {
  const label = value ? value.replaceAll('_', ' ') : 'estimated'
  return label.replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function parseDate(value: string | null | undefined) {
  if (!value) return null
  const parsed = new Date(`${value.slice(0, 10)}T00:00:00`)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

function daysUntil(value: string | null | undefined) {
  const target = parseDate(value)
  if (!target) return 'ETA not confirmed'
  const todayMidday = new Date()
  todayMidday.setHours(12, 0, 0, 0)
  const diff = Math.ceil((target.getTime() - todayMidday.getTime()) / 86_400_000)
  if (diff < 0) return `${Math.abs(diff)} days ago`
  if (diff === 0) return 'Today'
  if (diff === 1) return 'Tomorrow'
  return `${diff} days away`
}

function locationLabel(location: SupplierLocation) {
  return `${location.city}, ${location.province}, ${location.country}`
}

function Logo() {
  return (
    <div className="logo" aria-label="Ship Hoppa">
      <span className="logo-wordmark">
        <strong>Ship</strong>
        <span>Hoppa</span>
      </span>
    </div>
  )
}

function CapacityBar({
  label,
  value,
  detail,
}: {
  label: string
  value: number
  detail: string
}) {
  const pct = Math.min(100, Math.max(0, value * 100))
  return (
    <div className="capacity">
      <div className="capacity-row">
        <span>{label}</span>
        <strong>{formatPercent(value)}</strong>
      </div>
      <div className="bar" aria-label={`${label} ${formatPercent(value)}`}>
        <span style={{ width: `${pct}%` }} />
      </div>
      <small>{detail}</small>
    </div>
  )
}

function BookingUsageLedger({
  heading,
  totalLabel,
  total,
  bookedAfter,
  shipment,
  remainingAfter,
  unit,
  ariaLabel,
}: {
  heading: string
  totalLabel: string
  total: number
  bookedAfter: number
  shipment: number
  remainingAfter: number
  unit: 'CBM' | 'kg'
  ariaLabel: string
}) {
  const bookedAfterValue = Math.max(0, bookedAfter)
  const shipmentValue = Math.max(0, shipment)
  const bookedBefore = Math.max(0, bookedAfterValue - shipmentValue)
  const addedValue = Math.max(0, bookedAfterValue - bookedBefore)
  const remainingValue = Math.max(0, remainingAfter)
  const availableBeforeBooking = Math.min(1, Math.max(0, (total - bookedBefore) / total))
  const beforePct = Math.min(100, (bookedBefore / total) * 100)
  const shipmentPct = Math.min(100, (addedValue / total) * 100)
  const remainingPct = Math.min(100, (remainingValue / total) * 100)

  return (
    <div className="capacity-ledger">
      <div className="capacity-ledger-head">
        <div>
          <small>{heading}</small>
          <strong>{formatMeasure(remainingValue, unit)} available after this booking</strong>
        </div>
        <span>{formatPercent(availableBeforeBooking)} available</span>
      </div>

      <div className="capacity-line">
        <div className="capacity-stack-bar" aria-label={ariaLabel}>
          <span className="booked-before" style={{ width: `${beforePct}%` }} />
          <span className="your-booking" style={{ width: `${shipmentPct}%` }} />
          <span className="space-left" style={{ width: `${remainingPct}%` }} />
        </div>

        <div className="capacity-annotations">
          <span className="total-size">
            <i />
            <small>{totalLabel}</small>
            <b>{formatMeasure(total, unit)}</b>
          </span>
          <span className="currently-booked">
            <i />
            <small>Currently Booked</small>
            <b>{formatMeasure(bookedBefore, unit)}</b>
          </span>
          <span className="your-booking-note">
            <i />
            <small>Your Booking</small>
            <b>+{formatMeasure(addedValue, unit)}</b>
          </span>
          <span className="total-booking">
            <i />
            <small>Total Booking</small>
            <b>{formatMeasure(bookedAfterValue, unit)}</b>
          </span>
        </div>
      </div>
    </div>
  )
}

function BookingCapacityLedger({ booking, container }: { booking: Booking; container: Container }) {
  return (
    <BookingUsageLedger
      heading="Container space"
      totalLabel="Total Size"
      total={CONTAINER_CBM_LIMIT}
      bookedAfter={container.current_cbm}
      shipment={booking.cbm_estimate}
      remainingAfter={container.remaining_cbm}
      unit="CBM"
      ariaLabel="Container space before, this booking, and available space"
    />
  )
}

function BookingWeightLedger({ booking, container }: { booking: Booking; container: Container }) {
  return (
    <BookingUsageLedger
      heading="Container weight"
      totalLabel="Total Weight"
      total={CONTAINER_WEIGHT_LIMIT_KG}
      bookedAfter={container.current_weight_kg}
      shipment={booking.weight_kg_estimate}
      remainingAfter={container.remaining_weight_kg}
      unit="kg"
      ariaLabel="Container weight before, this booking, and available weight"
    />
  )
}

function ContainerLoadLedger({
  heading,
  totalLabel,
  bookedLabel,
  remainingLabel,
  total,
  booked,
  remaining,
  unit,
  ariaLabel,
}: {
  heading: string
  totalLabel: string
  bookedLabel: string
  remainingLabel: string
  total: number
  booked: number
  remaining: number
  unit: 'CBM' | 'kg'
  ariaLabel: string
}) {
  const bookedValue = Math.max(0, booked)
  const remainingValue = Math.max(0, remaining)
  const availablePct = Math.min(1, Math.max(0, remainingValue / total))
  const bookedPct = Math.min(100, (bookedValue / total) * 100)
  const remainingPct = Math.min(100, (remainingValue / total) * 100)

  return (
    <div className="capacity-ledger ops-container-ledger">
      <div className="capacity-ledger-head">
        <div>
          <small>{heading}</small>
          <strong>{formatMeasure(remainingValue, unit)} still available</strong>
        </div>
        <span>{formatPercent(availablePct)} available</span>
      </div>

      <div className="capacity-line">
        <div className="capacity-stack-bar" aria-label={ariaLabel}>
          <span className="booked-before" style={{ width: `${bookedPct}%` }} />
          <span className="space-left" style={{ width: `${remainingPct}%` }} />
        </div>

        <div className="capacity-annotations">
          <span className="total-size">
            <i />
            <small>{totalLabel}</small>
            <b>{formatMeasure(total, unit)}</b>
          </span>
          <span className="currently-booked">
            <i />
            <small>{bookedLabel}</small>
            <b>{formatMeasure(bookedValue, unit)}</b>
          </span>
          <span className="space-available-note">
            <i />
            <small>{remainingLabel}</small>
            <b>{formatMeasure(remainingValue, unit)}</b>
          </span>
        </div>
      </div>
    </div>
  )
}

function phaseIcon(phaseId: CustomerPhaseId) {
  if (phaseId === 'order') return <ClipboardCheck size={22} />
  if (phaseId === 'ship') return <Ship size={22} />
  if (phaseId === 'clear') return <ShieldCheck size={22} />
  return <UserRound size={22} />
}

function phaseCopy(phaseId: CustomerPhaseId) {
  if (phaseId === 'order') {
    return {
      eyebrow: 'Phase 1',
      title: 'Buy the stock and prove it is ready.',
      summary: 'Supplier, marketplace intake, production, inspection, supplier invoice/payment, and commercial proof stay together here.',
    }
  }
  if (phaseId === 'ship') {
    return {
      eyebrow: 'Phase 2',
      title: 'Move the cargo and protect the sailing.',
      summary: 'Cargo details, movement documents, pickup handoff, container matching, sailing selection, and tracking live here.',
    }
  }
  if (phaseId === 'clear') {
    return {
      eyebrow: 'Phase 3',
      title: 'Clear the border and finish delivery.',
      summary: 'Customs, duties, Ship Hoppa invoice, release checks, destination charges, and final delivery are handled here.',
    }
  }
  return {
    eyebrow: 'Account',
    title: 'Saved details for faster bookings.',
    summary: 'Company, delivery, and supplier defaults reduce repeated typing across every shipment.',
  }
}

function viewIntroCopy(view: View, phase: CustomerPhase) {
  const copy: Record<View, { title: string; summary: string }> = {
    supplier: {
      title: 'Supplier and order source.',
      summary: 'Capture who the supplier is, where the order came from, and how Ship Hoppa should collect missing order details.',
    },
    production: {
      title: 'Production progress.',
      summary: 'Track the purchase order, factory milestones, ready date, production delays, and approvals before the cargo can move.',
    },
    inspection: {
      title: 'Inspection and quality control.',
      summary: 'Confirm supplier photos, third-party inspection needs, defects, and buyer approval before release to shipping.',
    },
    supplier_pay: {
      title: 'Supplier invoice and payment.',
      summary: 'Track deposit, balance, FX/payment options, approvals, and outside-app payment without mixing it with Ship Hoppa freight invoices.',
    },
    order_docs: {
      title: 'Commercial proof and product files.',
      summary: 'Store the documents that prove what was bought and produced: invoice, product specs, supplier photos, and factory certificates.',
    },
    book: {
      title: 'Cargo and container matching.',
      summary: 'Enter carton, dimension, weight, and delivery details so Ship Hoppa can find feasible container space.',
    },
    ship_docs: {
      title: 'Shipping documents.',
      summary: 'Collect the files that move with the cargo: packing list, shipping instructions, ISPM evidence, BL, arrival notice, and delivery order.',
    },
    handoff: {
      title: 'Pickup and origin handoff.',
      summary: 'Plan how the cargo gets from supplier to Ship Hoppa before the warehouse cutoff and sailing deadline.',
    },
    sailings: {
      title: 'Sailing options.',
      summary: 'Browse origin, destination, carrier, ETD, ETA, cutoff, and available capacity before choosing a route.',
    },
    tracking: {
      title: 'Tracking and ETA.',
      summary: 'Choose an order and see its route, current status, completed milestones, map position, and expected arrival.',
    },
    customs: {
      title: 'Customs and border charges.',
      summary: 'Keep HS code, goods value, incoterm, duty, GST/tax, broker handoff, and biosecurity checks understandable.',
    },
    money: {
      title: 'Ship Hoppa invoice and release.',
      summary: 'Show freight, service fees, pickup, customs, destination charges, payment status, and release blockers clearly.',
    },
    delivery: {
      title: 'Final delivery.',
      summary: 'Prepare destination delivery only when customs, documents, payment, and release holds are clear.',
    },
    profile: {
      title: 'Saved account details.',
      summary: 'Store company, contact, delivery, supplier, and approval defaults so new imports do not start from a blank form.',
    },
    integrations: {
      title: 'Account integrations.',
      summary: 'Connect Alibaba, email inboxes, accounting, payments, and other reusable systems only when they improve the workflow.',
    },
    help: {
      title: 'Help and handoffs.',
      summary: 'See what Ship Hoppa automates, what the supplier needs to do, and what is waiting on the importer.',
    },
    inbox: {
      title: 'Inbox.',
      summary: 'Forwarded supplier emails, partner updates, and uploaded source documents with extraction status.',
    },
    notifications: {
      title: 'Notifications.',
      summary: 'Recent activity, automation events, and updates that need your attention.',
    },
    admin: {
      title: 'Admin.',
      summary: 'Internal operations controls.',
    },
  }
  return {
    eyebrow: `${phase.label} / ${phase.views.find((item) => item.view === view)?.label ?? sourceLabel(view)}`,
    ...copy[view],
  }
}

function PhaseOverview({
  phase,
  activeView,
  items,
  onOpen,
}: {
  phase: CustomerPhase
  activeView: View
  items: PhaseOverviewItem[]
  onOpen: (view: View) => void
}) {
  const copy = phaseCopy(phase.id)
  return (
    <section className={`phase-overview phase-overview-${phase.id}`} aria-label={`${phase.label} phase overview`}>
      <div className="phase-overview-main">
        <span className="phase-overview-icon">{phaseIcon(phase.id)}</span>
        <div>
          <p className="eyebrow">{copy.eyebrow}</p>
          <h2>{copy.title}</h2>
          <p>{copy.summary}</p>
        </div>
      </div>
      <div className="phase-step-grid">
        {items.map((item) => {
          const isActive = item.active ?? item.view === activeView
          return (
            <button
              className={`phase-step-card ${item.status} ${isActive ? 'active' : ''}`}
              key={`${phase.id}-${item.title}`}
              type="button"
              onClick={() => onOpen(item.view)}
            >
              <span className="phase-step-icon">{item.icon}</span>
              <span className="phase-step-copy">
                <strong>{item.title}</strong>
                <small>{item.detail}</small>
                <em>{item.meta}</em>
              </span>
              <span className={`phase-step-status ${item.status}`}>{item.statusLabel}</span>
              <ChevronRight size={16} />
            </button>
          )
        })}
      </div>
    </section>
  )
}

function placeCode(place: string | null | undefined, fallback: string) {
  const normalized = (place ?? '').toLowerCase()
  if (normalized.includes('china') || normalized.includes('foshan') || normalized.includes('guangzhou') || normalized.includes('shenzhen')) return 'CN'
  if (normalized.includes('australia') || normalized.includes('brisbane') || normalized.includes('sydney') || normalized.includes('melbourne')) return 'AU'
  if (normalized.includes('united states') || normalized.includes('los angeles') || normalized.includes('new york')) return 'US'
  if (normalized.includes('vietnam')) return 'VN'
  if (normalized.includes('india') || normalized.includes('mumbai')) return 'IN'
  if (normalized.includes('singapore')) return 'SG'
  if (normalized.includes('dubai') || normalized.includes('uae')) return 'AE'
  if (normalized.includes('rotterdam') || normalized.includes('netherlands')) return 'NL'
  return fallback
}

function RouteVisual({ origin = 'Origin port', destination = 'Destination port' }: { origin?: string; destination?: string }) {
  return (
    <div className="route-visual" aria-label={`${origin} to ${destination}`}>
      <div className="route-port">
        <span>{placeCode(origin, 'OR')}</span>
        <strong>{origin}</strong>
      </div>
      <div className="route-track" aria-hidden="true">
        <span />
        <Ship size={19} />
      </div>
      <div className="route-port destination">
        <span>{placeCode(destination, 'DE')}</span>
        <strong>{destination}</strong>
      </div>
    </div>
  )
}

function sailingOriginPort(sailing: SailingSearchResult | null | undefined) {
  if (sailing?.departure_port) return sailing.departure_port
  if (sailing?.lane_id.includes('SCN')) return 'South China'
  return 'Origin port'
}

function sailingDestinationPort(sailing: SailingSearchResult | null | undefined) {
  if (sailing?.arrival_port) return sailing.arrival_port
  if (sailing?.lane_id.includes('BNE')) return 'Brisbane'
  return 'Destination port'
}

function sailingForContainer(container: Container | null, sailingOptions: SailingSearchResult[]) {
  if (!container) return null
  return (
    sailingOptions.find((sailing) => sailing.sailing_option_id === container.sailing_option_id) ??
    sailingOptions.find((sailing) => sailing.etd === container.target_sailing_date) ??
    null
  )
}

function coordinateFor(...labels: (string | null | undefined)[]) {
  for (const label of labels) {
    const normalized = (label ?? '').toLowerCase()
    const directMatch = locationCoordinates[normalized]
    if (directMatch) return directMatch
    const partialMatch = Object.entries(locationCoordinates).find(([key]) => normalized.includes(key))
    if (partialMatch) return partialMatch[1]
  }
  return locationCoordinates.brisbane
}

const MAP_TILE_SIZE = 256
const JOURNEY_MAP_ZOOM = 4

function isEastAsiaToAustralia(origin: MapPoint, destination: MapPoint) {
  return origin.lng >= 105 && origin.lng <= 126 && origin.lat >= 15 && origin.lat <= 35 && destination.lng >= 140 && destination.lng <= 160 && destination.lat <= -10
}

function shippingRouteCoordinates(origin: MapPoint, destination: MapPoint): MapPoint[] {
  if (isEastAsiaToAustralia(origin, destination)) {
    return [
      origin,
      { lat: 22.35, lng: 114.75 },
      { lat: 21.9, lng: 117.0 },
      { lat: 21.6, lng: 120.5 },
      { lat: 20.0, lng: 123.5 },
      { lat: 14.5, lng: 127.5 },
      { lat: 7.2, lng: 132.8 },
      { lat: 1.5, lng: 143.8 },
      { lat: -1.2, lng: 153.0 },
      { lat: -9.5, lng: 162.5 },
      { lat: -18.8, lng: 160.2 },
      { lat: -25.0, lng: 155.1 },
      destination,
    ]
  }

  if (isEastAsiaToAustralia(destination, origin)) {
    return shippingRouteCoordinates(destination, origin).reverse()
  }

  return [origin, destination]
}

function routeCoordinatesForShipment(
  origin: MapPoint,
  destination: MapPoint,
  container: Container | null,
  sailing: SailingSearchResult | null,
) {
  const storedRoute =
    container?.route_waypoints && container.route_waypoints.length >= 2
      ? container.route_waypoints
      : sailing?.route_waypoints && sailing.route_waypoints.length >= 2
        ? sailing.route_waypoints
        : null

  return storedRoute ?? shippingRouteCoordinates(origin, destination)
}

function unwrapRouteLongitudes(points: MapPoint[]): MapPoint[] {
  if (points.length <= 1) return points
  let previousLng = points[0].lng

  return points.map((point, index) => {
    if (index === 0) return { ...point }
    let lng = point.lng
    while (lng - previousLng > 180) lng -= 360
    while (lng - previousLng < -180) lng += 360
    previousLng = lng
    return { ...point, lng }
  })
}

function mercatorPixel(point: MapPoint, zoom: number): MapPlotPoint {
  const worldSize = MAP_TILE_SIZE * 2 ** zoom
  const clippedLatitude = Math.max(-85.05112878, Math.min(85.05112878, point.lat))
  const sinLatitude = Math.sin((clippedLatitude * Math.PI) / 180)

  return {
    x: ((point.lng + 180) / 360) * worldSize,
    y: (0.5 - Math.log((1 + sinLatitude) / (1 - sinLatitude)) / (4 * Math.PI)) * worldSize,
  }
}

function routeTileViewport(points: MapPoint[]): TileMapViewport {
  const pixelPoints = points.map((point) => mercatorPixel(point, JOURNEY_MAP_ZOOM))
  const xValues = pixelPoints.map((point) => point.x)
  const yValues = pixelPoints.map((point) => point.y)
  const minX = Math.min(...xValues)
  const maxX = Math.max(...xValues)
  const minY = Math.min(...yValues)
  const maxY = Math.max(...yValues)
  const worldSize = MAP_TILE_SIZE * 2 ** JOURNEY_MAP_ZOOM
  const xPadding = Math.max(260, (maxX - minX) * 0.26)
  const yPadding = Math.max(210, (maxY - minY) * 0.2)
  const yMin = Math.max(0, minY - yPadding)
  const yMax = Math.min(worldSize, maxY + yPadding)

  return {
    zoom: JOURNEY_MAP_ZOOM,
    xMin: minX - xPadding,
    xMax: maxX + xPadding,
    yMin,
    yMax,
  }
}

function tileViewportPoint(point: MapPoint, viewport: TileMapViewport): MapPlotPoint {
  const pixel = mercatorPixel(point, viewport.zoom)

  return {
    x: ((pixel.x - viewport.xMin) / (viewport.xMax - viewport.xMin)) * 100,
    y: ((pixel.y - viewport.yMin) / (viewport.yMax - viewport.yMin)) * 100,
  }
}

function mapTilesForViewport(viewport: TileMapViewport): MapTile[] {
  const tileCount = 2 ** viewport.zoom
  const xStart = Math.floor(viewport.xMin / MAP_TILE_SIZE)
  const xEnd = Math.floor(viewport.xMax / MAP_TILE_SIZE)
  const yStart = Math.max(0, Math.floor(viewport.yMin / MAP_TILE_SIZE))
  const yEnd = Math.min(tileCount - 1, Math.floor(viewport.yMax / MAP_TILE_SIZE))
  const tiles: MapTile[] = []

  for (let y = yStart; y <= yEnd; y += 1) {
    for (let x = xStart; x <= xEnd; x += 1) {
      tiles.push({ x, y, z: viewport.zoom })
    }
  }

  return tiles
}

function wrappedTileX(x: number, zoom: number) {
  const tileCount = 2 ** zoom
  return ((x % tileCount) + tileCount) % tileCount
}

function mapTileStyle(tile: MapTile, viewport: TileMapViewport) {
  const width = viewport.xMax - viewport.xMin
  const height = viewport.yMax - viewport.yMin

  return {
    left: `${(((tile.x * MAP_TILE_SIZE) - viewport.xMin) / width) * 100}%`,
    top: `${(((tile.y * MAP_TILE_SIZE) - viewport.yMin) / height) * 100}%`,
    width: `${(MAP_TILE_SIZE / width) * 100}%`,
    height: `${(MAP_TILE_SIZE / height) * 100}%`,
  }
}

function routePathFromPoints(points: MapPlotPoint[]) {
  const [start, ...rest] = points
  return `M ${start.x} ${start.y} ${rest.map((point) => `L ${point.x} ${point.y}`).join(' ')}`
}

function pointAlongRoute(points: MapPlotPoint[], t: number) {
  const segments = points.slice(1).map((point, index) => ({
    start: points[index],
    end: point,
    length: Math.hypot(point.x - points[index].x, point.y - points[index].y),
  }))
  const totalLength = segments.reduce((sum, segment) => sum + segment.length, 0)
  let target = totalLength * Math.min(1, Math.max(0, t))

  for (const segment of segments) {
    if (target <= segment.length) {
      const segmentT = segment.length === 0 ? 0 : target / segment.length
      return {
        x: segment.start.x + (segment.end.x - segment.start.x) * segmentT,
        y: segment.start.y + (segment.end.y - segment.start.y) * segmentT,
      }
    }
    target -= segment.length
  }

  return points[points.length - 1]
}

function labelHorizontalSide(point: MapPlotPoint, routeNeighbor?: MapPlotPoint) {
  if (!routeNeighbor) {
    if (point.x > 76) return 'left'
    if (point.x < 24) return 'right'
    return 'center'
  }

  if (point.x < 18) return 'right'
  if (point.x > 82) return 'left'

  return routeNeighbor.x >= point.x ? 'left' : 'right'
}

function portLabelStyle(point: MapPlotPoint, routeNeighbor?: MapPlotPoint) {
  const horizontalSide = labelHorizontalSide(point, routeNeighbor)
  const xOffset =
    horizontalSide === 'left' ? 'calc(-100% - 18px)' : horizontalSide === 'right' ? '18px' : '-50%'
  return {
    left: `${point.x}%`,
    top: `${point.y}%`,
    transform: `translate(${xOffset}, -50%)`,
  }
}

function portTextAlign(point: MapPlotPoint, routeNeighbor?: MapPlotPoint) {
  const horizontalSide = labelHorizontalSide(point, routeNeighbor)
  if (horizontalSide === 'left') return 'right'
  if (horizontalSide === 'right') return 'left'
  if (point.x > 76) return 'right'
  if (point.x < 24) return 'left'
  return 'center'
}

function eventProgress(eventList: ShipmentEvent[]) {
  return Math.max(0, ...eventList.map((event) => trackingStageProgress[event.stage] ?? 0))
}

function bookingStatusProgress(booking: Booking) {
  switch (booking.status) {
    case 'confirmed':
      return 18
    case 'at_warehouse':
      return 38
    case 'loaded':
      return 52
    case 'shipped':
      return 68
    case 'arrived':
      return 88
    case 'delivered':
      return 100
    case 'matched':
    case 'submitted':
      return 12
    default:
      return trackingStageProgress[booking.tracking_status] ?? 6
  }
}

function containerStatusProgress(container: Container | null) {
  switch (container?.status) {
    case 'filling':
      return 32
    case 'committed':
      return 58
    case 'loading':
      return 62
    case 'shipped':
      return 68
    case 'arrived':
      return 88
    case 'unpacked':
      return 94
    case 'open':
      return 12
    default:
      return 0
  }
}

function derivedShipmentProgress(booking: Booking, container: Container | null, eventList: ShipmentEvent[]) {
  return Math.max(eventProgress(eventList), bookingStatusProgress(booking), containerStatusProgress(container))
}

function currentTrackingStage(booking: Booking, eventList: ShipmentEvent[]) {
  const latestEvent = eventList[eventList.length - 1]?.stage
  if (latestEvent && (trackingStageProgress[latestEvent] ?? 0) >= (trackingStageProgress[booking.tracking_status] ?? 0)) {
    return latestEvent
  }
  return booking.tracking_status
}

function currentTrackingLabel(booking: Booking, container: Container | null, eventList: ShipmentEvent[]) {
  if (container?.status === 'filling' && derivedShipmentProgress(booking, container, eventList) >= 32) return 'Container filling'
  if (container?.status === 'committed') return 'Container locked in'
  if (container?.status === 'loading') return 'Loading container'
  if (container?.status === 'shipped') return 'At sea'
  if (container?.status === 'arrived') return 'Arrived at destination port'
  if (container?.status === 'unpacked') return 'Ready for delivery'
  return trackingStageLabels[currentTrackingStage(booking, eventList)]
}

function shipmentProgress(booking: Booking, container: Container | null, eventList: ShipmentEvent[]) {
  const stageProgress = derivedShipmentProgress(booking, container, eventList)
  const departure = parseDate(container?.estimated_departure ?? container?.target_sailing_date)
  const arrival = parseDate(container?.estimated_arrival)
  const now = new Date()

  if (departure && arrival && now >= departure && now <= arrival && stageProgress >= trackingStageProgress.departed) {
    const oceanPct = (now.getTime() - departure.getTime()) / (arrival.getTime() - departure.getTime())
    return Math.min(88, Math.max(stageProgress, 68 + oceanPct * 20))
  }

  return stageProgress
}

function shipmentRouteProgress(booking: Booking, container: Container | null, eventList: ShipmentEvent[]) {
  const operationalProgress = derivedShipmentProgress(booking, container, eventList)
  const departure = parseDate(container?.estimated_departure ?? container?.target_sailing_date)
  const arrival = parseDate(container?.estimated_arrival)
  const now = new Date()

  if (operationalProgress >= trackingStageProgress.arrived || container?.status === 'arrived' || container?.status === 'unpacked') {
    return 100
  }

  if (operationalProgress < trackingStageProgress.departed && container?.status !== 'shipped') {
    return 0
  }

  if (departure && arrival) {
    if (now <= departure) return 0
    if (now >= arrival) return 100
    const oceanPct = (now.getTime() - departure.getTime()) / (arrival.getTime() - departure.getTime())
    return Math.min(95, Math.max(5, oceanPct * 100))
  }

  if (operationalProgress >= trackingStageProgress.transshipped) return 62
  return 12
}

function shipmentUpdateSteps(booking: Booking, container: Container | null, eventList: ShipmentEvent[]) {
  const progress = shipmentProgress(booking, container, eventList)
  const eventByStage = new Map(eventList.map((event) => [event.stage, event]))
  const steps = [
    { label: 'Booking received', threshold: 6, eventStage: 'booking_submitted' as TrackingStage },
    { label: 'Booking confirmed', threshold: 12, eventStage: 'booking_confirmed' as TrackingStage },
    { label: 'Container filling', threshold: 32 },
    { label: 'Container locked in', threshold: 58, eventStage: 'container_committed' as TrackingStage },
    { label: 'At sea', threshold: 68, eventStage: 'departed' as TrackingStage },
    { label: 'Arrived at destination', threshold: 88, eventStage: 'arrived' as TrackingStage },
    { label: 'Delivered', threshold: 100, eventStage: 'delivered' as TrackingStage },
  ]

  return steps.map((step) => {
    const event = step.eventStage ? eventByStage.get(step.eventStage) : null
    const isCurrentFillingStep = step.label === 'Container filling' && container?.status === 'filling'
    return {
      ...step,
      done: progress >= step.threshold,
      meta:
        event?.occurred_at?.slice(0, 10) ??
        event?.estimated_at?.slice(0, 10) ??
        (isCurrentFillingStep ? 'Current status' : progress >= step.threshold ? 'Completed' : 'Next step'),
    }
  })
}

function DetailTile({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="detail-tile">
      <span>{icon}</span>
      <div>
        <small>{label}</small>
        <strong>{value}</strong>
      </div>
    </div>
  )
}

function invoiceLineTitle(label: string) {
  const serviceFeePrefix = 'Ship Hoppa service fee - '
  if (!label.startsWith(serviceFeePrefix)) return label
  const category = label.slice(serviceFeePrefix.length)
  return (
    <>
      Ship Hoppa service fee - <span className="invoice-service-tier">{category}</span>
    </>
  )
}

function InvoiceSheet({
  invoice,
  booking,
  actionLabel,
  loading,
  onPay,
}: {
  invoice: Invoice | null
  booking: Booking
  actionLabel: string
  loading: boolean
  onPay: () => void
}) {
  const lines = invoice?.line_items ?? []
  return (
    <article className="invoice-sheet">
      <div className="invoice-sheet-head">
        <div>
          <small>Invoice</small>
          <strong>{invoice?.id ?? 'Loading invoice'}</strong>
          <span>{booking.id} · due {formatDateShort(invoice?.due_date)}</span>
        </div>
        <span className={`status-chip ${invoice?.status === 'paid' ? 'green' : 'orange'}`}>
          {invoice ? sourceLabel(invoice.status) : 'Loading'}
        </span>
      </div>

      <div className="invoice-lines" aria-label="Invoice line items">
        <div className="invoice-row invoice-row-header">
          <span>Fee type</span>
          <span>Price</span>
        </div>
        {lines.length ? (
          lines.map((item) => (
            <div className="invoice-row" key={item.id}>
              <div className="invoice-line-label">
                <strong>{invoiceLineTitle(item.label)}</strong>
                <small>{formatInvoiceSource(item.source)}</small>
              </div>
              <b>{formatMoney(item.amount_usd)}</b>
            </div>
          ))
        ) : (
          <div className="invoice-row muted">
            <div className="invoice-line-label">
              <strong>Invoice loading</strong>
              <small>Line items will appear here.</small>
            </div>
            <b>TBC</b>
          </div>
        )}
      </div>

      <div className="invoice-totals" aria-label="Invoice totals">
        <div className="invoice-total-row">
          <span>Subtotal</span>
          <b>{formatMoney(invoice?.subtotal_usd)}</b>
        </div>
        <div className="invoice-total-row total">
          <span>Total due</span>
          <b>{formatMoney(invoice?.total_usd)}</b>
        </div>
      </div>

      <div className="invoice-sheet-foot">
        <p>Payment unlocks release once documents and customs checks are also clear.</p>
        <button className="primary-action small" type="button" onClick={onPay} disabled={loading || invoice?.status === 'paid'}>
          <Receipt size={15} />
          {actionLabel}
        </button>
      </div>
    </article>
  )
}

function TrackingOrderCard({
  booking,
  container,
  sailing,
  selected,
  pendingApprovalCount,
  onOpen,
}: {
  booking: Booking
  container: Container | null
  sailing: SailingSearchResult | null
  selected: boolean
  pendingApprovalCount?: number
  onOpen: (bookingId: string) => void
}) {
  const routeOrigin = sailing ? sailingOriginPort(sailing) : [booking.supplier_city, booking.supplier_country].filter(Boolean).join(', ')
  const routeDestination = sailing ? sailingDestinationPort(sailing) : [booking.delivery_city, booking.delivery_country].filter(Boolean).join(', ')

  return (
    <button className={`tracking-order-card ${selected ? 'selected' : ''}`} type="button" onClick={() => onOpen(booking.id)}>
      <div className="tracking-order-top">
        <span className={`status-chip ${booking.release_status === 'blocked' ? 'orange' : 'blue'}`}>
          {currentTrackingLabel(booking, container, [])}
        </span>
        <ChevronRight size={18} />
      </div>
      <strong>{booking.id}</strong>
      <span>{booking.cargo_description ?? sourceLabel(booking.cargo_category)}</span>
      <div className="tracking-order-route">
        <small>{routeOrigin}</small>
        <i />
        <small>{routeDestination}</small>
      </div>
      <small className="tracking-order-supplier">Supplier: {booking.supplier_city}</small>
      <div className="tracking-order-facts">
        <b>{formatMeasure(booking.cbm_estimate, 'CBM')}</b>
        <b>{booking.container_id ?? 'Awaiting container'}</b>
      </div>
      {pendingApprovalCount !== undefined && pendingApprovalCount > 0 && (
        <div className="tracking-order-attention">
          <span className="status-chip orange">
            {pendingApprovalCount} approval{pendingApprovalCount === 1 ? '' : 's'} waiting
          </span>
        </div>
      )}
    </button>
  )
}

function SpareSpacePanel({
  opportunities,
  onDetect,
  onList,
}: {
  opportunities: SpaceOpportunity[]
  onDetect: () => void
  onList: (opportunityId: string) => void
}) {
  const active = opportunities.find((o) => o.status === 'detected' || o.status === 'awaiting_owner_approval')
  const listed = opportunities.find((o) => o.status === 'listed')

  return (
    <section className="panel space-opportunity-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Spare container space</p>
          <h2>Recover unused FCL capacity</h2>
        </div>
        <PackageCheck size={22} />
      </div>
      {!active && !listed && (
        <div className="empty-state">
          <PackageCheck size={36} />
          <p>If this is an FCL shipment with spare room, Ship Hoppa can list the unused space for other importers without exposing your cargo details.</p>
          <button className="secondary-action" type="button" onClick={onDetect}>
            <PackageCheck size={15} />
            Check for spare space
          </button>
        </div>
      )}
      {active && (
        <div className="space-opportunity-card">
          <div className="space-opportunity-grid">
            <DetailTile icon={<PackageCheck size={18} />} label="Container size" value={`${active.total_container_cbm} CBM`} />
            <DetailTile icon={<Gauge size={18} />} label="Your cargo" value={`${active.booked_cbm} CBM`} />
            <DetailTile icon={<ShieldCheck size={18} />} label="Buffer" value={`${active.protected_buffer_cbm} CBM`} />
            <DetailTile icon={<CircleDollarSign size={18} />} label="Recoverable" value={`${active.recoverable_cbm} CBM`} />
            <DetailTile icon={<Receipt size={18} />} label="Estimated revenue" value={`USD ${active.estimated_recovery_usd.toLocaleString()}`} />
          </div>
          <p>
            Your cargo loads first and stays priority. Spare space only goes to compatible cargo that
            still meets the carrier cutoff.
          </p>
          <button
            className="primary-action"
            type="button"
            onClick={() => onList(active.id)}
          >
            <Check size={15} />
            List spare space
          </button>
        </div>
      )}
      {listed && !active && (
        <div className="space-opportunity-card listed">
          <span className="status-chip green">Listed</span>
          <h3>{listed.recoverable_cbm} CBM listed</h3>
          <p>Other importers can now see this listing in the spare-space marketplace. We will notify you when a match is confirmed.</p>
        </div>
      )}
    </section>
  )
}

function ShipmentJourneyMap({
  booking,
  container,
  events,
  sailing,
}: {
  booking: Booking
  container: Container | null
  events: ShipmentEvent[]
  sailing: SailingSearchResult | null
}) {
  const routeProgress = shipmentRouteProgress(booking, container, events)
  const origin = sailing ? sailingOriginPort(sailing) : [booking.supplier_city, booking.supplier_country].filter(Boolean).join(', ')
  const destination = sailing ? sailingDestinationPort(sailing) : [booking.delivery_city, booking.delivery_country].filter(Boolean).join(', ')
  const originCoordinate = coordinateFor(origin, booking.supplier_city, booking.supplier_country)
  const destinationCoordinate = coordinateFor(destination, booking.delivery_city, booking.delivery_country)
  const routeCoordinates = unwrapRouteLongitudes(routeCoordinatesForShipment(originCoordinate, destinationCoordinate, container, sailing))
  const viewport = routeTileViewport(routeCoordinates)
  const mapTiles = mapTilesForViewport(viewport)
  const originPoint = tileViewportPoint(routeCoordinates[0] ?? originCoordinate, viewport)
  const destinationPoint = tileViewportPoint(routeCoordinates[routeCoordinates.length - 1] ?? destinationCoordinate, viewport)
  const routePoints = routeCoordinates.map((point) => tileViewportPoint(point, viewport))
  const shipPoint = pointAlongRoute(routePoints, routeProgress / 100)
  const routePath = routePathFromPoints(routePoints)
  const originLabelNeighbor = routePoints[1] ?? destinationPoint
  const destinationLabelNeighbor = routePoints[routePoints.length - 2] ?? originPoint
  const labelForCurrentStage = currentTrackingLabel(booking, container, events)
  const eta = container?.estimated_arrival ?? sailing?.eta ?? null
  const updateSteps = shipmentUpdateSteps(booking, container, events)

  return (
    <article className="shipment-journey-card">
      <div className="journey-card-head">
        <div>
          <span className="status-chip blue">Selected order</span>
          <h3>{labelForCurrentStage}</h3>
          <p>
            {booking.id} · {container?.id ?? 'Container not assigned yet'}
          </p>
        </div>
        <div className="eta-card">
          <small>ETA</small>
          <strong>{formatDateFriendly(eta)}</strong>
          <span>{daysUntil(eta)}</span>
        </div>
      </div>

      <div className="journey-board">
        <div className="journey-map-stage" aria-label={`${booking.id} journey map`}>
          {mapTiles.map((tile) => (
            <img
              alt=""
              className="journey-map-tile"
              draggable="false"
              key={`${tile.z}-${tile.x}-${tile.y}`}
              src={`https://tile.openstreetmap.org/${tile.z}/${wrappedTileX(tile.x, tile.z)}/${tile.y}.png`}
              style={mapTileStyle(tile, viewport)}
            />
          ))}
          <div className="journey-map-tile-shade" />
          <svg className="journey-route-svg" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
            <path className="journey-route-shadow" d={routePath} />
            {routeProgress > 0 ? (
              <path className="journey-route-progress" d={routePath} pathLength={100} style={{ strokeDasharray: `${routeProgress} 100` }} />
            ) : null}
            <circle className="journey-port-dot origin-dot" cx={originPoint.x} cy={originPoint.y} r="1.8" />
            <circle className="journey-port-dot destination-dot" cx={destinationPoint.x} cy={destinationPoint.y} r="1.8" />
          </svg>
          <span className="journey-ship-marker" style={{ left: `${shipPoint.x}%`, top: `${shipPoint.y}%` }}>
            <Ship size={20} />
          </span>
          <div
            className="journey-port-label origin"
            style={{ ...portLabelStyle(originPoint, originLabelNeighbor), textAlign: portTextAlign(originPoint, originLabelNeighbor) }}
          >
            <small>Origin</small>
            <strong>{origin}</strong>
          </div>
          <div
            className="journey-port-label destination"
            style={{
              ...portLabelStyle(destinationPoint, destinationLabelNeighbor),
              textAlign: portTextAlign(destinationPoint, destinationLabelNeighbor),
            }}
          >
            <small>Destination</small>
            <strong>{destination}</strong>
          </div>
          <a className="journey-map-attribution" href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">
            © OpenStreetMap
          </a>
        </div>

        <aside className="journey-detail-panel">
          <div className="journey-detail-grid">
            <span>
              <small>Warehouse cutoff</small>
              <strong>{formatDateFriendly(booking.warehouse_receipt_cutoff)}</strong>
            </span>
            <span>
              <small>Sailing</small>
              <strong>{formatDateFriendly(container?.target_sailing_date ?? sailing?.etd)}</strong>
            </span>
            <span>
              <small>ETA</small>
              <strong>{formatDateFriendly(eta)}</strong>
            </span>
            <span>
              <small>Container</small>
              <strong>{container?.id ?? 'Not assigned'}</strong>
            </span>
          </div>

          <div className="journey-update-panel">
            <div className="section-subhead">
              <strong>Journey updates</strong>
              <span>{labelForCurrentStage}</span>
            </div>
            <ol className="journey-step-list">
              {updateSteps.map((step) => (
                <li key={step.label} className={step.done ? 'done' : ''}>
                  <span>{step.done ? <Check size={14} /> : null}</span>
                  <div>
                    <p>{step.label}</p>
                    <small>{step.meta}</small>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </aside>
      </div>
    </article>
  )
}

function SailingCard({
  sailing,
  selected,
  onSelect,
}: {
  sailing: SailingSearchResult
  selected: boolean
  onSelect: () => void
}) {
  return (
    <article className={`sailing-card ${selected ? 'selected' : ''}`}>
      <div className="option-ticket-header sailing-ticket-header">
        <div className="compact-option-top">
          <div>
            <span className="option-number">{selected ? 'Selected' : 'Sailing'}</span>
            <strong>{sailing.carrier_name}</strong>
          </div>
          <span className={`confidence-badge ${sailing.source_confidence}`}>{sourceLabel(sailing.source_confidence)}</span>
        </div>
        <div className="option-hero">
          <CalendarClock size={20} />
          <div>
            <small>Leaves origin</small>
            <strong>{formatDateFriendly(sailing.etd)}</strong>
          </div>
        </div>
      </div>

      <div className="option-ticket-body">
        <RouteVisual origin={sailingOriginPort(sailing)} destination={sailingDestinationPort(sailing)} />

        <div className="option-fact-grid">
          <span>
            <MapPin size={15} />
            <small>Warehouse deadline</small>
            <b>{formatDateFriendly(sailing.warehouse_receipt_cutoff_date)}</b>
          </span>
          <span>
            <Ship size={15} />
            <small>Arrives destination</small>
            <b>{formatDateFriendly(sailing.eta)}</b>
          </span>
          <span>
            <PackageCheck size={15} />
            <small>Space open</small>
            <b>{sailing.available_cbm} CBM</b>
          </span>
          <span>
            <Gauge size={15} />
            <small>Weight open</small>
            <b>{sailing.available_weight_kg.toLocaleString()} kg</b>
          </span>
        </div>

        <div className="sailing-bottom">
          <div className="capacity-pair">
            <CapacityBar
              label="CBM open"
              value={sailing.available_cbm / CONTAINER_CBM_LIMIT}
              detail={`${sailing.available_cbm} CBM available`}
            />
            <CapacityBar
              label="Weight open"
              value={sailing.available_weight_kg / CONTAINER_WEIGHT_LIMIT_KG}
              detail={`${sailing.available_weight_kg.toLocaleString()} kg available`}
            />
          </div>
          <button className={selected ? 'secondary-action small selected' : 'primary-action small'} type="button" onClick={onSelect}>
            {selected ? <Check size={16} /> : <ArrowRight size={16} />}
            {selected ? 'Selected' : 'Book this sailing'}
          </button>
        </div>
      </div>
    </article>
  )
}

function ContainerOpsPlan({ container }: { container: Container }) {
  return (
    <div className="container-plan-card">
      <div className="container-plan-header">
        <div>
          <span className={`confidence-badge ${container.sailing_source_confidence}`}>
            {sourceLabel(container.sailing_source_confidence)}
          </span>
          <strong>{container.carrier_name ?? 'Shared container sailing'}</strong>
        </div>
        <span className="shipper-pill">
          <Scale size={15} />
          {container.shipper_count} {container.shipper_count === 1 ? 'shipment' : 'shipments'}
        </span>
      </div>

      <div className="container-milestone-grid">
        <span className="container-milestone urgent">
          <MapPin size={17} />
          <small>Goods must reach our warehouse</small>
          <b>{formatDateFriendly(container.warehouse_receipt_cutoff_date)}</b>
          <em>Customer stock must be received by Ship Hoppa.</em>
        </span>
        <span className="container-milestone">
          <ClipboardCheck size={17} />
          <small>Container must reach port</small>
          <b>{formatDateFriendly(container.carrier_cutoff_date)}</b>
          <em>Ship Hoppa must get the loaded container to the shipping line.</em>
        </span>
        <span className="container-milestone">
          <Ship size={17} />
          <small>Leaves origin port</small>
          <b>{formatDateFriendly(container.target_sailing_date)}</b>
          <em>Target vessel departure.</em>
        </span>
      </div>

      <div className="source-note-card">
        <Gauge size={17} />
        <div>
          <small>Where this sailing date came from</small>
          <strong>{container.sailing_source_name}</strong>
          <span>
            {sourceLabel(container.sailing_source_confidence)} · Verified{' '}
            {formatDateShort(container.sailing_source_last_verified_at)}
          </span>
        </div>
      </div>
    </div>
  )
}

function shipmentRoute(shipmentBookings: Booking[]) {
  const firstBooking = shipmentBookings[0]
  if (!firstBooking) return { origin: 'Origin port', destination: 'Destination port' }
  return {
    origin: [firstBooking.supplier_city, firstBooking.supplier_country].filter(Boolean).join(', '),
    destination: [firstBooking.delivery_city, firstBooking.delivery_country].filter(Boolean).join(', '),
  }
}

function OpsSailingCard({
  container,
  shipmentBookings,
  options,
  loading,
  onLoadCarrierOptions,
  onCommit,
  onOpenBooking,
}: {
  container: Container
  shipmentBookings: Booking[]
  options: CarrierOption[]
  loading: boolean
  onLoadCarrierOptions: (containerId: string) => void
  onCommit: (container: Container, option?: CarrierOption) => void
  onOpenBooking: (bookingId: string) => void
}) {
  const route = shipmentRoute(shipmentBookings)

  return (
    <article className="ops-sailing-card">
      <div className="option-ticket-header ops-sailing-header">
        <div className="compact-option-top">
          <div>
            <span className="option-number">Shared container</span>
            <strong>{container.id}</strong>
          </div>
          <span className={`confidence-badge ${container.sailing_source_confidence}`}>
            {sourceLabel(container.sailing_source_confidence)}
          </span>
        </div>
        <div className="option-hero">
          <Ship size={20} />
          <div>
            <small>Leaves origin</small>
            <strong>{formatDateFriendly(container.target_sailing_date)}</strong>
          </div>
        </div>
      </div>

      <div className="ops-sailing-body">
        <RouteVisual origin={route.origin} destination={route.destination} />

        <div className="ops-card-explainer">
          <strong>What this card is</strong>
          <span>
            One planned Ship Hoppa shared container sailing. The shipment cards below are customer bookings already matched to this container.
          </span>
        </div>

        <ContainerOpsPlan container={container} />

        <div className="ops-load-grid">
          <ContainerLoadLedger
            heading="Container space"
            totalLabel="Total Container Size"
            bookedLabel="Already Booked"
            remainingLabel="Still Available"
            total={CONTAINER_CBM_LIMIT}
            booked={container.current_cbm}
            remaining={container.remaining_cbm}
            unit="CBM"
            ariaLabel="Container space booked and available"
          />
          <ContainerLoadLedger
            heading="Container weight"
            totalLabel="Total Weight Limit"
            bookedLabel="Already Booked"
            remainingLabel="Still Available"
            total={CONTAINER_WEIGHT_LIMIT_KG}
            booked={container.current_weight_kg}
            remaining={container.remaining_weight_kg}
            unit="kg"
            ariaLabel="Container weight booked and available"
          />
        </div>

        <div className="ops-card-section">
          <div className="section-subhead">
            <strong>Shipments in this sailing</strong>
            <span>{shipmentBookings.length} total</span>
          </div>
          <div className="ops-shipment-mini-grid">
            {shipmentBookings.length ? (
              shipmentBookings.slice(0, 5).map((booking) => (
                <button className="ops-shipment-mini" type="button" key={booking.id} onClick={() => onOpenBooking(booking.id)}>
                  <strong>{booking.id}</strong>
                  <span>{statusLabels[booking.feasibility_status ?? 'admin_review']}</span>
                  <small>
                    {formatQuantity(booking.cbm_estimate)} CBM · {formatQuantity(booking.weight_kg_estimate, 0)} kg
                  </small>
                </button>
              ))
            ) : (
              <div className="empty-mini-card">No shipments matched yet.</div>
            )}
          </div>
        </div>

        {container.carrier_name && (
          <div className="selected-carrier">
            <Ship size={17} />
            {container.carrier_name} selected · leaves {formatDateFriendly(container.estimated_departure)} · arrives{' '}
            {formatDateFriendly(container.estimated_arrival)}
          </div>
        )}

        <div className="ops-card-actions">
          <button className="secondary-action" onClick={() => onLoadCarrierOptions(container.id)}>
            <Ship size={16} />
            Check shipping options
          </button>
          <button className="secondary-action" onClick={() => onCommit(container)} disabled={loading || container.status === 'committed'}>
            <Check size={16} />
            Lock in sailing
          </button>
        </div>

        {options.length > 0 && (
          <div className="carrier-option-grid">
            {options.map((option) => (
              <article className="carrier-option-card" key={`${option.service_id}-${option.sailing_date}`}>
                <div>
                  <span className={`confidence-badge ${option.confidence}`}>{sourceLabel(option.confidence)}</span>
                  <strong>{option.carrier_name}</strong>
                  <small>{option.service_name}</small>
                </div>
                <div className="carrier-option-facts">
                  <span>
                    <small>Cost</small>
                    <b>{formatMoney(option.total_all_in_usd)}</b>
                  </span>
                  <span>
                    <small>Leaves</small>
                    <b>{formatDateShort(option.sailing_date)}</b>
                  </span>
                  <span>
                    <small>Port deadline</small>
                    <b>{formatDateShort(option.carrier_gate_in_cutoff_date)}</b>
                  </span>
                </div>
                <button
                  className="primary-action small"
                  onClick={() => onCommit(container, option)}
                  disabled={loading || container.status === 'committed'}
                >
                  Confirm option
                </button>
              </article>
            ))}
          </div>
        )}
      </div>
    </article>
  )
}

function OpsShipmentCard({
  booking,
  selected,
  onOpen,
}: {
  booking: Booking
  selected: boolean
  onOpen: (bookingId: string) => void
}) {
  return (
    <article className={`ops-shipment-card ${selected ? 'selected' : ''}`}>
      <div className="ops-shipment-card-head">
        <span className={`feasibility-pill ${booking.feasibility_status ?? 'admin_review'}`}>
          {statusLabels[booking.feasibility_status ?? 'admin_review']}
        </span>
        <button className="secondary-action small" type="button" onClick={() => onOpen(booking.id)}>
          Open work
        </button>
      </div>
      <strong>{booking.id}</strong>
      <p>{booking.cargo_description ?? sourceLabel(booking.cargo_category)}</p>
      <div className="ops-shipment-facts">
        <span>
          <small>Container</small>
          <b>{booking.container_id ?? 'Not assigned'}</b>
        </span>
        <span>
          <small>Cutoff</small>
          <b>{formatDateShort(booking.warehouse_receipt_cutoff)}</b>
        </span>
        <span>
          <small>Docs</small>
          <b>{sourceLabel(booking.checklist_status)}</b>
        </span>
        <span>
          <small>Delivery</small>
          <b>{sourceLabel(booking.release_status)}</b>
        </span>
      </div>
    </article>
  )
}

function OpsWorldMap({
  containers,
  bookings,
  onOpenBooking,
}: {
  containers: Container[]
  bookings: Booking[]
  onOpenBooking: (bookingId: string) => void
}) {
  const globalRoutes = [
    { x1: 76, y1: 40, x2: 82, y2: 76, arc: 12, name: 'Asia Pacific' },
    { x1: 70, y1: 52, x2: 84, y2: 78, arc: 9, name: 'Southeast Asia' },
    { x1: 60, y1: 46, x2: 54, y2: 40, arc: 7, name: 'Middle East' },
    { x1: 45, y1: 30, x2: 27, y2: 38, arc: 11, name: 'Europe' },
    { x1: 18, y1: 42, x2: 82, y2: 76, arc: 18, name: 'Trans-Pacific' },
  ]
  const vesselMarkers = [
    { left: 30, top: 46 },
    { left: 43, top: 38 },
    { left: 56, top: 44 },
    { left: 68, top: 50 },
    { left: 77, top: 62 },
    { left: 86, top: 74 },
  ]
  const mapPath = (route: (typeof globalRoutes)[number]) => {
    const x1 = route.x1 * 10
    const y1 = route.y1 * 5.2
    const x2 = route.x2 * 10
    const y2 = route.y2 * 5.2
    const midpointX = (x1 + x2) / 2
    const midpointY = (y1 + y2) / 2 - route.arc * 5.2
    return `M ${x1} ${y1} Q ${midpointX} ${midpointY} ${x2} ${y2}`
  }
  const totalShipments = containers.reduce(
    (total, container) => total + bookings.filter((booking) => booking.container_id === container.id).length,
    0,
  )

  return (
    <section className="ops-map-panel" aria-label="Ship Hoppa container map">
      <div className="ops-map-copy">
        <span className="status-chip blue">Map view</span>
        <h3>Global container watch</h3>
        <p>Small ship pins show active shared containers. The container cards are kept outside the map so the route view stays readable.</p>
      </div>

      <div className="ops-map-layout">
      <div className="ops-map-stage">
        <svg className="world-map-svg" viewBox="0 0 1000 520" role="img" aria-label="Global world map of Ship Hoppa shared containers">
          <defs>
            <linearGradient id="mapRouteGradient" x1="0%" x2="100%" y1="0%" y2="100%">
              <stop offset="0%" stopColor="#f0a06b" stopOpacity="0.35" />
              <stop offset="55%" stopColor="#f26a2e" stopOpacity="0.95" />
              <stop offset="100%" stopColor="#ffe2c7" stopOpacity="0.75" />
            </linearGradient>
            <filter id="routeGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          {[160, 260, 360, 460].map((y) => (
            <path className="map-grid-line" d={`M 70 ${y} H 930`} key={`lat-${y}`} />
          ))}
          {[160, 300, 440, 580, 720, 860].map((x) => (
            <path className="map-grid-line" d={`M ${x} 70 V 456`} key={`lng-${x}`} />
          ))}
          <image className="map-land-image" href="/world-land.svg" x="70" y="42" width="860" height="420" preserveAspectRatio="xMidYMid meet" />
          {globalRoutes.map((route, index) => (
            <path
              className={index < 2 ? 'ops-map-route' : 'ops-map-route secondary'}
              d={mapPath(route)}
              key={route.name}
            />
          ))}
          {globalRoutes.map((route) => (
            <g className="map-node" key={`${route.name}-node`}>
              <circle cx={route.x1 * 10} cy={route.y1 * 5.2} r="5" />
              <circle cx={route.x2 * 10} cy={route.y2 * 5.2} r="5" />
            </g>
          ))}
        </svg>

        <div className="map-region americas">Americas</div>
        <div className="map-region europe">Europe</div>
        <div className="map-region asia">Asia Pacific</div>

        <div className="map-network-stat">
          <small>Shared containers on map</small>
          <strong>{containers.length}</strong>
          <span>{totalShipments} customer shipments</span>
        </div>

        {containers.slice(0, 6).map((container, index) => {
          const shipmentBookings = bookings.filter((booking) => booking.container_id === container.id)
          const marker = vesselMarkers[index % vesselMarkers.length]
          const firstBooking = shipmentBookings[0]

          return (
            <button
              className="map-vessel-button"
              type="button"
              key={container.id}
              style={{ left: `${marker.left}%`, top: `${marker.top}%` }}
              onClick={() => firstBooking && onOpenBooking(firstBooking.id)}
              disabled={!firstBooking}
              aria-label={`Open ${container.id}`}
            >
              <Ship size={17} />
            </button>
          )
        })}
      </div>

        <div className="map-vessel-stack" aria-label="Active shared containers">
          <div className="map-vessel-stack-head">
            <small>Active shared containers</small>
            <strong>{containers.length}</strong>
          </div>
          {containers.slice(0, 6).map((container) => {
            const shipmentBookings = bookings.filter((booking) => booking.container_id === container.id)
            const firstBooking = shipmentBookings[0]
            return (
              <button
                className="map-vessel-card"
                type="button"
                key={container.id}
                onClick={() => firstBooking && onOpenBooking(firstBooking.id)}
                disabled={!firstBooking}
              >
                <span>
                  <Ship size={16} />
                </span>
                <div>
                  <strong>{container.id}</strong>
                  <small>{formatDateShort(container.target_sailing_date)} · {shipmentBookings.length} shipments</small>
                </div>
              </button>
            )
          })}
        </div>
      </div>
    </section>
  )
}

function parseNotification(message: string) {
  return {
    booking: message.match(/Booking ([A-Z]+-\d+)/)?.[1],
    container: message.match(/Container ([A-Z0-9-]+)/)?.[1],
    sailing: message.match(/sailing (\d{4}-\d{2}-\d{2})/i)?.[1],
    cutoff: message.match(/cutoff is (\d{4}-\d{2}-\d{2})/i)?.[1],
    readyBy: message.match(/ready by (\d{4}-\d{2}-\d{2})/i)?.[1],
    cost: message.match(/Cost: \$([0-9.]+)/i)?.[1],
    confirmBy: message.match(/Confirm within ([^.]+)/i)?.[1],
  }
}

function notificationTitle(trigger: string) {
  if (trigger.includes('booking_matched')) return 'Booking matched'
  if (trigger.includes('72h')) return 'Ready window'
  if (trigger.includes('24h')) return 'Final readiness check'
  if (trigger.includes('cutoff')) return 'Cutoff alert'
  return sourceLabel(trigger)
}

function NotificationCard({ notification }: { notification: DashboardSummary['notifications'][number] }) {
  const facts = parseNotification(notification.message)
  const factItems = [
    facts.booking ? ['Booking', facts.booking] : null,
    facts.container ? ['Container', facts.container] : null,
    facts.sailing ? ['Sailing', formatDateShort(facts.sailing)] : null,
    facts.cutoff ? ['Warehouse cutoff', formatDateShort(facts.cutoff)] : null,
    facts.readyBy ? ['Ready by', formatDateShort(facts.readyBy)] : null,
    facts.cost ? ['Cost', formatMoney(Number(facts.cost))] : null,
    facts.confirmBy ? ['Confirm', facts.confirmBy] : null,
  ].filter(Boolean) as [string, string][]

  return (
    <div className={`notification-card ${notification.trigger.includes('24h') ? 'urgent' : ''}`}>
      <div className="notification-icon">
        <Bell size={18} />
      </div>
      <div className="notification-main">
        <strong>{notificationTitle(notification.trigger)}</strong>
        {factItems.length ? (
          <div className="fact-grid">
            {factItems.map(([label, value]) => (
              <span className="fact-chip" key={`${notification.id}-${label}`}>
                <small>{label}</small>
                <b>{value}</b>
              </span>
            ))}
          </div>
        ) : (
          <p>{notification.message}</p>
        )}
      </div>
    </div>
  )
}

function bookingReviewReasons(booking: Booking) {
  const reasons: string[] = []
  if (booking.admin_review_required || booking.feasibility_status === 'admin_review') reasons.push('Needs team decision')
  if (booking.feasibility_status === 'misses_cutoff') reasons.push('Misses cutoff')
  if (booking.feasibility_status === 'tight') reasons.push('Tight cutoff')
  if (booking.checklist_status !== 'complete') reasons.push('Documents incomplete')
  if (booking.payment_status !== 'paid') reasons.push('Payment open')
  if (booking.release_status === 'blocked') reasons.push('Release blocked')
  if (booking.exception_count > 0) reasons.push(`${booking.exception_count} exception${booking.exception_count === 1 ? '' : 's'}`)
  return Array.from(new Set(reasons))
}

function needsAdminReview(booking: Booking) {
  return bookingReviewReasons(booking).length > 0
}

function supplierLocationInputValue(form: BookingPayload) {
  const matchedLocation = supplierLocations.find((location) => location.city.toLowerCase() === form.supplier_city.toLowerCase())
  if (matchedLocation) return locationLabel(matchedLocation)
  return [form.supplier_city, form.supplier_province, form.supplier_country].filter(Boolean).join(', ')
}

function brokerTokenFromPath(): string | null {
  const pathname = globalThis.location?.pathname ?? ''
  const match = pathname.match(/^\/broker\/([^/]+)\/?$/)
  return match ? match[1] : null
}

function warehouseTokenFromPath(): string | null {
  const pathname = globalThis.location?.pathname ?? ''
  const match = pathname.match(/^\/warehouse\/([^/]+)\/?$/)
  return match ? match[1] : null
}

function carrierTokenFromPath(): string | null {
  const pathname = globalThis.location?.pathname ?? ''
  const match = pathname.match(/^\/carrier\/([^/]+)\/?$/)
  return match ? match[1] : null
}

function truckerTokenFromPath(): string | null {
  const pathname = globalThis.location?.pathname ?? ''
  const match = pathname.match(/^\/trucker\/([^/]+)\/?$/)
  return match ? match[1] : null
}

function initialWorkspaceMode(): WorkspaceMode {
  if (brokerTokenFromPath()) return 'broker-portal'
  if (warehouseTokenFromPath()) return 'warehouse-portal'
  if (carrierTokenFromPath()) return 'carrier-portal'
  if (truckerTokenFromPath()) return 'trucker-portal'
  return globalThis.location?.pathname === '/admin' ? 'admin-login' : 'customer'
}

function setBrowserPath(path: string) {
  if (globalThis.location?.pathname !== path) {
    globalThis.history?.pushState({}, '', path)
  }
}

function BrokerPortalView({ token }: { token: string }) {
  const [portal, setPortal] = useState<BrokerPortalResponse | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [statusChoice, setStatusChoice] = useState<BrokerSubmittableStatus>('submitted')
  const [entryNumber, setEntryNumber] = useState('')
  const [dutyPaid, setDutyPaid] = useState('')
  const [gstPaid, setGstPaid] = useState('')
  const [notes, setNotes] = useState('')
  const [docFile, setDocFile] = useState('')
  const [docType, setDocType] = useState<DocumentType>('house_bill')
  const [docNotes, setDocNotes] = useState('')
  const [docSubmitting, setDocSubmitting] = useState(false)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)
  const [docMessage, setDocMessage] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getBrokerPortal(token)
      .then((data) => {
        if (cancelled) return
        setPortal(data)
        setStatusChoice(
          data.customs.customs_status === 'cleared' || data.customs.customs_status === 'queried' || data.customs.customs_status === 'submitted'
            ? (data.customs.customs_status as BrokerSubmittableStatus)
            : 'submitted',
        )
        setEntryNumber(data.customs.customs_entry_number ?? '')
        setNotes(data.customs.broker_notes ?? '')
        setDutyPaid(data.customs.duty_paid_usd != null ? String(data.customs.duty_paid_usd) : '')
        setGstPaid(data.customs.gst_paid_usd != null ? String(data.customs.gst_paid_usd) : '')
      })
      .catch((err: unknown) => {
        if (!cancelled) setLoadError(err instanceof Error ? err.message : 'Could not load broker portal')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [token])

  async function refreshPortal() {
    const data = await getBrokerPortal(token)
    setPortal(data)
    return data
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!portal) return
    if (statusChoice === 'queried' && !notes.trim()) {
      setStatusMessage('A note explaining the query is required when status is queried.')
      return
    }
    setSubmitting(true)
    setStatusMessage(null)
    try {
      const latest = await refreshPortal()
      if (latest.customs.updated_at !== portal.customs.updated_at) {
        setStatusMessage('The customs profile changed since you opened this page. Re-check the latest values, then submit again.')
        setSubmitting(false)
        return
      }
      const payload: BrokerClearanceUpdate = {
        customs_status: statusChoice,
        customs_entry_number: entryNumber.trim() || null,
        duty_paid_usd: dutyPaid ? Number(dutyPaid) : null,
        gst_paid_usd: gstPaid ? Number(gstPaid) : null,
        broker_notes: notes.trim() || null,
      }
      const updated = await submitBrokerClearance(token, payload)
      setPortal(updated)
      setStatusMessage(`Customs status set to ${statusChoice.replace('_', ' ')}.`)
    } catch (err) {
      setStatusMessage(err instanceof Error ? err.message : 'Could not save clearance update.')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDocUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!docFile.trim()) {
      setDocMessage('A file name is required before uploading.')
      return
    }
    setDocSubmitting(true)
    setDocMessage(null)
    try {
      await uploadBrokerDocument(token, docType, docFile.trim(), docNotes.trim() || undefined)
      const refreshed = await refreshPortal()
      setPortal(refreshed)
      setDocMessage(`${docFile} attached to the shipment.`)
      setDocFile('')
      setDocNotes('')
    } catch (err) {
      setDocMessage(err instanceof Error ? err.message : 'Could not upload the document.')
    } finally {
      setDocSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="app-shell broker-portal-shell">
        <header className="topbar">
          <Logo />
          <span className="eyebrow">Broker workspace</span>
        </header>
        <main className="broker-portal-main">
          <p>Loading shipment.</p>
        </main>
      </div>
    )
  }

  if (loadError || !portal) {
    return (
      <div className="app-shell broker-portal-shell">
        <header className="topbar">
          <Logo />
          <span className="eyebrow">Broker workspace</span>
        </header>
        <main className="broker-portal-main">
          <div className="notice error">{loadError ?? 'Broker link not found.'}</div>
        </main>
      </div>
    )
  }

  const { booking, customs, holds, documents, events } = portal

  return (
    <div className="app-shell broker-portal-shell">
      <header className="topbar broker-portal-topbar">
        <Logo />
        <span className="eyebrow">Broker workspace</span>
      </header>
      <main className="broker-portal-main">
        <section className="broker-portal-card">
          <p className="eyebrow">Shipment</p>
          <h1>{booking.id}</h1>
          <p className="broker-portal-subtitle">
            {booking.importer_company_name ?? 'Importer'} into {booking.delivery_city}, {booking.delivery_country}.
            Cargo from {booking.supplier_country}, ready by {booking.cargo_ready_date_latest}.
          </p>
          <div className="broker-portal-grid">
            <div>
              <p className="broker-portal-label">Importer</p>
              <p>{booking.importer_company_name ?? 'Not on file'}</p>
            </div>
            <div>
              <p className="broker-portal-label">Importer ABN / tax ID</p>
              <p>{booking.importer_abn ?? 'Not on file. Ask the importer.'}</p>
            </div>
            <div>
              <p className="broker-portal-label">HS code</p>
              <p>{customs.hs_code ?? 'Not yet classified.'}</p>
            </div>
            <div>
              <p className="broker-portal-label">Goods value</p>
              <p>
                {customs.currency} {customs.goods_value_usd.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="broker-portal-label">Incoterm</p>
              <p>{customs.incoterm}</p>
            </div>
            <div>
              <p className="broker-portal-label">Customs status</p>
              <p>{customs.customs_status.replace('_', ' ')}</p>
            </div>
            <div>
              <p className="broker-portal-label">Duty estimate</p>
              <p>USD {customs.duty_estimate_usd.toLocaleString()}</p>
            </div>
            <div>
              <p className="broker-portal-label">GST estimate</p>
              <p>USD {customs.gst_estimate_usd.toLocaleString()}</p>
            </div>
          </div>
          {customs.biosecurity_flags.length > 0 && (
            <p className="notice">
              <ShieldCheck size={16} /> Biosecurity flags: {customs.biosecurity_flags.join(', ')}
            </p>
          )}
        </section>

        <section className="broker-portal-card">
          <h2>Submit clearance update</h2>
          <form onSubmit={handleSubmit} className="broker-portal-form">
            <label>
              <span>Status</span>
              <select
                value={statusChoice}
                onChange={(event) => setStatusChoice(event.target.value as BrokerSubmittableStatus)}
              >
                <option value="submitted">Submitted to customs</option>
                <option value="queried">Queried by customs</option>
                <option value="cleared">Cleared</option>
              </select>
            </label>
            <label>
              <span>Customs entry number</span>
              <input
                value={entryNumber}
                onChange={(event) => setEntryNumber(event.target.value)}
                placeholder="e.g. E-123456"
              />
            </label>
            <label>
              <span>Duty paid (USD)</span>
              <input
                type="number"
                min="0"
                step="0.01"
                value={dutyPaid}
                onChange={(event) => setDutyPaid(event.target.value)}
              />
            </label>
            <label>
              <span>GST paid (USD)</span>
              <input
                type="number"
                min="0"
                step="0.01"
                value={gstPaid}
                onChange={(event) => setGstPaid(event.target.value)}
              />
            </label>
            <label className="broker-portal-textarea">
              <span>Broker notes {statusChoice === 'queried' && '(required for queries)'}</span>
              <textarea
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                rows={3}
              />
            </label>
            <button className="primary-action" type="submit" disabled={submitting}>
              {submitting ? <Loader2 size={16} className="spin" /> : <Check size={16} />}
              {submitting ? 'Saving' : 'Submit update'}
            </button>
          </form>
          {statusMessage && <div className="notice">{statusMessage}</div>}
        </section>

        <section className="broker-portal-card">
          <h2>Attach customs document</h2>
          <form onSubmit={handleDocUpload} className="broker-portal-form">
            <label>
              <span>Document type</span>
              <select value={docType} onChange={(event) => setDocType(event.target.value as DocumentType)}>
                <option value="house_bill">House bill of lading</option>
                <option value="commercial_invoice">Commercial invoice</option>
                <option value="packing_list">Packing list</option>
                <option value="arrival_notice">Arrival notice</option>
                <option value="delivery_order">Delivery order</option>
              </select>
            </label>
            <label>
              <span>File name</span>
              <input
                value={docFile}
                onChange={(event) => setDocFile(event.target.value)}
                placeholder="e.g. customs-decl-1234.pdf"
              />
            </label>
            <label className="broker-portal-textarea">
              <span>Notes</span>
              <textarea value={docNotes} onChange={(event) => setDocNotes(event.target.value)} rows={2} />
            </label>
            <button className="secondary-action" type="submit" disabled={docSubmitting}>
              {docSubmitting ? <Loader2 size={16} className="spin" /> : <FileText size={16} />}
              {docSubmitting ? 'Attaching' : 'Attach document'}
            </button>
          </form>
          {docMessage && <div className="notice">{docMessage}</div>}
        </section>

        <section className="broker-portal-card">
          <h2>Active holds</h2>
          {holds.length === 0 ? (
            <p>No release holds. Shipment can move when customs is cleared.</p>
          ) : (
            <ul className="broker-portal-list">
              {holds.map((hold) => (
                <li key={hold.id}>
                  <strong>{hold.hold_type.replace('_', ' ')}</strong>: {hold.reason}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="broker-portal-card">
          <h2>Recent documents</h2>
          {documents.length === 0 ? (
            <p>No documents attached yet.</p>
          ) : (
            <ul className="broker-portal-list">
              {documents.slice(0, 8).map((doc) => (
                <li key={doc.id}>
                  {doc.file_name} <span className="muted">({doc.document_type.replace('_', ' ')})</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="broker-portal-card">
          <h2>Recent events</h2>
          {events.length === 0 ? (
            <p>No events recorded yet.</p>
          ) : (
            <ul className="broker-portal-list">
              {events.slice(0, 8).map((event) => (
                <li key={event.id}>
                  <strong>{event.label}</strong> <span className="muted">({event.stage.replace('_', ' ')})</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  )
}


function WarehousePortalView({ token }: { token: string }) {
  const [portal, setPortal] = useState<WarehousePortalResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [actualCbm, setActualCbm] = useState('')
  const [actualWeight, setActualWeight] = useState('')
  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [confirmedAt, setConfirmedAt] = useState<string | null>(null)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)
  const [docFile, setDocFile] = useState('')
  const [docNotes, setDocNotes] = useState('')
  const [docSubmitting, setDocSubmitting] = useState(false)
  const [docMessage, setDocMessage] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getWarehousePortal(token)
      .then((data) => {
        if (cancelled) return
        setPortal(data)
        if (data.booking.cbm_actual != null) setActualCbm(String(data.booking.cbm_actual))
        if (data.booking.weight_kg_actual != null) setActualWeight(String(data.booking.weight_kg_actual))
        if (data.booking.received_at_warehouse) setConfirmedAt(data.booking.received_at_warehouse)
      })
      .catch((err: unknown) => {
        if (!cancelled) setLoadError(err instanceof Error ? err.message : 'Could not load warehouse portal')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [token])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!portal) return
    const cbmValue = Number(actualCbm)
    const weightValue = Number(actualWeight)
    if (!Number.isFinite(cbmValue) || cbmValue <= 0) {
      setStatusMessage('Enter actual cubic meters greater than zero.')
      return
    }
    if (!Number.isFinite(weightValue) || weightValue <= 0) {
      setStatusMessage('Enter actual weight in kilograms greater than zero.')
      return
    }
    setSubmitting(true)
    setStatusMessage(null)
    try {
      const updated = await submitWarehouseReceipt(token, {
        actual_cbm: cbmValue,
        actual_weight_kg: weightValue,
        notes: notes.trim() || null,
      })
      setPortal(updated)
      setConfirmedAt(updated.booking.received_at_warehouse ?? new Date().toISOString())
      setStatusMessage('Receipt confirmed. The importer has been notified.')
    } catch (err) {
      setStatusMessage(err instanceof Error ? err.message : 'Could not save receipt.')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDocUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!docFile.trim()) {
      setDocMessage('A file name is required before uploading.')
      return
    }
    setDocSubmitting(true)
    setDocMessage(null)
    try {
      await uploadWarehouseDocument(token, 'supplier_photos', docFile.trim(), docNotes.trim() || undefined)
      const refreshed = await getWarehousePortal(token)
      setPortal(refreshed)
      setDocMessage(`${docFile} attached.`)
      setDocFile('')
      setDocNotes('')
    } catch (err) {
      setDocMessage(err instanceof Error ? err.message : 'Could not upload the photo.')
    } finally {
      setDocSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="app-shell broker-portal-shell">
        <header className="topbar">
          <Logo />
          <span className="eyebrow">Warehouse workspace</span>
        </header>
        <main className="broker-portal-main">
          <p>Loading shipment.</p>
        </main>
      </div>
    )
  }

  if (loadError || !portal) {
    return (
      <div className="app-shell broker-portal-shell">
        <header className="topbar">
          <Logo />
          <span className="eyebrow">Warehouse workspace</span>
        </header>
        <main className="broker-portal-main">
          <div className="notice error">{loadError ?? 'Warehouse link not found.'}</div>
        </main>
      </div>
    )
  }

  const { booking, documents, events } = portal
  const isPickupMode = booking.delivery_mode === 'ship_hoppa_pickup'

  return (
    <div className="app-shell broker-portal-shell">
      <header className="topbar broker-portal-topbar">
        <Logo />
        <span className="eyebrow">Warehouse workspace</span>
      </header>
      <main className="broker-portal-main">
        <section className="broker-portal-card">
          <p className="eyebrow">Shipment</p>
          <h1>{booking.id}</h1>
          <p className="broker-portal-subtitle">
            {booking.importer_company_name ?? 'Importer'} from {booking.supplier_city}, {booking.supplier_country}.
            Ready by {booking.cargo_ready_date_latest}.
            {booking.warehouse_name && <> Drop at {booking.warehouse_name}.</>}
          </p>
          <div className="broker-portal-grid">
            <div>
              <p className="broker-portal-label">Cargo</p>
              <p>{booking.cargo_description ?? booking.cargo_category}</p>
            </div>
            <div>
              <p className="broker-portal-label">Expected cubic meters (CBM)</p>
              <p>{booking.cbm_estimate}</p>
            </div>
            <div>
              <p className="broker-portal-label">Expected weight (kg)</p>
              <p>{booking.weight_kg_estimate}</p>
            </div>
            <div>
              <p className="broker-portal-label">Packages</p>
              <p>{booking.number_of_packages ?? 'Not provided'}</p>
            </div>
            <div>
              <p className="broker-portal-label">Receipt cutoff</p>
              <p>{booking.warehouse_receipt_cutoff ?? 'No cutoff set'}</p>
            </div>
            <div>
              <p className="broker-portal-label">Booking status</p>
              <p>{booking.status.replace('_', ' ')}</p>
            </div>
          </div>
        </section>

        {isPickupMode ? (
          <section className="broker-portal-card">
            <h2>Ship Hoppa is collecting from the supplier</h2>
            <p>
              This shipment is on Ship Hoppa pickup. You do not need to receive it at a warehouse. The pickup driver will contact
              the supplier directly. If you reached this page by mistake, please tell the importer.
            </p>
          </section>
        ) : confirmedAt ? (
          <section className="broker-portal-card">
            <h2>Receipt confirmed</h2>
            <p>
              You confirmed receipt at {new Date(confirmedAt).toLocaleString()} with {booking.cbm_actual ?? actualCbm} CBM and{' '}
              {booking.weight_kg_actual ?? actualWeight} kg. The importer can see this in their tracking tab.
            </p>
            <p className="muted">If something is wrong, contact the importer to correct the record.</p>
          </section>
        ) : (
          <section className="broker-portal-card">
            <h2>Confirm cargo receipt</h2>
            <form onSubmit={handleSubmit} className="broker-portal-form">
              <label>
                <span>Actual cubic meters (CBM)</span>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={actualCbm}
                  onChange={(event) => setActualCbm(event.target.value)}
                  required
                />
              </label>
              <label>
                <span>Actual weight (kg)</span>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={actualWeight}
                  onChange={(event) => setActualWeight(event.target.value)}
                  required
                />
              </label>
              <label className="broker-portal-textarea">
                <span>Receipt notes (damage, missing items, anything unusual)</span>
                <textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={3} />
              </label>
              <button className="primary-action" type="submit" disabled={submitting}>
                {submitting ? <Loader2 size={16} className="spin" /> : <Check size={16} />}
                {submitting ? 'Saving' : 'Confirm receipt'}
              </button>
            </form>
            {statusMessage && <div className="notice">{statusMessage}</div>}
          </section>
        )}

        {!isPickupMode && (
          <section className="broker-portal-card">
            <h2>Attach a cargo photo</h2>
            <form onSubmit={handleDocUpload} className="broker-portal-form">
              <label>
                <span>File name</span>
                <input
                  value={docFile}
                  onChange={(event) => setDocFile(event.target.value)}
                  placeholder="e.g. cargo-photo-front.jpg"
                />
              </label>
              <label className="broker-portal-textarea">
                <span>Notes</span>
                <textarea value={docNotes} onChange={(event) => setDocNotes(event.target.value)} rows={2} />
              </label>
              <button className="secondary-action" type="submit" disabled={docSubmitting}>
                {docSubmitting ? <Loader2 size={16} className="spin" /> : <FileText size={16} />}
                {docSubmitting ? 'Attaching' : 'Attach photo'}
              </button>
            </form>
            {docMessage && <div className="notice">{docMessage}</div>}
          </section>
        )}

        <section className="broker-portal-card">
          <h2>Recent documents</h2>
          {documents.length === 0 ? (
            <p>No documents attached yet.</p>
          ) : (
            <ul className="broker-portal-list">
              {documents.slice(0, 8).map((doc) => (
                <li key={doc.id}>
                  {doc.file_name} <span className="muted">({doc.document_type.replace('_', ' ')})</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="broker-portal-card">
          <h2>Recent events</h2>
          {events.length === 0 ? (
            <p>No events recorded yet.</p>
          ) : (
            <ul className="broker-portal-list">
              {events.slice(0, 8).map((event) => (
                <li key={event.id}>
                  <strong>{event.label}</strong> <span className="muted">({event.stage.replace('_', ' ')})</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  )
}


function CarrierPortalView({ token }: { token: string }) {
  const [portal, setPortal] = useState<CarrierPortalResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [eta, setEta] = useState('')
  const [etaNote, setEtaNote] = useState('')
  const [etaSubmitting, setEtaSubmitting] = useState(false)
  const [etaMessage, setEtaMessage] = useState<string | null>(null)
  const [eventSubmitting, setEventSubmitting] = useState<CarrierEventStage | null>(null)
  const [eventMessage, setEventMessage] = useState<string | null>(null)
  const [docFile, setDocFile] = useState('')
  const [docNotes, setDocNotes] = useState('')
  const [docSubmitting, setDocSubmitting] = useState(false)
  const [docMessage, setDocMessage] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getCarrierPortal(token)
      .then((data) => {
        if (cancelled) return
        setPortal(data)
        if (data.booking.estimated_arrival) setEta(data.booking.estimated_arrival)
      })
      .catch((err: unknown) => {
        if (!cancelled) setLoadError(err instanceof Error ? err.message : 'Could not load carrier portal')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [token])

  async function handleEtaSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!eta) {
      setEtaMessage('Pick a new estimated arrival date.')
      return
    }
    setEtaSubmitting(true)
    setEtaMessage(null)
    try {
      const updated = await submitCarrierEta(token, {
        estimated_arrival: eta,
        note: etaNote.trim() || null,
      })
      setPortal(updated)
      setEtaMessage('ETA saved. The importer will see the updated arrival.')
      setEtaNote('')
    } catch (err) {
      setEtaMessage(err instanceof Error ? err.message : 'Could not update ETA.')
    } finally {
      setEtaSubmitting(false)
    }
  }

  async function handleEvent(stage: CarrierEventStage) {
    setEventSubmitting(stage)
    setEventMessage(null)
    try {
      const updated = await submitCarrierEvent(token, { stage })
      setPortal(updated)
      setEventMessage(`Recorded ${stage.replace('_', ' ')}.`)
    } catch (err) {
      setEventMessage(err instanceof Error ? err.message : 'Could not record the event.')
    } finally {
      setEventSubmitting(null)
    }
  }

  async function handleDocUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!docFile.trim()) {
      setDocMessage('A file name is required before uploading.')
      return
    }
    setDocSubmitting(true)
    setDocMessage(null)
    try {
      await uploadCarrierDocument(token, 'house_bill', docFile.trim(), docNotes.trim() || undefined)
      const refreshed = await getCarrierPortal(token)
      setPortal(refreshed)
      setDocMessage(`${docFile} attached to the shipment.`)
      setDocFile('')
      setDocNotes('')
    } catch (err) {
      setDocMessage(err instanceof Error ? err.message : 'Could not upload the document.')
    } finally {
      setDocSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="app-shell broker-portal-shell">
        <header className="topbar">
          <Logo />
          <span className="eyebrow">Carrier workspace</span>
        </header>
        <main className="broker-portal-main">
          <p>Loading shipment.</p>
        </main>
      </div>
    )
  }

  if (loadError || !portal) {
    return (
      <div className="app-shell broker-portal-shell">
        <header className="topbar">
          <Logo />
          <span className="eyebrow">Carrier workspace</span>
        </header>
        <main className="broker-portal-main">
          <div className="notice error">{loadError ?? 'Carrier link not found.'}</div>
        </main>
      </div>
    )
  }

  const { booking, documents, events } = portal
  const noContainer = !booking.container_id

  return (
    <div className="app-shell broker-portal-shell">
      <header className="topbar broker-portal-topbar">
        <Logo />
        <span className="eyebrow">Carrier workspace</span>
      </header>
      <main className="broker-portal-main">
        <section className="broker-portal-card">
          <p className="eyebrow">Shipment</p>
          <h1>{booking.id}</h1>
          <p className="broker-portal-subtitle">
            {booking.importer_company_name ?? 'Importer'}. {booking.cargo_description ?? booking.cargo_category}.
          </p>
          <div className="broker-portal-grid">
            <div>
              <p className="broker-portal-label">Container</p>
              <p>{booking.container_number ?? booking.container_id ?? 'Not yet assigned'}</p>
            </div>
            <div>
              <p className="broker-portal-label">Vessel / voyage</p>
              <p>
                {booking.vessel_name ?? 'TBC'}
                {booking.voyage_number && ` / ${booking.voyage_number}`}
              </p>
            </div>
            <div>
              <p className="broker-portal-label">Carrier</p>
              <p>{booking.carrier_name ?? 'TBC'}</p>
            </div>
            <div>
              <p className="broker-portal-label">Sailing date</p>
              <p>{booking.target_sailing_date ?? booking.estimated_departure ?? 'TBC'}</p>
            </div>
            <div>
              <p className="broker-portal-label">Current ETA</p>
              <p>{booking.estimated_arrival ?? 'Not set'}</p>
            </div>
            <div>
              <p className="broker-portal-label">Cutoff</p>
              <p>{booking.carrier_cutoff_date ?? 'TBC'}</p>
            </div>
          </div>
        </section>

        {noContainer ? (
          <section className="broker-portal-card">
            <h2>Container not yet assigned</h2>
            <p>
              This booking has not been placed on a container. ETA updates and milestone events are accepted only after the
              importer has selected a sailing.
            </p>
          </section>
        ) : (
          <>
            <section className="broker-portal-card">
              <h2>Update ETA</h2>
              <form onSubmit={handleEtaSubmit} className="broker-portal-form">
                <label>
                  <span>New estimated arrival</span>
                  <input
                    type="date"
                    value={eta}
                    onChange={(event) => setEta(event.target.value)}
                    required
                  />
                </label>
                <label className="broker-portal-textarea">
                  <span>Reason / note (optional)</span>
                  <textarea value={etaNote} onChange={(event) => setEtaNote(event.target.value)} rows={2} />
                </label>
                <button className="primary-action" type="submit" disabled={etaSubmitting}>
                  {etaSubmitting ? <Loader2 size={16} className="spin" /> : <CalendarClock size={16} />}
                  {etaSubmitting ? 'Saving' : 'Save new ETA'}
                </button>
              </form>
              {etaMessage && <div className="notice">{etaMessage}</div>}
            </section>

            <section className="broker-portal-card">
              <h2>Mark milestone</h2>
              <p className="muted">
                Record the moment the cargo is loaded, the vessel departs, or the vessel arrives at the destination port.
              </p>
              <div className="action-panel-buttons">
                <button
                  className="secondary-action small"
                  type="button"
                  disabled={eventSubmitting !== null}
                  onClick={() => handleEvent('loaded')}
                >
                  {eventSubmitting === 'loaded' ? <Loader2 size={14} className="spin" /> : <Check size={14} />}
                  Mark loaded
                </button>
                <button
                  className="secondary-action small"
                  type="button"
                  disabled={eventSubmitting !== null}
                  onClick={() => handleEvent('departed')}
                >
                  {eventSubmitting === 'departed' ? <Loader2 size={14} className="spin" /> : <Ship size={14} />}
                  Mark departed
                </button>
                <button
                  className="secondary-action small"
                  type="button"
                  disabled={eventSubmitting !== null}
                  onClick={() => handleEvent('arrived')}
                >
                  {eventSubmitting === 'arrived' ? <Loader2 size={14} className="spin" /> : <MapPin size={14} />}
                  Mark arrived
                </button>
              </div>
              {eventMessage && <div className="notice">{eventMessage}</div>}
            </section>

            <section className="broker-portal-card">
              <h2>Attach bill of lading</h2>
              <form onSubmit={handleDocUpload} className="broker-portal-form">
                <label>
                  <span>File name</span>
                  <input
                    value={docFile}
                    onChange={(event) => setDocFile(event.target.value)}
                    placeholder="e.g. house-bl-12345.pdf"
                  />
                </label>
                <label className="broker-portal-textarea">
                  <span>Notes</span>
                  <textarea value={docNotes} onChange={(event) => setDocNotes(event.target.value)} rows={2} />
                </label>
                <button className="secondary-action" type="submit" disabled={docSubmitting}>
                  {docSubmitting ? <Loader2 size={16} className="spin" /> : <FileText size={16} />}
                  {docSubmitting ? 'Attaching' : 'Attach BL'}
                </button>
              </form>
              {docMessage && <div className="notice">{docMessage}</div>}
            </section>
          </>
        )}

        <section className="broker-portal-card">
          <h2>Recent events</h2>
          {events.length === 0 ? (
            <p>No events recorded yet.</p>
          ) : (
            <ul className="broker-portal-list">
              {events.slice(0, 8).map((event) => (
                <li key={event.id}>
                  <strong>{event.label}</strong> <span className="muted">({event.stage.replace('_', ' ')})</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="broker-portal-card">
          <h2>Recent documents</h2>
          {documents.length === 0 ? (
            <p>No documents attached yet.</p>
          ) : (
            <ul className="broker-portal-list">
              {documents.slice(0, 8).map((doc) => (
                <li key={doc.id}>
                  {doc.file_name} <span className="muted">({doc.document_type.replace('_', ' ')})</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  )
}


function TruckerPortalView({ token }: { token: string }) {
  const [portal, setPortal] = useState<TruckerPortalResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [stageSubmitting, setStageSubmitting] = useState<TruckerStage | null>(null)
  const [stageMessage, setStageMessage] = useState<string | null>(null)
  const [statusNotes, setStatusNotes] = useState('')
  const [podFile, setPodFile] = useState('')
  const [podNotes, setPodNotes] = useState('')
  const [podSubmitting, setPodSubmitting] = useState(false)
  const [podMessage, setPodMessage] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getTruckerPortal(token)
      .then((data) => {
        if (!cancelled) setPortal(data)
      })
      .catch((err: unknown) => {
        if (!cancelled) setLoadError(err instanceof Error ? err.message : 'Could not load trucker portal')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [token])

  async function handleStage(stage: TruckerStage) {
    setStageSubmitting(stage)
    setStageMessage(null)
    try {
      const updated = await submitTruckerStatus(token, { stage, notes: statusNotes.trim() || null })
      setPortal(updated)
      setStageMessage(`Recorded ${stage.replace('_', ' ')}.`)
      setStatusNotes('')
    } catch (err) {
      setStageMessage(err instanceof Error ? err.message : 'Could not record the status update.')
    } finally {
      setStageSubmitting(null)
    }
  }

  async function handlePodUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!podFile.trim()) {
      setPodMessage('A file name is required before uploading.')
      return
    }
    setPodSubmitting(true)
    setPodMessage(null)
    try {
      await uploadTruckerPod(token, podFile.trim(), podNotes.trim() || undefined)
      const refreshed = await getTruckerPortal(token)
      setPortal(refreshed)
      setPodMessage(`${podFile} attached as proof of delivery.`)
      setPodFile('')
      setPodNotes('')
    } catch (err) {
      setPodMessage(err instanceof Error ? err.message : 'Could not upload the proof of delivery.')
    } finally {
      setPodSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="app-shell broker-portal-shell">
        <header className="topbar">
          <Logo />
          <span className="eyebrow">Trucker workspace</span>
        </header>
        <main className="broker-portal-main">
          <p>Loading shipment.</p>
        </main>
      </div>
    )
  }

  if (loadError || !portal) {
    return (
      <div className="app-shell broker-portal-shell">
        <header className="topbar">
          <Logo />
          <span className="eyebrow">Trucker workspace</span>
        </header>
        <main className="broker-portal-main">
          <div className="notice error">{loadError ?? 'Trucker link not found.'}</div>
        </main>
      </div>
    )
  }

  const { booking, holds, can_deliver: canDeliver, documents, events } = portal

  return (
    <div className="app-shell broker-portal-shell">
      <header className="topbar broker-portal-topbar">
        <Logo />
        <span className="eyebrow">Trucker workspace</span>
      </header>
      <main className="broker-portal-main">
        <section className="broker-portal-card">
          <p className="eyebrow">Shipment</p>
          <h1>{booking.id}</h1>
          <p className="broker-portal-subtitle">
            Deliver to {booking.importer_company_name ?? 'importer'} at {booking.destination_address}.
          </p>
          <div className="broker-portal-grid">
            <div>
              <p className="broker-portal-label">Contact</p>
              <p>{booking.destination_contact_name}</p>
            </div>
            <div>
              <p className="broker-portal-label">Phone</p>
              <p>{booking.destination_contact_phone ?? 'Not provided'}</p>
            </div>
            <div>
              <p className="broker-portal-label">Delivery window</p>
              <p>
                {booking.delivery_window_start ?? 'TBC'}
                {booking.delivery_window_end && ` to ${booking.delivery_window_end}`}
              </p>
            </div>
            <div>
              <p className="broker-portal-label">Equipment</p>
              <p>{booking.equipment_required.length ? booking.equipment_required.join(', ') : 'None specified'}</p>
            </div>
            <div>
              <p className="broker-portal-label">Cargo</p>
              <p>{booking.cargo_description ?? booking.cargo_category}</p>
            </div>
            <div>
              <p className="broker-portal-label">Volume / weight</p>
              <p>{booking.cbm_estimate} CBM / {booking.weight_kg_estimate} kg</p>
            </div>
          </div>
        </section>

        {!canDeliver && holds.length > 0 && (
          <section className="broker-portal-card">
            <h2>Release blocked</h2>
            <p>This shipment cannot be marked delivered until the importer clears these holds.</p>
            <ul className="broker-portal-list">
              {holds.map((hold) => (
                <li key={hold.id}>
                  <strong>{hold.hold_type.replace('_', ' ')}</strong>: {hold.reason}
                </li>
              ))}
            </ul>
            <p className="muted">You can still mark pickup_scheduled and picked_up while we wait.</p>
          </section>
        )}

        <section className="broker-portal-card">
          <h2>Update delivery status</h2>
          <label className="broker-portal-textarea">
            <span>Optional note for this update</span>
            <textarea value={statusNotes} onChange={(event) => setStatusNotes(event.target.value)} rows={2} />
          </label>
          <div className="action-panel-buttons">
            <button
              className="secondary-action small"
              type="button"
              disabled={stageSubmitting !== null}
              onClick={() => handleStage('pickup_scheduled')}
            >
              {stageSubmitting === 'pickup_scheduled' ? <Loader2 size={14} className="spin" /> : <CalendarClock size={14} />}
              Pickup scheduled
            </button>
            <button
              className="secondary-action small"
              type="button"
              disabled={stageSubmitting !== null}
              onClick={() => handleStage('picked_up')}
            >
              {stageSubmitting === 'picked_up' ? <Loader2 size={14} className="spin" /> : <Truck size={14} />}
              Picked up from port
            </button>
            <button
              className="primary-action small"
              type="button"
              disabled={stageSubmitting !== null || !canDeliver}
              onClick={() => handleStage('delivered')}
              title={canDeliver ? '' : 'Release is blocked. Importer must clear holds first.'}
            >
              {stageSubmitting === 'delivered' ? <Loader2 size={14} className="spin" /> : <PackageCheck size={14} />}
              Mark delivered
            </button>
          </div>
          {stageMessage && <div className="notice">{stageMessage}</div>}
        </section>

        <section className="broker-portal-card">
          <h2>Upload proof of delivery</h2>
          <form onSubmit={handlePodUpload} className="broker-portal-form">
            <label>
              <span>POD file name</span>
              <input
                value={podFile}
                onChange={(event) => setPodFile(event.target.value)}
                placeholder="e.g. pod-signed.pdf"
              />
            </label>
            <label className="broker-portal-textarea">
              <span>Notes</span>
              <textarea value={podNotes} onChange={(event) => setPodNotes(event.target.value)} rows={2} />
            </label>
            <button className="secondary-action" type="submit" disabled={podSubmitting}>
              {podSubmitting ? <Loader2 size={16} className="spin" /> : <FileText size={16} />}
              {podSubmitting ? 'Attaching' : 'Attach POD'}
            </button>
          </form>
          {podMessage && <div className="notice">{podMessage}</div>}
        </section>

        <section className="broker-portal-card">
          <h2>Recent events</h2>
          {events.length === 0 ? (
            <p>No events recorded yet.</p>
          ) : (
            <ul className="broker-portal-list">
              {events.slice(0, 8).map((event) => (
                <li key={event.id}>
                  <strong>{event.label}</strong> <span className="muted">({event.stage.replace('_', ' ')})</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="broker-portal-card">
          <h2>Recent documents</h2>
          {documents.length === 0 ? (
            <p>No documents attached yet.</p>
          ) : (
            <ul className="broker-portal-list">
              {documents.slice(0, 8).map((doc) => (
                <li key={doc.id}>
                  {doc.file_name} <span className="muted">({doc.document_type.replace('_', ' ')})</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  )
}


function App() {
  const [view, setView] = useState<View>('book')
  const hasAutoRoutedRef = useRef(false)
  const [workspaceMode, setWorkspaceMode] = useState<WorkspaceMode>(() => initialWorkspaceMode())
  const [adminView, setAdminView] = useState<AdminView>('overview')
  const [automationResult, setAutomationResult] = useState<AutomationRunAllResult | null>(null)
  const [staleAlerts, setStaleAlerts] = useState<StaleCheckAlert[]>([])
  const [shipmentStates, setShipmentStates] = useState<Record<string, ShipmentStateResponse>>({})
  const [adminTasks, setAdminTasks] = useState<AdminTask[]>([])
  const [adminTaskSummary, setAdminTaskSummary] = useState<AdminTaskSummary | null>(null)
  const [allApprovals, setAllApprovals] = useState<ApprovalRequestRecord[]>([])
  const [auditFilters, setAuditFilters] = useState<AuditEventFilters>({})
  const [auditFilterDraft, setAuditFilterDraft] = useState<AuditEventFilters>({})
  const [auditResults, setAuditResults] = useState<AuditEvent[] | null>(null)
  const [auditLoading, setAuditLoading] = useState(false)
  const [auditError, setAuditError] = useState<string | null>(null)
  const [inboxMessages, setInboxMessages] = useState<SourceMessage[]>([])
  const [landedCost, setLandedCost] = useState<LandedCostSummary | null>(null)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [activeShipmentState, setActiveShipmentState] = useState<ShipmentStateResponse | null>(null)
  const [activeMissingData, setActiveMissingData] = useState<APIMissingDataItem[]>([])
  const [spaceOpportunities, setSpaceOpportunities] = useState<SpaceOpportunity[]>([])
  const [invoiceText, setInvoiceText] = useState('')
  const [parsedInvoice, setParsedInvoice] = useState<ParsedInvoice | null>(null)
  const [parsingInvoice, setParsingInvoice] = useState(false)
  const [activeInspections, setActiveInspections] = useState<QualityInspectionRecord[]>([])
  const [inspectionDraft, setInspectionDraft] = useState({ provider: '', inspection_date: '', location: '' })
  const [hsSuggestions, setHsSuggestions] = useState<HsSuggestionsResponse | null>(null)
  const [adminEmail, setAdminEmail] = useState('ops@shiphoppa.example')
  const [adminPassword, setAdminPassword] = useState('')
  const [adminLoginError, setAdminLoginError] = useState<string | null>(null)
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [containers, setContainers] = useState<Container[]>([])
  const [bookings, setBookings] = useState<Booking[]>([])
  const [profile, setProfile] = useState<CustomerProfile>(() => readStoredProfile())
  const [accountIntegrations, setAccountIntegrations] = useState<AccountIntegration[]>([])
  const [form, setForm] = useState<BookingPayload>(() => ({ ...initialForm, ...readStoredProfile() }))
  const [supplierLocationInput, setSupplierLocationInput] = useState(() =>
    supplierLocationInputValue({ ...initialForm, ...readStoredProfile() }),
  )
  const [match, setMatch] = useState<MatchResult | null>(null)
  const [activeOpsBookingId, setActiveOpsBookingId] = useState<string | null>(null)
  const [supplierInstructions, setSupplierInstructions] = useState<string | null>(null)
  const [carrierOptions, setCarrierOptions] = useState<Record<string, CarrierOption[]>>({})
  const [sailings, setSailings] = useState<SailingSearchResult[]>([])
  const [sailingOrigin, setSailingOrigin] = useState('all')
  const [sailingDestination, setSailingDestination] = useState('all')
  const [sailingWindowStart, setSailingWindowStart] = useState(() => formatDateInput(0))
  const [sailingWindowEnd, setSailingWindowEnd] = useState(() => formatDateInput(60))
  const [checklist, setChecklist] = useState<BookingChecklistResponse | null>(null)
  const [events, setEvents] = useState<ShipmentEvent[]>([])
  const [invoice, setInvoice] = useState<Invoice | null>(null)
  const [releaseStatus, setReleaseStatus] = useState<ReleaseStatusResponse | null>(null)
  const [customsProfile, setCustomsProfile] = useState<CustomsProfile | null>(null)
  const [deliveryPlan, setDeliveryPlan] = useState<DeliveryPlan | null>(null)
  const [projectWorkspace, setProjectWorkspace] = useState<ImportProjectWorkspaceResponse | null>(null)
  const [supplierLink, setSupplierLink] = useState<SupplierAccessLink | null>(null)
  const [supplierPortal, setSupplierPortal] = useState<SupplierPortalResponse | null>(null)
  const [brokerLink, setBrokerLink] = useState<BrokerAccessLink | null>(null)
  const [brokerInviteMessage, setBrokerInviteMessage] = useState<string | null>(null)
  const [warehouseLink, setWarehouseLink] = useState<WarehouseAccessLink | null>(null)
  const [warehouseInviteMessage, setWarehouseInviteMessage] = useState<string | null>(null)
  const [carrierLink, setCarrierLink] = useState<CarrierAccessLink | null>(null)
  const [carrierInviteMessage, setCarrierInviteMessage] = useState<string | null>(null)
  const [truckerLink, setTruckerLink] = useState<TruckerAccessLink | null>(null)
  const [truckerInviteMessage, setTruckerInviteMessage] = useState<string | null>(null)
  const [sourceMessageDraft, setSourceMessageDraft] = useState({
    from_address: 'sales@supplier.example',
    subject: 'Supplier pro forma and production update',
    body: 'Please find the pro forma invoice, production timing, packing details, and cargo-ready estimate attached.',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [releaseMessage, setReleaseMessage] = useState<string | null>(null)

  async function refresh() {
    const [summaryData, containerData, bookingData, sailingData, profileData, integrationData] = await Promise.all([
      getSummary(),
      getContainers(),
      getBookings(),
      getSailings(),
      getAccountProfile(),
      getAccountIntegrations(),
    ])
    setSummary(summaryData)
    setContainers(containerData)
    setBookings(bookingData)
    setSailings(sailingData)
    const accountProfile = customerProfileFromAccount(profileData)
    setProfile(accountProfile)
    const accountDefaults = bookingDefaultsFromAccountProfile(profileData)
    setForm((current) => ({ ...current, ...accountDefaults }))
    if (profileData.default_supplier_city) {
      setSupplierLocationInput(supplierLocationInputValue({ ...initialForm, ...accountDefaults }))
    }
    setAccountIntegrations(integrationData)
  }

  useEffect(() => {
    let cancelled = false
    getApprovals()
      .then((data) => {
        if (!cancelled) setAllApprovals(data)
      })
      .catch(() => {})
    getNotifications()
      .then((data) => {
        if (!cancelled) setNotifications(data)
      })
      .catch(() => {})
    Promise.all([getSummary(), getContainers(), getBookings(), getSailings(), getAccountProfile(), getAccountIntegrations()])
      .then(([summaryData, containerData, bookingData, sailingData, profileData, integrationData]) => {
        if (cancelled) return
        setSummary(summaryData)
        setContainers(containerData)
        setBookings(bookingData)
        setSailings(sailingData)
        const accountProfile = customerProfileFromAccount(profileData)
        setProfile(accountProfile)
        globalThis.localStorage?.setItem(PROFILE_STORAGE_KEY, JSON.stringify(accountProfile))
        const accountDefaults = bookingDefaultsFromAccountProfile(profileData)
        setForm((current) => ({ ...current, ...accountDefaults }))
        setSupplierLocationInput(
          supplierLocationInputValue({
            ...initialForm,
            ...readStoredProfile(),
            ...accountDefaults,
          }),
        )
        setAccountIntegrations(integrationData)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    function syncWorkspaceToPath() {
      if (brokerTokenFromPath()) {
        setWorkspaceMode('broker-portal')
        return
      }
      if (warehouseTokenFromPath()) {
        setWorkspaceMode('warehouse-portal')
        return
      }
      if (carrierTokenFromPath()) {
        setWorkspaceMode('carrier-portal')
        return
      }
      if (truckerTokenFromPath()) {
        setWorkspaceMode('trucker-portal')
        return
      }
      if (globalThis.location?.pathname === '/admin') {
        setWorkspaceMode((current) => (current === 'admin' ? current : 'admin-login'))
        return
      }
      setWorkspaceMode('customer')
      setAdminPassword('')
      setAdminLoginError(null)
    }

    globalThis.addEventListener?.('popstate', syncWorkspaceToPath)
    return () => {
      globalThis.removeEventListener?.('popstate', syncWorkspaceToPath)
    }
  }, [])

  useEffect(() => {
    globalThis.scrollTo?.({ top: 0, left: 0, behavior: 'auto' })
  }, [view, adminView, workspaceMode])

  useEffect(() => {
    if (workspaceMode === 'admin' && (adminView === 'exceptions' || adminView === 'overview')) {
      getAdminTasks({ status: 'open' }).then(setAdminTasks).catch(() => {})
      getAdminTaskSummary().then(setAdminTaskSummary).catch(() => {})
    }
  }, [workspaceMode, adminView])

  useEffect(() => {
    if (view === 'inbox') {
      getSourceMessages().then(setInboxMessages).catch(() => {})
    }
  }, [view])

  useEffect(() => {
    if (hasAutoRoutedRef.current) return
    if (workspaceMode !== 'customer') return
    if (bookings.length === 0) return
    if (view !== 'book') return
    hasAutoRoutedRef.current = true
    setView('tracking')
  }, [bookings.length, workspaceMode, view])

  // Poll for new approvals and notifications every 30s while customer view is active
  useEffect(() => {
    if (workspaceMode !== 'customer') return
    const interval = setInterval(() => {
      getApprovals().then(setAllApprovals).catch(() => {})
      getNotifications().then(setNotifications).catch(() => {})
    }, 30000)
    return () => clearInterval(interval)
  }, [workspaceMode])

  const selectedContainer = useMemo(() => {
    if (match?.container) {
      return containers.find((container) => container.id === match.container?.id) ?? match.container
    }
    return containers[0] ?? null
  }, [containers, match])

  const activeBooking = bookings.find((booking) => booking.id === activeOpsBookingId) ?? match?.booking ?? bookings[0] ?? null

  useEffect(() => {
    if (view === 'money' && activeBooking) {
      getLandedCostSummary(activeBooking.id).then(setLandedCost).catch(() => setLandedCost(null))
    }
  }, [view, activeBooking?.id])

  useEffect(() => {
    if (view === 'customs' && activeBooking) {
      getHsSuggestions(activeBooking.id).then(setHsSuggestions).catch(() => setHsSuggestions(null))
    }
  }, [view, activeBooking?.id])

  async function handleAcceptHsSuggestion() {
    if (!activeBooking) return
    try {
      await acceptHsSuggestion(activeBooking.id)
      const refreshed = await getHsSuggestions(activeBooking.id)
      setHsSuggestions(refreshed)
      setReleaseMessage('HS code applied to the customs profile.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not accept HS suggestion')
    }
  }

  useEffect(() => {
    if (!activeBooking) {
      setActiveShipmentState(null)
      setActiveMissingData([])
      setSpaceOpportunities([])
      setActiveInspections([])
      return
    }
    getShipmentState(activeBooking.id).then(setActiveShipmentState).catch(() => setActiveShipmentState(null))
    getMissingData(activeBooking.id).then(setActiveMissingData).catch(() => setActiveMissingData([]))
    getSpaceOpportunities(activeBooking.id).then(setSpaceOpportunities).catch(() => setSpaceOpportunities([]))
    getBookingInspections(activeBooking.id).then(setActiveInspections).catch(() => setActiveInspections([]))
  }, [activeBooking?.id])

  async function handleBookInspector(inspectionId: string) {
    if (!inspectionDraft.provider || !inspectionDraft.inspection_date || !inspectionDraft.location) {
      setError('Please fill provider, date and location to book an inspector.')
      return
    }
    try {
      await bookInspection(inspectionId, inspectionDraft)
      if (activeBooking) {
        const refreshed = await getBookingInspections(activeBooking.id)
        setActiveInspections(refreshed)
      }
      setInspectionDraft({ provider: '', inspection_date: '', location: '' })
      setReleaseMessage('Inspector booked. You will be notified when the result is in.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not book inspector')
    }
  }

  async function handleDetectSpareSpace() {
    if (!activeBooking) return
    try {
      const result = await detectSpaceOpportunity(activeBooking.id)
      if (result) {
        const refreshed = await getSpaceOpportunities(activeBooking.id)
        setSpaceOpportunities(refreshed)
      } else {
        setError('No spare capacity detected. This shipment is not FCL or is already full.')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not detect spare space')
    }
  }

  async function handleListSpareSpace(opportunityId: string) {
    if (!activeBooking) return
    try {
      await listSpaceOpportunity(opportunityId)
      const refreshed = await getSpaceOpportunities(activeBooking.id)
      setSpaceOpportunities(refreshed)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not list spare space')
    }
  }

  async function handleInvoicePreview() {
    if (!invoiceText.trim()) {
      setError('Paste invoice text first.')
      return
    }
    setParsingInvoice(true)
    try {
      const response = await parseInvoiceText(invoiceText, { booking_id: activeBooking?.id })
      setParsedInvoice(response.parsed)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not parse invoice')
    } finally {
      setParsingInvoice(false)
    }
  }

  async function handleInvoiceApply() {
    if (!invoiceText.trim()) {
      setError('Paste invoice text first.')
      return
    }
    setParsingInvoice(true)
    try {
      const response = await parseInvoiceText(invoiceText, { booking_id: activeBooking?.id, apply: true })
      setParsedInvoice(response.parsed)
      if (response.applied?.supplier_pay_request_id) {
        setReleaseMessage('Invoice captured and supplier payment created. Approve in your queue.')
        const refreshed = await getApprovals()
        setAllApprovals(refreshed)
      } else {
        setError('Could not match invoice to a purchase order. Check the PO reference and supplier name.')
      }
      setInvoiceText('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not apply invoice')
    } finally {
      setParsingInvoice(false)
    }
  }

  async function handleInvoicePdfUpload(file: File, apply: boolean) {
    setParsingInvoice(true)
    try {
      const response = await parseInvoicePdf(file, { booking_id: activeBooking?.id, apply })
      setParsedInvoice(response.parsed)
      if (response.warning) {
        setError(response.warning)
      } else if (apply && response.applied?.supplier_pay_request_id) {
        setReleaseMessage('Invoice PDF captured and supplier payment created. Approve in your queue.')
        const refreshed = await getApprovals()
        setAllApprovals(refreshed)
      } else if (apply && !response.applied?.supplier_pay_request_id) {
        setError('Parsed the PDF but could not match it to a purchase order. Check the PO reference and supplier name.')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not parse the PDF')
    } finally {
      setParsingInvoice(false)
    }
  }

  const orderSwitcherBookings = useMemo(() => {
    if (!activeBooking || bookings.some((booking) => booking.id === activeBooking.id)) return bookings
    return [activeBooking, ...bookings]
  }, [activeBooking, bookings])
  const activeContainer = useMemo(() => {
    if (!activeBooking?.container_id) return selectedContainer
    return containers.find((container) => container.id === activeBooking.container_id) ?? selectedContainer
  }, [activeBooking, containers, selectedContainer])
  const activeSailing = useMemo(() => {
    return sailingForContainer(activeContainer, sailings)
  }, [activeContainer, sailings])
  const activeReleaseHolds = releaseStatus?.holds.filter((hold) => hold.status === 'active') ?? []
  const approvedDocumentCount = checklist?.documents.filter((document) => document.status === 'approved').length ?? 0
  const uploadedDocumentCount = checklist?.documents.length ?? 0
  const requiredDocumentCount = checklist?.requirements.filter((requirement) => requirement.required).length ?? 0
  const orderDocumentRequirements = checklist?.requirements.filter((requirement) => orderDocumentTypes.has(requirement.document_type)) ?? []
  const shipDocumentRequirements = checklist?.requirements.filter((requirement) => shipDocumentTypes.has(requirement.document_type)) ?? []
  const orderDocumentCount = checklist?.documents.filter((document) => orderDocumentTypes.has(document.document_type)).length ?? 0
  const shipDocumentCount = checklist?.documents.filter((document) => shipDocumentTypes.has(document.document_type)).length ?? 0
  const orderApprovedDocumentCount =
    checklist?.documents.filter((document) => orderDocumentTypes.has(document.document_type) && document.status === 'approved').length ?? 0
  const shipApprovedDocumentCount =
    checklist?.documents.filter((document) => shipDocumentTypes.has(document.document_type) && document.status === 'approved').length ?? 0
  const orderMissingDocumentCount = checklist?.missing_document_types.filter((type) => orderDocumentTypes.has(type)).length ?? 0
  const shipMissingDocumentCount = checklist?.missing_document_types.filter((type) => shipDocumentTypes.has(type)).length ?? 0
  const activeDocumentRequirements = view === 'order_docs' ? orderDocumentRequirements : shipDocumentRequirements
  const activeDocumentRequiredCount = activeDocumentRequirements.filter((requirement) => requirement.required).length
  const activeDocumentUploadedCount = view === 'order_docs' ? orderDocumentCount : shipDocumentCount
  const activeDocumentApprovedCount = view === 'order_docs' ? orderApprovedDocumentCount : shipApprovedDocumentCount
  const activeDocumentMissingCount = view === 'order_docs' ? orderMissingDocumentCount : shipMissingDocumentCount
  const activePurchaseOrder = projectWorkspace?.purchase_orders[0] ?? null
  const activeProductionMilestones = projectWorkspace?.production_milestones.filter(
    (milestone) => milestone.purchase_order_id === activePurchaseOrder?.id,
  ) ?? []
  const activeQualityInspection =
    projectWorkspace?.quality_inspections.find((inspection) => inspection.purchase_order_id === activePurchaseOrder?.id) ?? null
  const activeQcMilestone = activeProductionMilestones.find((milestone) => milestone.milestone_type === 'qc_passed') ?? null
  const activeSupplierPayRequests = projectWorkspace?.supplier_pay_requests.filter(
    (request) => request.purchase_order_id === activePurchaseOrder?.id,
  ) ?? []
  const activeSupplierPayRequest = activeSupplierPayRequests[0] ?? null
  const activeSupplierPayQuotes = projectWorkspace?.supplier_pay_quotes.filter(
    (quote) => quote.supplier_pay_request_id === activeSupplierPayRequest?.id,
  ) ?? []
  const openApprovals = projectWorkspace?.approvals.filter((approval) => approval.status === 'pending') ?? []
  const allPendingApprovals = allApprovals.filter((approval) => approval.status === 'pending')
  const unreadNotificationCount = notifications.filter((n) => !n.read).length

  async function handleApprovalDecision(approvalId: string, decision: 'approve' | 'reject') {
    try {
      if (decision === 'approve') {
        await approveApprovalRequest(approvalId)
      } else {
        await rejectApprovalRequest(approvalId)
      }
      const refreshed = await getApprovals()
      setAllApprovals(refreshed)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Approval decision failed')
    }
  }
  const activeSourceMessages = projectWorkspace?.source_messages ?? []
  const selectedSailing = useMemo(
    () => sailings.find((sailing) => sailing.sailing_option_id === form.preferred_sailing_option_id) ?? null,
    [form.preferred_sailing_option_id, sailings],
  )
  const sailingOriginOptions = useMemo(
    () => Array.from(new Set(sailings.map((sailing) => sailingOriginPort(sailing)))).sort(),
    [sailings],
  )
  const sailingDestinationOptions = useMemo(
    () => Array.from(new Set(sailings.map((sailing) => sailingDestinationPort(sailing)))).sort(),
    [sailings],
  )
  const filteredSailings = useMemo(
    () =>
      sailings.filter((sailing) => {
        const originMatches = sailingOrigin === 'all' || sailingOriginPort(sailing) === sailingOrigin
        const destinationMatches = sailingDestination === 'all' || sailingDestinationPort(sailing) === sailingDestination
        const startsAfterWindow = !sailingWindowStart || sailing.etd >= sailingWindowStart
        const startsBeforeWindow = !sailingWindowEnd || sailing.etd <= sailingWindowEnd
        return originMatches && destinationMatches && startsAfterWindow && startsBeforeWindow
      }),
    [sailings, sailingDestination, sailingOrigin, sailingWindowEnd, sailingWindowStart],
  )
  const visibleSailing = selectedSailing ?? filteredSailings[0] ?? sailings[0] ?? null
  const alternativeSailings = useMemo(() => {
    const matchedSailingId = match?.container?.sailing_option_id
    const matchedSailingDate = match?.container?.target_sailing_date
    return sailings
      .filter((sailing) => sailing.sailing_option_id !== matchedSailingId && sailing.etd !== matchedSailingDate)
      .slice(0, 3)
  }, [match, sailings])
  async function loadOperatingData(bookingId: string) {
    const [checklistData, eventData, invoiceData, releaseData, customsData, deliveryData, workspaceData] = await Promise.all([
      getChecklist(bookingId),
      getEvents(bookingId),
      getInvoice(bookingId),
      getReleaseStatus(bookingId),
      getCustomsProfile(bookingId),
      getDeliveryPlan(bookingId),
      getImportProjectWorkspace(bookingId),
    ])
    setChecklist(checklistData)
    setEvents(eventData)
    setInvoice(invoiceData)
    setReleaseStatus(releaseData)
    setCustomsProfile(customsData)
    setDeliveryPlan(deliveryData)
    setProjectWorkspace(workspaceData)
  }

  async function openOpsBooking(bookingId: string) {
    setActiveOpsBookingId(bookingId)
    setError(null)
    try {
      await loadOperatingData(bookingId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load shipment work')
    }
  }

  useEffect(() => {
    if (!activeBooking?.id) return
    let cancelled = false
    Promise.all([
      getChecklist(activeBooking.id),
      getEvents(activeBooking.id),
      getInvoice(activeBooking.id),
      getReleaseStatus(activeBooking.id),
      getCustomsProfile(activeBooking.id),
      getDeliveryPlan(activeBooking.id),
      getImportProjectWorkspace(activeBooking.id),
    ])
      .then(([checklistData, eventData, invoiceData, releaseData, customsData, deliveryData, workspaceData]) => {
        if (cancelled) return
        setChecklist(checklistData)
        setEvents(eventData)
        setInvoice(invoiceData)
        setReleaseStatus(releaseData)
        setCustomsProfile(customsData)
        setDeliveryPlan(deliveryData)
        setProjectWorkspace(workspaceData)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Could not load booking workspace')
      })
    return () => {
      cancelled = true
    }
  }, [activeBooking?.id])

  function updateField<K extends keyof BookingPayload>(key: K, value: BookingPayload[K]) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  function updatePackageField<K extends keyof BookingPayload>(key: K, value: BookingPayload[K]) {
    setForm((current) => {
      const next = { ...current, [key]: value }
      const calculatedVolume = calculateVolumeM3(
        next.number_of_packages,
        next.package_length_cm,
        next.package_width_cm,
        next.package_height_cm,
      )
      return {
        ...next,
        cbm_estimate: calculatedVolume ?? current.cbm_estimate,
      }
    })
  }

  function updateSupplierLocation(value: string) {
    setSupplierLocationInput(value)
    const normalizedCity = value.split(',')[0].trim()
    const normalizedValue = value.trim().toLowerCase()
    const matchedLocation = supplierLocations.find(
      (location) =>
        location.city.toLowerCase() === normalizedCity.toLowerCase() ||
        locationLabel(location).toLowerCase() === normalizedValue,
    )
    if (matchedLocation) setSupplierLocationInput(locationLabel(matchedLocation))
    setForm((current) => ({
      ...current,
      supplier_city: matchedLocation?.city ?? normalizedCity,
      supplier_province: matchedLocation?.province ?? current.supplier_province,
      supplier_country: matchedLocation?.country ?? current.supplier_country,
      pickup_address: matchedLocation?.pickupAddress ?? current.pickup_address,
    }))
  }

  function updateProfileField<K extends keyof CustomerProfile>(key: K, value: CustomerProfile[K]) {
    setProfile((current) => ({ ...current, [key]: value }))
  }

  async function handleProfileSave(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError(null)
    setReleaseMessage(null)
    try {
      const saved = await updateAccountProfile({
        ...profile,
        default_supplier_city: form.supplier_city,
        default_supplier_province: form.supplier_province,
        default_supplier_country: form.supplier_country,
        default_delivery_mode: form.delivery_mode,
      })
      const savedProfile = customerProfileFromAccount(saved)
      globalThis.localStorage?.setItem(PROFILE_STORAGE_KEY, JSON.stringify(savedProfile))
      setProfile(savedProfile)
      setForm((current) => ({ ...current, ...bookingDefaultsFromAccountProfile(saved) }))
      setReleaseMessage('Profile saved. New bookings will use these defaults.')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  async function handleIntegrationStatus(provider: AccountIntegrationProvider, connected: boolean) {
    setLoading(true)
    setError(null)
    setReleaseMessage(null)
    try {
      const updated = await updateAccountIntegration(provider, {
        status: connected ? 'connected' : 'not_connected',
        notes: connected ? 'Connected in Ship Hoppa demo mode.' : 'Disconnected by importer.',
      })
      setAccountIntegrations((current) => current.map((item) => (item.provider === updated.provider ? updated : item)))
      setReleaseMessage(`${updated.display_name} integration updated.`)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  function updateSourceMessageDraft<K extends keyof typeof sourceMessageDraft>(key: K, value: (typeof sourceMessageDraft)[K]) {
    setSourceMessageDraft((current) => ({ ...current, [key]: value }))
  }

  async function handleSourceMessageIngest(event: FormEvent) {
    event.preventDefault()
    if (!activeBooking) {
      setError('Create or select an order before forwarding supplier messages into Ship Hoppa.')
      return
    }
    setLoading(true)
    setError(null)
    setReleaseMessage(null)
    try {
      const subject = sourceMessageDraft.subject.includes(activeBooking.id)
        ? sourceMessageDraft.subject
        : `${activeBooking.id} · ${sourceMessageDraft.subject}`
      await createSourceMessage({
        source_type: 'forwarded_email',
        from_address: sourceMessageDraft.from_address,
        to_addresses: [profile.importer_email],
        subject,
        body: `${sourceMessageDraft.body}\n\nSupplier: ${activeBooking.supplier_name ?? form.supplier_name ?? activeBooking.supplier_city}`,
        attachment_names: ['pro-forma-invoice.pdf', 'packing-draft.pdf'],
      })
      await loadOperatingData(activeBooking.id)
      await refresh()
      setReleaseMessage('Supplier email ingested and matched to this order.')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  function handleAdminLogin(event: FormEvent) {
    event.preventDefault()
    if (!adminEmail.includes('@') || !adminPassword.trim()) {
      setAdminLoginError('Enter an admin email and password to open the operations workspace.')
      return
    }
    setAdminLoginError(null)
    setReleaseMessage(null)
    setError(null)
    setBrowserPath('/admin')
    setWorkspaceMode('admin')
    setAdminView('overview')
  }

  function openCustomerPortal() {
    setBrowserPath('/')
    setWorkspaceMode('customer')
    setView('book')
    setAdminPassword('')
    setAdminLoginError(null)
  }

  function updateCategory(value: CargoCategory) {
    const defaults = categoryDefaults[value]
    setForm((current) => ({
      ...current,
      cargo_category: value,
      weight_kg_estimate: defaults.weight,
    }))
  }

  async function runBookingSearch(payload: BookingPayload) {
    setLoading(true)
    setError(null)
    setReleaseMessage(null)
    try {
      const result = await createBooking({ ...payload, ...profile })
      setMatch(result)
      setActiveOpsBookingId(result.booking.id)
      setSupplierInstructions(null)
      await refresh()
      await loadOperatingData(result.booking.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not submit booking')
    } finally {
      setLoading(false)
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    await runBookingSearch(form)
  }

  async function handleConfirm() {
    if (!match) return
    setLoading(true)
    setError(null)
    try {
      const confirmation = await confirmBooking(match.booking.id)
      setActiveOpsBookingId(confirmation.booking.id)
      await refresh()
      await loadOperatingData(confirmation.booking.id)
      setSupplierInstructions(confirmation.supplier_instructions)
      setMatch((current) =>
        current
          ? {
              ...current,
              booking: confirmation.booking,
            }
          : current,
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not confirm booking')
    } finally {
      setLoading(false)
    }
  }

  const isConfirmed = match?.booking.status === 'confirmed'

  async function loadCarrierOptions(containerId: string) {
    setError(null)
    try {
      const options = await getCarrierOptions(containerId)
      setCarrierOptions((current) => ({ ...current, [containerId]: options }))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load carrier options')
    }
  }

  async function handleCommit(container: Container, option?: CarrierOption) {
    setLoading(true)
    setError(null)
    try {
      const result = await commitContainer(container.id, option)
      await refresh()
      setReleaseMessage(
        result.selected_carrier
          ? `${container.id} locked in with ${result.selected_carrier.carrier_name} on ${result.selected_carrier.sailing_date}.`
          : `${container.id} locked in.`,
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not commit container')
    } finally {
      setLoading(false)
    }
  }

  async function handleReleaseCheck() {
    setLoading(true)
    setError(null)
    try {
      const results = await runReleaseChecks()
      await refresh()
      const released = results.filter((result) => result.released)
      setReleaseMessage(
        released.length
          ? `${released.length} container${released.length === 1 ? '' : 's'} ready for delivery.`
          : 'No delivery blockers changed.',
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not run release checks')
    } finally {
      setLoading(false)
    }
  }

  async function handleDocumentUpload(documentType: DocumentType) {
    if (!activeBooking) return
    setLoading(true)
    setError(null)
    try {
      await uploadDocument(activeBooking.id, documentType, `${activeBooking.id}-${documentType}.pdf`)
      await loadOperatingData(activeBooking.id)
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not upload document')
    } finally {
      setLoading(false)
    }
  }

  async function handleApproveDocument(documentId: string) {
    if (!activeBooking) return
    setLoading(true)
    setError(null)
    try {
      await approveDocument(documentId)
      await loadOperatingData(activeBooking.id)
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not approve document')
    } finally {
      setLoading(false)
    }
  }

  async function handleAddEvent() {
    await handleShipmentEvent('warehouse_received', 'Warehouse received cargo', 'Warehouse receipt added.')
  }

  async function handleShipmentEvent(stage: ShipmentEvent['stage'], label: string, successMessage: string) {
    if (!activeBooking) return
    setLoading(true)
    setError(null)
    setReleaseMessage(null)
    try {
      await addEvent(activeBooking.id, stage, label)
      await loadOperatingData(activeBooking.id)
      await refresh()
      setReleaseMessage(successMessage)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not add event')
    } finally {
      setLoading(false)
    }
  }

  async function handleSupplierLink() {
    if (!activeBooking) return
    setLoading(true)
    setError(null)
    try {
      const link = await createSupplierLink(activeBooking.id)
      setSupplierLink(link)
      const portal = await supplierReady(link.token, activeBooking.cargo_ready_date_latest)
      setSupplierPortal(portal)
      await loadOperatingData(activeBooking.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create supplier link')
    } finally {
      setLoading(false)
    }
  }

  async function handleInviteBroker() {
    if (!activeBooking) return
    setLoading(true)
    setError(null)
    setBrokerInviteMessage(null)
    try {
      const link = await createBrokerLink(activeBooking.id)
      setBrokerLink(link)
      const url = `${globalThis.location?.origin ?? ''}/broker/${link.token}`
      let copied = false
      try {
        await globalThis.navigator?.clipboard?.writeText(url)
        copied = true
      } catch {
        copied = false
      }
      setBrokerInviteMessage(
        copied
          ? 'Broker link copied to clipboard. Send it to your customs broker.'
          : 'Broker link ready. Copy the URL below and send it to your customs broker.',
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create broker link')
    } finally {
      setLoading(false)
    }
  }

  async function handleInviteWarehouse() {
    if (!activeBooking) return
    setLoading(true)
    setError(null)
    setWarehouseInviteMessage(null)
    try {
      const link = await createWarehouseLink(activeBooking.id)
      setWarehouseLink(link)
      const url = `${globalThis.location?.origin ?? ''}/warehouse/${link.token}`
      let copied = false
      try {
        await globalThis.navigator?.clipboard?.writeText(url)
        copied = true
      } catch {
        copied = false
      }
      setWarehouseInviteMessage(
        copied
          ? 'Warehouse link copied to clipboard. Send it to the warehouse contact.'
          : 'Warehouse link ready. Copy the URL below and send it to the warehouse contact.',
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create warehouse link')
    } finally {
      setLoading(false)
    }
  }

  async function handleInviteCarrier() {
    if (!activeBooking) return
    setLoading(true)
    setError(null)
    setCarrierInviteMessage(null)
    try {
      const link = await createCarrierLink(activeBooking.id)
      setCarrierLink(link)
      const url = `${globalThis.location?.origin ?? ''}/carrier/${link.token}`
      let copied = false
      try {
        await globalThis.navigator?.clipboard?.writeText(url)
        copied = true
      } catch {
        copied = false
      }
      setCarrierInviteMessage(
        copied
          ? 'Carrier link copied to clipboard. Send it to the carrier contact.'
          : 'Carrier link ready. Copy the URL below and send it to the carrier contact.',
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create carrier link')
    } finally {
      setLoading(false)
    }
  }

  async function handleInviteTrucker() {
    if (!activeBooking) return
    setLoading(true)
    setError(null)
    setTruckerInviteMessage(null)
    try {
      const link = await createTruckerLink(activeBooking.id)
      setTruckerLink(link)
      const url = `${globalThis.location?.origin ?? ''}/trucker/${link.token}`
      let copied = false
      try {
        await globalThis.navigator?.clipboard?.writeText(url)
        copied = true
      } catch {
        copied = false
      }
      setTruckerInviteMessage(
        copied
          ? 'Trucker link copied to clipboard. Send it to the destination trucker.'
          : 'Trucker link ready. Copy the URL below and send it to the destination trucker.',
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create trucker link')
    } finally {
      setLoading(false)
    }
  }

  async function handleSupplierUpload() {
    if (!supplierLink || !activeBooking) return
    setLoading(true)
    setError(null)
    try {
      await uploadSupplierDocument(supplierLink.token, 'packing_list')
      const portal = await supplierReady(supplierLink.token, activeBooking.cargo_ready_date_latest)
      setSupplierPortal(portal)
      await loadOperatingData(activeBooking.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not upload supplier document')
    } finally {
      setLoading(false)
    }
  }

  async function handleMarkPaid() {
    if (!invoice || !activeBooking) return
    setLoading(true)
    setError(null)
    try {
      await markInvoicePaid(invoice.id)
      await loadOperatingData(activeBooking.id)
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not mark invoice paid')
    } finally {
      setLoading(false)
    }
  }

  async function handleCustomsClear() {
    if (!customsProfile || !activeBooking) return
    setLoading(true)
    setError(null)
    try {
      const updated = await updateCustomsProfile(activeBooking.id, { customs_status: 'cleared' })
      setCustomsProfile(updated)
      await loadOperatingData(activeBooking.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not refresh customs')
    } finally {
      setLoading(false)
    }
  }

  async function handleDeliveryPlanSave() {
    if (!activeBooking || !deliveryPlan) return
    setLoading(true)
    setError(null)
    setReleaseMessage(null)
    try {
      const updated = await updateDeliveryPlan(activeBooking.id, {
        delivery_method: deliveryPlan.delivery_method,
        destination_address: deliveryPlan.destination_address,
        destination_contact_name: deliveryPlan.destination_contact_name,
        destination_contact_phone: deliveryPlan.destination_contact_phone,
        delivery_window_start: deliveryPlan.delivery_window_start,
        delivery_window_end: deliveryPlan.delivery_window_end,
        equipment_required: deliveryPlan.equipment_required,
        notes: deliveryPlan.notes,
      })
      setDeliveryPlan(updated)
      await loadOperatingData(activeBooking.id)
      setReleaseMessage('Delivery details saved.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save delivery details')
    } finally {
      setLoading(false)
    }
  }

  async function handleBookDelivery() {
    if (!activeBooking || !deliveryPlan) return
    setLoading(true)
    setError(null)
    setReleaseMessage(null)
    try {
      const updated = await bookDeliveryPlan(deliveryPlan.id)
      setDeliveryPlan(updated)
      await loadOperatingData(activeBooking.id)
      setReleaseMessage('Delivery booked.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delivery cannot be booked yet')
    } finally {
      setLoading(false)
    }
  }

  async function handleMarkDelivered() {
    if (!activeBooking || !deliveryPlan) return
    setLoading(true)
    setError(null)
    setReleaseMessage(null)
    try {
      const updated = await markDeliveryDelivered(deliveryPlan.id)
      setDeliveryPlan(updated)
      await loadOperatingData(activeBooking.id)
      await refresh()
      setReleaseMessage('Delivery marked complete.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not mark delivery complete')
    } finally {
      setLoading(false)
    }
  }

  async function handleCreateProductionPlan() {
    if (!activeBooking) return
    setLoading(true)
    setError(null)
    try {
      const goodsValue = Math.max(customsProfile?.goods_value_usd ?? activeBooking.total_cost_usd ?? 6000, 1000)
      await createPurchaseOrder({
        booking_id: activeBooking.id,
        order_reference: `PO-${activeBooking.id.replace('BKG-', '')}`,
        buyer_company_name: profile.importer_company_name,
        supplier_name: activeBooking.supplier_name ?? `${activeBooking.supplier_city} supplier`,
        product_summary: activeBooking.cargo_description ?? sourceLabel(activeBooking.cargo_category),
        goods_value: goodsValue,
        deposit_amount: Math.round(goodsValue * 0.3),
        balance_amount: Math.round(goodsValue * 0.7),
        production_due_date: formatDateInput(21),
        cargo_ready_target_date: activeBooking.cargo_ready_date_latest,
        inspection_required: true,
      })
      await loadOperatingData(activeBooking.id)
      await refresh()
      setReleaseMessage('Production plan created with Supplier Pay approval ready.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create production plan')
    } finally {
      setLoading(false)
    }
  }

  async function handleCompleteMilestone(milestoneId: string, label: string) {
    if (!activeBooking) return
    setLoading(true)
    setError(null)
    setReleaseMessage(null)
    try {
      await completeProductionMilestone(milestoneId, `${label} completed from the Ship Hoppa order workflow.`)
      await loadOperatingData(activeBooking.id)
      await refresh()
      setReleaseMessage(`${label} marked complete.`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not complete milestone')
    } finally {
      setLoading(false)
    }
  }

  async function handleSupplierPayMarkPaid() {
    if (!activeBooking || !activeSupplierPayRequest) return
    setLoading(true)
    setError(null)
    try {
      await markSupplierPayPaid(activeSupplierPayRequest.id, 'Paid outside Ship Hoppa. Proof can be added later if needed.')
      await loadOperatingData(activeBooking.id)
      await refresh()
      setReleaseMessage('Supplier payment marked as paid.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update Supplier Pay')
    } finally {
      setLoading(false)
    }
  }

  function bookSailing(sailing: SailingSearchResult) {
    setForm((current) => ({
      ...current,
      preferred_sailing_option_id: sailing.sailing_option_id,
      preferred_container_id: sailing.container_id ?? undefined,
    }))
    setView('book')
  }

  async function checkAlternativeSailing(sailing: SailingSearchResult) {
    const nextForm = {
      ...form,
      preferred_sailing_option_id: sailing.sailing_option_id,
      preferred_container_id: sailing.container_id ?? undefined,
    }
    setForm(nextForm)
    await runBookingSearch(nextForm)
  }

  const blockedShipmentCount = bookings.filter((booking) => booking.release_status === 'blocked').length
  const unpaidShipmentCount = bookings.filter((booking) => booking.payment_status !== 'paid').length
  const exceptionBookings = useMemo(() => bookings.filter(needsAdminReview), [bookings])
  const documentQueueCount = bookings.filter((booking) => booking.checklist_status !== 'complete').length
  const containerDecisionCount = containers.filter((container) => container.status !== 'committed').length
  const trackingExceptionCount = bookings.filter((booking) => booking.exception_count > 0).length
  const adminNavItems: { view: AdminView; label: string; icon: ReactNode }[] = [
    { view: 'overview', label: 'Overview', icon: <Gauge size={17} /> },
    { view: 'containers', label: 'Containers', icon: <ContainerIcon size={17} /> },
    { view: 'exceptions', label: 'Exceptions', icon: <PackageCheck size={17} /> },
    { view: 'documents', label: 'Documents', icon: <FileText size={17} /> },
    { view: 'tracking', label: 'Tracking', icon: <Truck size={17} /> },
    { view: 'payments', label: 'Payments', icon: <Receipt size={17} /> },
    { view: 'customs', label: 'Customs', icon: <ShieldCheck size={17} /> },
    { view: 'automation', label: 'Automation', icon: <RefreshCw size={17} /> },
    { view: 'audit', label: 'Audit log', icon: <Bell size={17} /> },
  ]
  const adminTitles: Record<AdminView, { eyebrow: string; title: string; summary: string; automation: string }> = {
    overview: {
      eyebrow: 'Admin workspace',
      title: 'Exception dashboard',
      summary: 'Shows only what needs human attention. Normal bookings should flow through automation without an operator touching them.',
      automation: 'Automated: booking match, cutoff feasibility, checklist creation, invoice generation, event creation, and release checks.',
    },
    containers: {
      eyebrow: 'Container control',
      title: 'Shared containers',
      summary: 'Container-level decisions: sailing source, space, weight, carrier confirmation, and cutoff protection.',
      automation: 'Automated: booking assignment, load calculations, cutoff fallback, and carrier option ranking. Human needed only to confirm a carrier until live integrations are connected.',
    },
    exceptions: {
      eyebrow: 'Exception queue',
      title: `${exceptionBookings.length} shipments need review`,
      summary: 'This is not a manual processing list. It is the queue of shipments where automation needs a human decision or override.',
      automation: 'Automated: normal status movement. Human needed for admin review, cutoff risk, missing documents, unpaid release, customs holds, or warehouse variance.',
    },
    documents: {
      eyebrow: 'Document control',
      title: activeBooking ? `${activeBooking.id} documents` : 'Documents',
      summary: 'Document exceptions for the selected shipment: missing, rejected, or waiting-for-approval files.',
      automation: 'Automated: requirement generation and upload capture. Human needed for approval or rejection until OCR/compliance checks are integrated.',
    },
    tracking: {
      eyebrow: 'Tracking control',
      title: activeBooking ? `${activeBooking.id} movement` : 'Tracking',
      summary: 'Tracking exceptions and manual event overrides for the selected shipment.',
      automation: 'Automated: booking, supplier, warehouse, and container events. Human needed only when a real-world event arrives outside the system.',
    },
    payments: {
      eyebrow: 'Finance control',
      title: activeBooking ? `${activeBooking.id} payment and release` : 'Payments',
      summary: 'Payment state, invoice lines, and release holds for the selected shipment.',
      automation: 'Automated: invoice line creation and release-hold checks. Human needed only to mark manual payment or waive a hold until payment webhooks are connected.',
    },
    customs: {
      eyebrow: 'Customs control',
      title: activeBooking ? `${activeBooking.id} customs` : 'Customs',
      summary: 'Customs and landed-cost exceptions for the selected shipment.',
      automation: 'Automated: landed-cost estimate and customs checklist state. Human needed for broker handoff, holds, queries, and final clearance.',
    },
    automation: {
      eyebrow: 'Automation engine',
      title: 'Shipment lifecycle and chase',
      summary: 'State machine, fact extraction, missing-data detection, and partner chase queue. Run automation to advance shipments and detect issues.',
      automation: 'Automated: lifecycle state derivation, fact extraction from messages, missing-data detection, and partner chase message generation.',
    },
    audit: {
      eyebrow: 'Audit log',
      title: 'System decisions',
      summary: 'A read-only record of automation decisions, operator actions, and notifications.',
      automation: 'Automated: every system or operator decision writes an audit event. Human action should not be required here.',
    },
  }
  const adminTabAudit: { view: AdminView; label: string; necessary: string; human: string }[] = [
    {
      view: 'overview',
      label: 'Overview',
      necessary: 'Yes. It should be the first screen because it prioritises exceptions.',
      human: 'Choose which exception to resolve next.',
    },
    {
      view: 'containers',
      label: 'Containers',
      necessary: 'Yes. Container commitment is the main operational risk.',
      human: 'Confirm carrier/sailing when source confidence is not confirmed.',
    },
    {
      view: 'exceptions',
      label: 'Exceptions',
      necessary: 'Yes. This replaces vague shipment work.',
      human: 'Resolve only shipments that automation flags.',
    },
    {
      view: 'documents',
      label: 'Documents',
      necessary: 'Yes for v1. Later this can shrink after OCR and compliance automation.',
      human: 'Approve or reject files when rules cannot decide.',
    },
    {
      view: 'tracking',
      label: 'Tracking',
      necessary: 'Yes, but only for manual event overrides.',
      human: 'Add a real-world event missed by integrations.',
    },
    {
      view: 'payments',
      label: 'Payments',
      necessary: 'Yes until payment processor webhooks are live.',
      human: 'Mark bank transfer paid or waive a release hold.',
    },
    {
      view: 'customs',
      label: 'Customs',
      necessary: 'Yes because broker and biosecurity outcomes need oversight.',
      human: 'Resolve customs queries, holds, and clearance.',
    },
    {
      view: 'automation',
      label: 'Automation',
      necessary: 'Yes. It runs the state machine and partner chase system.',
      human: 'Trigger automation cycles, review stale data, and monitor extraction quality.',
    },
    {
      view: 'audit',
      label: 'Audit log',
      necessary: 'Yes, but read-only. It is not daily work.',
      human: 'Investigate why automation or an operator made a decision.',
    },
  ]
  const customerPhases: CustomerPhase[] = [
    {
      id: 'order',
      number: '1',
      label: 'Order',
      summary: 'Place the order, run production, inspect, get cargo ready to ship',
      defaultView: 'supplier',
      views: [
        { view: 'supplier', label: 'Supplier', icon: <UserRound size={16} /> },
        { view: 'production', label: 'Production', icon: <ClipboardCheck size={16} /> },
        { view: 'inspection', label: 'Inspection', icon: <Scale size={16} /> },
        { view: 'supplier_pay', label: 'Supplier Pay', icon: <CircleDollarSign size={16} /> },
        { view: 'order_docs', label: 'Docs', icon: <FileText size={16} /> },
      ],
    },
    {
      id: 'ship',
      number: '2',
      label: 'Ship',
      summary: 'FCL, MCL or LCL transport from origin port to destination port',
      defaultView: 'book',
      views: [
        { view: 'book', label: 'Cargo', icon: <PackageCheck size={16} /> },
        { view: 'ship_docs', label: 'Ship Docs', icon: <FileText size={16} /> },
        { view: 'handoff', label: 'Pickup', icon: <Truck size={16} /> },
        { view: 'sailings', label: 'Sailings', icon: <CalendarClock size={16} /> },
        { view: 'tracking', label: 'Tracking', icon: <Truck size={16} /> },
      ],
    },
    {
      id: 'clear',
      number: '3',
      label: 'Deliver',
      summary: 'From the moment the ship docks to arrival at your warehouse',
      defaultView: 'money',
      views: [
        { view: 'customs', label: 'Customs', icon: <ShieldCheck size={16} /> },
        { view: 'money', label: 'Payments', icon: <Receipt size={16} /> },
        { view: 'delivery', label: 'Delivery', icon: <MapPin size={16} /> },
      ],
    },
    {
      id: 'account',
      number: '',
      label: 'Account',
      summary: 'Saved details',
      defaultView: 'profile',
      views: [
        { view: 'profile', label: 'Profile', icon: <UserRound size={16} /> },
        { view: 'integrations', label: 'Integrations', icon: <ArrowRight size={16} /> },
        { view: 'help', label: 'Help', icon: <CircleHelp size={16} /> },
      ],
    },
  ]
  const activeCustomerPhase =
    customerPhases.find((phase) => phase.views.some((item) => item.view === view)) ?? customerPhases[1]
  const customerWorkflowPhases = customerPhases.filter((phase) => phase.id !== 'account')
  const activeViewIntro = viewIntroCopy(view, activeCustomerPhase)
  const customerPhaseItems = useMemo<PhaseOverviewItem[]>(() => {
    if (activeCustomerPhase.id === 'order') {
      const supplierStatus: PhaseStepStatus = activeBooking?.supplier_name || form.supplier_name ? 'ready' : 'attention'
      const productionStatus: PhaseStepStatus = activePurchaseOrder ? (openApprovals.length ? 'attention' : 'ready') : 'attention'
      const documentStatus: PhaseStepStatus = orderMissingDocumentCount ? 'attention' : orderApprovedDocumentCount ? 'ready' : 'idle'
      const supplierPayStatus: PhaseStepStatus = activeSupplierPayRequest
        ? activeSupplierPayRequest.status === 'paid' || activeSupplierPayRequest.marked_paid_at
          ? 'ready'
          : 'attention'
        : 'idle'
      return [
        {
          view: 'supplier',
          icon: <UserRound size={18} />,
          title: 'Supplier',
          detail: activeBooking?.supplier_name ?? form.supplier_name ?? 'Add supplier details',
          meta: `${form.supplier_city || activeBooking?.supplier_city || 'Origin city'}, ${form.supplier_country || activeBooking?.supplier_country || 'country TBC'}`,
          status: supplierStatus,
          statusLabel: supplierStatus === 'ready' ? 'Saved' : 'Needed',
          active: view === 'supplier',
        },
        {
          view: 'production',
          icon: <ClipboardCheck size={18} />,
          title: 'Production',
          detail: activePurchaseOrder ? activePurchaseOrder.product_summary : 'Create the order plan',
          meta: activeProductionMilestones.length ? `${activeProductionMilestones.length} milestones tracked` : 'No production plan yet',
          status: productionStatus,
          statusLabel: activePurchaseOrder ? (openApprovals.length ? `${openApprovals.length} approval${openApprovals.length === 1 ? '' : 's'}` : 'On track') : 'Start',
          active: view === 'production',
        },
        {
          view: 'inspection',
          icon: <Scale size={18} />,
          title: 'Inspection',
          detail: activeQualityInspection?.inspection_required ? 'QC before release' : 'Supplier photo check',
          meta: activeQualityInspection
            ? sourceLabel(activeQualityInspection.result)
            : 'Supplier photos or third-party inspection',
          status: activeQualityInspection?.result === 'failed' ? 'attention' : activeQualityInspection ? 'ready' : 'idle',
          statusLabel: activeQualityInspection ? sourceLabel(activeQualityInspection.result) : 'Optional',
          active: view === 'inspection',
        },
        {
          view: 'supplier_pay',
          icon: <CircleDollarSign size={18} />,
          title: 'Supplier Pay',
          detail: activeSupplierPayRequest ? `${activeSupplierPayRequest.supplier_name} · ${formatMoney(activeSupplierPayRequest.amount)}` : 'Optional supplier payment',
          meta: activeSupplierPayRequest ? sourceLabel(activeSupplierPayRequest.status) : 'Add when the supplier needs paying',
          status: supplierPayStatus,
          statusLabel: activeSupplierPayRequest ? sourceLabel(activeSupplierPayRequest.status) : 'Optional',
          active: view === 'supplier_pay',
        },
        {
          view: 'order_docs',
          icon: <FileText size={18} />,
          title: 'Order Docs',
          detail: checklist ? `${orderApprovedDocumentCount}/${orderDocumentRequirements.length || 3} approved` : 'Checklist loading',
          meta: orderMissingDocumentCount ? `${orderMissingDocumentCount} still needed` : 'Commercial proof and product files',
          status: documentStatus,
          statusLabel: orderMissingDocumentCount ? 'Needs files' : orderApprovedDocumentCount ? 'Ready' : 'Waiting',
          active: view === 'order_docs',
        },
      ]
    }

    if (activeCustomerPhase.id === 'ship') {
      const shipDocStatus: PhaseStepStatus = shipMissingDocumentCount ? 'attention' : shipApprovedDocumentCount ? 'ready' : 'idle'
      const handoffStatus: PhaseStepStatus = activeBooking?.pickup_address || form.pickup_address ? 'ready' : 'attention'
      const sailingStatus: PhaseStepStatus = selectedSailing || visibleSailing ? 'ready' : 'idle'
      const trackingStatus: PhaseStepStatus = activeBooking ? (activeBooking.exception_count ? 'attention' : 'ready') : 'idle'
      const latestEvent = events[events.length - 1]
      return [
        {
          view: 'book',
          icon: <PackageCheck size={18} />,
          title: 'Book',
          detail: match?.container ? match.container.id : activeBooking ? activeBooking.id : 'Find a container',
          meta: match?.container
            ? `${formatMeasure(match.booking.cbm_estimate, 'CBM')} · ${formatMoney(match.booking.total_cost_usd)}`
            : `${formatMeasure(form.cbm_estimate, 'CBM')} ready to search`,
          status: match?.container || activeBooking ? 'ready' : 'attention',
          statusLabel: match?.container ? 'Matched' : activeBooking ? 'Booked' : 'Search',
          active: view === 'book',
        },
        {
          view: 'ship_docs',
          icon: <FileText size={18} />,
          title: 'Ship Docs',
          detail: checklist ? `${shipApprovedDocumentCount}/${shipDocumentRequirements.length || 6} approved` : 'Checklist loading',
          meta: shipMissingDocumentCount ? `${shipMissingDocumentCount} still needed` : 'Packing and movement documents',
          status: shipDocStatus,
          statusLabel: shipMissingDocumentCount ? 'Needs files' : shipApprovedDocumentCount ? 'Ready' : 'Waiting',
          active: view === 'ship_docs',
        },
        {
          view: 'handoff',
          icon: <Truck size={18} />,
          title: 'Pickup',
          detail: deliveryModeLabels[activeBooking?.delivery_mode ?? form.delivery_mode],
          meta: formatDateShort(activeBooking?.warehouse_receipt_cutoff ?? match?.booking.warehouse_receipt_cutoff ?? selectedContainer?.warehouse_receipt_cutoff_date),
          status: handoffStatus,
          statusLabel: handoffStatus === 'ready' ? 'Planned' : 'Needed',
          active: view === 'handoff',
        },
        {
          view: 'sailings',
          icon: <CalendarClock size={18} />,
          title: 'Sailings',
          detail: visibleSailing ? `${sailingOriginPort(visibleSailing)} -> ${sailingDestinationPort(visibleSailing)}` : 'Choose a sailing window',
          meta: visibleSailing ? `${formatDateShort(visibleSailing.etd)} -> ${formatDateShort(visibleSailing.eta)}` : `${filteredSailings.length} options`,
          status: sailingStatus,
          statusLabel: selectedSailing ? 'Selected' : visibleSailing ? `${filteredSailings.length} options` : 'Browse',
          active: view === 'sailings',
        },
        {
          view: 'tracking',
          icon: <Truck size={18} />,
          title: 'Tracking',
          detail: activeBooking ? activeBooking.id : 'No shipment yet',
          meta: latestEvent ? `${sourceLabel(latestEvent.stage)} · ${formatDateShort(latestEvent.occurred_at ?? latestEvent.estimated_at)}` : `ETA ${formatDateShort(activeContainer?.estimated_arrival ?? activeSailing?.eta)}`,
          status: trackingStatus,
          statusLabel: activeBooking?.exception_count ? 'Check' : activeBooking ? 'Live' : 'Waiting',
          active: view === 'tracking',
        },
      ]
    }

    if (activeCustomerPhase.id === 'clear') {
      const paymentStatus: PhaseStepStatus = invoice?.status === 'paid' || activeBooking?.payment_status === 'paid' ? 'ready' : 'attention'
      const customsStatus: PhaseStepStatus = customsProfile?.customs_status === 'cleared' ? 'ready' : 'attention'
      const releaseStepStatus: PhaseStepStatus = releaseStatus?.can_release ? 'ready' : activeReleaseHolds.length ? 'attention' : 'idle'
      return [
        {
          view: 'money',
          icon: <Receipt size={18} />,
          title: 'Payments',
          detail: invoice ? `${formatMoney(invoice.total_usd)} invoice` : 'Invoice loading',
          meta: invoice ? sourceLabel(invoice.status) : 'Generated from booking fees',
          status: paymentStatus,
          statusLabel: invoice?.status === 'paid' || activeBooking?.payment_status === 'paid' ? 'Paid' : 'Open',
          active: view === 'money',
        },
        {
          view: 'customs',
          icon: <ShieldCheck size={18} />,
          title: 'Customs',
          detail: `${formatMoney(customsProfile?.landed_cost_estimate_usd)} estimated`,
          meta: formatCustomsStatus(customsProfile?.customs_status),
          status: customsStatus,
          statusLabel: customsProfile?.customs_status === 'cleared' ? 'Clear' : 'In progress',
          active: view === 'customs',
        },
        {
          view: 'money',
          icon: <Gauge size={18} />,
          title: 'Release',
          detail: releaseStatus?.can_release ? 'Freight can be released' : `${activeReleaseHolds.length} active hold${activeReleaseHolds.length === 1 ? '' : 's'}`,
          meta: releaseStatus ? sourceLabel(releaseStatus.release_status) : 'Checks loading',
          status: releaseStepStatus,
          statusLabel: releaseStatus?.can_release ? 'Ready' : activeReleaseHolds.length ? 'Blocked' : 'Checking',
          active: view === 'delivery',
        },
        {
          view: 'delivery',
          icon: <MapPin size={18} />,
          title: 'Delivery',
          detail: `${profile.delivery_city}, ${profile.delivery_country}`,
          meta: releaseStatus?.can_release ? 'Ready to dispatch' : 'Waits for release',
          status: releaseStatus?.can_release ? 'ready' : 'idle',
          statusLabel: releaseStatus?.can_release ? 'Ready' : 'Queued',
          active: view === 'delivery',
        },
      ]
    }

    const connectedIntegrations = accountIntegrations.filter((integration) => integration.status === 'connected').length
    return [
      {
        view: 'profile',
        icon: <UserRound size={18} />,
        title: 'Company profile',
        detail: profile.importer_company_name,
        meta: `${profile.importer_contact_name} · ${profile.importer_email}`,
        status: 'ready',
        statusLabel: 'Saved',
        active: view === 'profile',
      },
      {
        view: 'profile',
        icon: <MapPin size={18} />,
        title: 'Delivery default',
        detail: `${profile.delivery_city}, ${profile.delivery_country}`,
        meta: profile.delivery_postcode ? `Postcode ${profile.delivery_postcode}` : 'No postcode saved',
        status: profile.delivery_city ? 'ready' : 'attention',
        statusLabel: profile.delivery_city ? 'Saved' : 'Add',
        active: false,
      },
      {
        view: 'profile',
        icon: <Truck size={18} />,
        title: 'Supplier default',
        detail: supplierLocationInput || 'No supplier selected',
        meta: `Default service: ${deliveryModeLabels[form.delivery_mode]}`,
        status: supplierLocationInput ? 'ready' : 'idle',
        statusLabel: supplierLocationInput ? 'Ready' : 'Optional',
        active: false,
      },
      {
        view: 'integrations',
        icon: <ArrowRight size={18} />,
        title: 'Integrations',
        detail: accountIntegrations.length
          ? `${connectedIntegrations} of ${accountIntegrations.length} connected`
          : 'Alibaba and inbox connections',
        meta: 'Optional wires into existing workflows',
        status: connectedIntegrations ? 'ready' : 'idle',
        statusLabel: connectedIntegrations ? 'Connected' : 'Optional',
        active: view === 'integrations',
      },
      {
        view: 'help',
        icon: <CircleHelp size={18} />,
        title: 'Help',
        detail: 'Guided handoffs',
        meta: 'Importer, supplier, courier, broker',
        status: 'idle',
        statusLabel: 'Guide',
        active: view === 'help',
      },
    ]
  }, [
    activeBooking,
    activeContainer,
    activeCustomerPhase.id,
    accountIntegrations,
    activeProductionMilestones.length,
    activePurchaseOrder,
    activeQualityInspection,
    activeReleaseHolds.length,
    activeSailing,
    activeSupplierPayRequest,
    checklist,
    customsProfile,
    events,
    filteredSailings.length,
    form.cbm_estimate,
    form.delivery_mode,
    form.pickup_address,
    form.supplier_country,
    form.supplier_name,
    form.supplier_city,
    invoice,
    match,
    openApprovals.length,
    orderApprovedDocumentCount,
    orderDocumentRequirements.length,
    orderMissingDocumentCount,
    profile,
    releaseStatus,
    selectedSailing,
    selectedContainer,
    shipApprovedDocumentCount,
    shipDocumentRequirements.length,
    shipMissingDocumentCount,
    supplierLocationInput,
    view,
    visibleSailing,
  ])

  if (workspaceMode === 'broker-portal') {
    const brokerToken = brokerTokenFromPath()
    if (brokerToken) {
      return <BrokerPortalView token={brokerToken} />
    }
  }

  if (workspaceMode === 'warehouse-portal') {
    const whToken = warehouseTokenFromPath()
    if (whToken) {
      return <WarehousePortalView token={whToken} />
    }
  }

  if (workspaceMode === 'carrier-portal') {
    const carrierToken = carrierTokenFromPath()
    if (carrierToken) {
      return <CarrierPortalView token={carrierToken} />
    }
  }

  if (workspaceMode === 'trucker-portal') {
    const truckerToken = truckerTokenFromPath()
    if (truckerToken) {
      return <TruckerPortalView token={truckerToken} />
    }
  }

  if (workspaceMode === 'admin-login') {
    return (
      <div className="app-shell admin-login-shell">
        <header className="topbar admin-topbar">
          <Logo />
          <button className="secondary-action small" type="button" onClick={openCustomerPortal}>
            <ArrowRight size={15} />
            Customer portal
          </button>
        </header>
        <main className="admin-login-main">
          <section className="admin-login-card">
            <div>
              <p className="eyebrow">Ship Hoppa admin</p>
              <h1>Operations login</h1>
              <p>Internal exception queues for containers, shipments, documents, payments, customs, and release checks.</p>
            </div>
            <form onSubmit={handleAdminLogin}>
              <label>
                <span>Admin email</span>
                <input
                  type="email"
                  value={adminEmail}
                  onChange={(event) => setAdminEmail(event.target.value)}
                  autoComplete="username"
                />
              </label>
              <label>
                <span>Password</span>
                <input
                  type="password"
                  value={adminPassword}
                  onChange={(event) => setAdminPassword(event.target.value)}
                  autoComplete="current-password"
                  placeholder="Prototype password"
                />
              </label>
              {adminLoginError && <div className="notice error">{adminLoginError}</div>}
              <button className="primary-action" type="submit">
                <Gauge size={18} />
                Open admin workspace
              </button>
            </form>
          </section>
        </main>
      </div>
    )
  }

  if (workspaceMode === 'admin') {
    const currentAdminTitle = adminTitles[adminView]

    return (
      <div className="app-shell admin-app-shell">
        <header className="topbar admin-topbar admin-shell-topbar">
          <Logo />
          <div className="admin-topbar-title">
            <span>Internal admin</span>
            <strong>Ship Hoppa Operations</strong>
          </div>
          <button className="secondary-action small admin-exit-button" type="button" onClick={openCustomerPortal}>
            Customer portal
          </button>
        </header>

        <div className="admin-shell-layout">
          <aside className="admin-sidebar">
            <nav className="admin-nav" aria-label="Admin workspace">
              {adminNavItems.map((item) => (
                <button
                  className={adminView === item.view ? 'active' : ''}
                  type="button"
                  key={item.view}
                  onClick={() => setAdminView(item.view)}
                >
                  {item.icon}
                  {item.label}
                </button>
              ))}
            </nav>
          </aside>

        <main className="admin-main admin-content">
          {error && (
            <div className="notice error" role="alert">
              {error}
            </div>
          )}
          {releaseMessage && <div className="notice success">{releaseMessage}</div>}

          <section className="admin-page-heading">
            <div>
              <p className="eyebrow">{currentAdminTitle.eyebrow}</p>
              <h1>{currentAdminTitle.title}</h1>
              <p>{currentAdminTitle.summary}</p>
              <div className="admin-automation-note">
                <Check size={16} />
                <span>{currentAdminTitle.automation}</span>
              </div>
            </div>
            <button className="secondary-action" onClick={handleReleaseCheck} disabled={loading}>
              <RefreshCw size={17} />
              Run release checks
            </button>
          </section>

          {adminView === 'overview' && (
            <div className="workspace admin-workspace admin-dashboard">
              <section className="panel admin-panel full">
                <div className="admin-command-grid">
                  <button className="admin-command-card" type="button" onClick={() => setAdminView('containers')}>
                    <span>
                      <ContainerIcon size={19} />
                    </span>
                    <small>Containers</small>
                    <strong>{containers.length}</strong>
                    <em>Open container plan</em>
                  </button>
                  <button className="admin-command-card" type="button" onClick={() => setAdminView('exceptions')}>
                    <span>
                      <PackageCheck size={19} />
                    </span>
                    <small>Exceptions</small>
                    <strong>{exceptionBookings.length}</strong>
                    <em>Review automation stops</em>
                  </button>
                  <button className="admin-command-card urgent" type="button" onClick={() => setAdminView('payments')}>
                    <span>
                      <ShieldCheck size={19} />
                    </span>
                    <small>Blocked release</small>
                    <strong>{blockedShipmentCount}</strong>
                    <em>Clear delivery blockers</em>
                  </button>
                  <button className="admin-command-card" type="button" onClick={() => setAdminView('documents')}>
                    <span>
                      <FileText size={19} />
                    </span>
                    <small>Document queue</small>
                    <strong>{documentQueueCount}</strong>
                    <em>Missing or unapproved</em>
                  </button>
                </div>
              </section>

              <section className="panel admin-panel full">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Automation exceptions</p>
                    <h2>What still needs a human.</h2>
                  </div>
                  <ClipboardCheck size={24} />
                </div>
                <div className="ops-grid">
                  <div className="ops-card">
                    <strong>Container commitments</strong>
                    <span>{containerDecisionCount} containers still need carrier confirmation because live carrier booking data is not connected yet.</span>
                    <button className="secondary-action small" type="button" onClick={() => setAdminView('containers')}>
                      Open containers
                    </button>
                  </div>
                  <div className="ops-card">
                    <strong>Shipment exceptions</strong>
                    <span>{exceptionBookings.length} shipments need a human decision. Everything else should move automatically.</span>
                    <button className="secondary-action small" type="button" onClick={() => setAdminView('exceptions')}>
                      Open exceptions
                    </button>
                  </div>
                  <div className="ops-card">
                    <strong>Payments</strong>
                    <span>{unpaidShipmentCount} shipments are not marked paid because payment webhooks are not connected in v1.</span>
                    <button className="secondary-action small" type="button" onClick={() => setAdminView('payments')}>
                      Open payments
                    </button>
                  </div>
                </div>
              </section>

              <section className="panel admin-panel full">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Tab audit</p>
                    <h2>Why each admin tab exists.</h2>
                  </div>
                  <Check size={24} />
                </div>
                <div className="admin-tab-audit-grid">
                  {adminTabAudit.map((item) => (
                    <button className="admin-tab-audit-card" type="button" key={item.view} onClick={() => setAdminView(item.view)}>
                      <strong>{item.label}</strong>
                      <span>{item.necessary}</span>
                      <small>{item.human}</small>
                    </button>
                  ))}
                </div>
              </section>
            </div>
          )}

          {adminView === 'containers' && (
            <div className="workspace admin-workspace ops-workspace">
              <section className="panel admin-panel full">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Container control</p>
                    <h2>Planned shared containers.</h2>
                  </div>
                  <button className="secondary-action" onClick={handleReleaseCheck} disabled={loading}>
                    <RefreshCw size={17} />
                    Check blockers
                  </button>
                </div>
                <div className="admin-function-summary">
                  <DetailTile icon={<ContainerIcon size={18} />} label="Planned containers" value={`${containers.length}`} />
                  <DetailTile icon={<ClipboardCheck size={18} />} label="Matched shipments" value={`${bookings.length}`} />
                  <DetailTile icon={<ShieldCheck size={18} />} label="Blocked deliveries" value={`${blockedShipmentCount}`} />
                </div>
                <OpsWorldMap
                  containers={containers}
                  bookings={bookings}
                  onOpenBooking={(bookingId) => {
                    void openOpsBooking(bookingId)
                    setAdminView('exceptions')
                  }}
                />
                <div className="section-subhead ops-list-heading">
                  <strong>Container list</strong>
                  <span>Each card is one Ship Hoppa shared container sailing.</span>
                </div>
                <div className="ops-sailing-grid">
                  {containers.map((container) => {
                    const options = carrierOptions[container.id] ?? []
                    const shipmentBookings = bookings.filter((booking) => booking.container_id === container.id)
                    return (
                      <OpsSailingCard
                        key={container.id}
                        container={container}
                        shipmentBookings={shipmentBookings}
                        options={options}
                        loading={loading}
                        onLoadCarrierOptions={loadCarrierOptions}
                        onCommit={handleCommit}
                        onOpenBooking={(bookingId) => {
                          void openOpsBooking(bookingId)
                          setAdminView('exceptions')
                        }}
                      />
                    )
                  })}
                </div>
              </section>
            </div>
          )}

          {adminView === 'exceptions' && (
            <div className="workspace admin-workspace">
              <section className="panel admin-panel full">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Exception queue</p>
                    <h2>Select an exception to resolve.</h2>
                  </div>
                  <ClipboardCheck size={24} />
                </div>
                <div className="admin-function-summary">
                  <DetailTile icon={<PackageCheck size={18} />} label="Needs review" value={`${exceptionBookings.length}`} />
                  <DetailTile icon={<FileText size={18} />} label="Documents" value={`${documentQueueCount}`} />
                  <DetailTile icon={<Truck size={18} />} label="Tracking flags" value={`${trackingExceptionCount}`} />
                </div>
                <div className="ops-shipment-grid">
                  {exceptionBookings.slice(0, 12).map((booking) => (
                    <OpsShipmentCard
                      booking={booking}
                      key={booking.id}
                      selected={booking.id === activeBooking?.id}
                      onOpen={(bookingId) => {
                        void openOpsBooking(bookingId)
                      }}
                    />
                  ))}
                </div>
              </section>

              <section className="panel admin-panel full">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Selected exception</p>
                    <h2>{activeBooking ? `${activeBooking.id} resolution cards` : 'No shipment selected.'}</h2>
                  </div>
                  <button
                    className="secondary-action"
                    type="button"
                    onClick={() => activeBooking && loadOperatingData(activeBooking.id)}
                    disabled={!activeBooking || loading}
                  >
                    <RefreshCw size={17} />
                    Refresh
                  </button>
                </div>

                {activeBooking ? (
                  <div className="ops-selected-layout">
                    <div className="admin-function-summary">
                      <DetailTile icon={<FileText size={18} />} label="Documents" value={checklist ? sourceLabel(checklist.checklist_status) : 'Loading'} />
                      <DetailTile icon={<Truck size={18} />} label="Tracking" value={sourceLabel(activeBooking.tracking_status)} />
                      <DetailTile icon={<Receipt size={18} />} label="Payment" value={sourceLabel(activeBooking.payment_status)} />
                    </div>
                    <div className="exception-reason-row">
                      {bookingReviewReasons(activeBooking).map((reason) => (
                        <span key={reason}>{reason}</span>
                      ))}
                    </div>
                    <div className="ops-grid">
                      <div className="ops-card">
                        <strong>Documents</strong>
                        <span>{checklist ? sourceLabel(checklist.checklist_status) : 'Not loaded'}</span>
                        <button className="secondary-action small" type="button" onClick={() => setAdminView('documents')}>
                          Open documents
                        </button>
                      </div>
                      <div className="ops-card">
                        <strong>Movement</strong>
                        <span>{events.length ? `${events.length} events` : 'No events loaded'}</span>
                        <button className="secondary-action small" type="button" onClick={() => setAdminView('tracking')}>
                          Open tracking
                        </button>
                      </div>
                      <div className="ops-card">
                        <strong>Delivery blockers</strong>
                        <span>{releaseStatus ? sourceLabel(releaseStatus.release_status) : 'Not loaded'}</span>
                        <button className="secondary-action small" type="button" onClick={() => setAdminView('payments')}>
                          Open payments
                        </button>
                      </div>
                    </div>
                  </div>
	              ) : (
                  <div className="empty-state">
                    <ClipboardCheck size={42} />
                    <p>No exceptions need manual review right now.</p>
                  </div>
                )}
              </section>

              <section className="panel admin-panel full">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Automation queue</p>
                    <h2>{adminTasks.length ? `${adminTasks.length} open admin tasks` : 'No open admin tasks'}</h2>
                  </div>
                  <button
                    className="secondary-action"
                    type="button"
                    onClick={() => {
                      getAdminTasks({ status: 'open' }).then(setAdminTasks).catch(() => {})
                      getAdminTaskSummary().then(setAdminTaskSummary).catch(() => {})
                    }}
                  >
                    <RefreshCw size={17} />
                    Refresh
                  </button>
                </div>
                {adminTaskSummary && (
                  <div className="admin-function-summary">
                    <DetailTile icon={<ClipboardCheck size={18} />} label="Open" value={`${adminTaskSummary.total_open}`} />
                    <DetailTile icon={<PackageCheck size={18} />} label="Resolved" value={`${adminTaskSummary.total_done}`} />
                    <DetailTile icon={<FileText size={18} />} label="Waived" value={`${adminTaskSummary.total_waived}`} />
                  </div>
                )}
                {adminTasks.length > 0 ? (
                  <div className="ops-grid">
                    {adminTasks.map((task) => (
                      <div className="ops-card" key={task.id}>
                        <strong>{task.title}</strong>
                        <span>{task.task_type.replace(/_/g, ' ')}</span>
                        <span style={{ fontSize: '0.85em', opacity: 0.7 }}>Booking: {task.booking_id}</span>
                        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                          <button
                            className="secondary-action small"
                            type="button"
                            onClick={async () => {
                              await resolveAdminTask(task.id)
                              const tasks = await getAdminTasks({ status: 'open' })
                              setAdminTasks(tasks)
                              const summary = await getAdminTaskSummary()
                              setAdminTaskSummary(summary)
                            }}
                          >
                            Resolve
                          </button>
                          <button
                            className="secondary-action small"
                            type="button"
                            onClick={async () => {
                              await dismissAdminTask(task.id)
                              const tasks = await getAdminTasks({ status: 'open' })
                              setAdminTasks(tasks)
                              const summary = await getAdminTaskSummary()
                              setAdminTaskSummary(summary)
                            }}
                          >
                            Waive
                          </button>
                          <button
                            className="secondary-action small"
                            type="button"
                            onClick={() => {
                              void openOpsBooking(task.booking_id)
                            }}
                          >
                            Open shipment
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">
                    <ClipboardCheck size={42} />
                    <p>The automation queue is clear.</p>
                  </div>
                )}
              </section>
            </div>
          )}

          {adminView === 'documents' && (
            <section className="panel admin-panel full">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Document control</p>
                  <h2>{activeBooking ? `${activeBooking.id} required files` : 'No shipment selected.'}</h2>
                </div>
                <FileText size={24} />
              </div>
              {activeBooking ? (
                <>
                  <div className="admin-function-summary">
                    <DetailTile icon={<ClipboardCheck size={18} />} label="Required" value={`${requiredDocumentCount}`} />
                    <DetailTile icon={<FileText size={18} />} label="Uploaded" value={`${uploadedDocumentCount}`} />
                    <DetailTile icon={<Check size={18} />} label="Approved" value={`${approvedDocumentCount}`} />
                  </div>
                  <div className="document-grid">
                    {(checklist?.requirements ?? []).map((requirement) => (
                      <article className={`document-card ${requirement.status}`} key={requirement.id}>
                        <span className="document-icon">
                          <FileText size={18} />
                        </span>
                        <div>
                          <strong>{requirement.label}</strong>
                          <small>{requirement.reason}</small>
                        </div>
                        <button
                          className={requirement.status === 'approved' ? 'secondary-action small selected' : 'secondary-action small'}
                          type="button"
                          onClick={() => handleDocumentUpload(requirement.document_type)}
                          disabled={loading || requirement.status === 'approved'}
                        >
                          {sourceLabel(requirement.status)}
                        </button>
                      </article>
                    ))}
                  </div>
                  <div className="action-panel supplier-panel">
                    <div>
                      <span className="status-chip blue">Supplier portal</span>
                      <h3>{supplierLink ? `Link active · ${supplierLink.token.slice(0, 8)}...` : 'Create supplier link'}</h3>
                      <p>Supplier can confirm readiness and upload packing files without seeing pricing.</p>
                    </div>
                    <div className="action-panel-buttons">
                      <button className="secondary-action small" type="button" onClick={handleSupplierLink} disabled={loading}>
                        <ArrowRight size={15} />
                        Create link
                      </button>
                      <button className="secondary-action small" type="button" onClick={handleSupplierUpload} disabled={loading || !supplierLink}>
                        <FileText size={15} />
                        Supplier upload
                      </button>
                    </div>
                    {supplierPortal && <small>{supplierPortal.supplier_instructions}</small>}
                  </div>
                </>
              ) : (
                <div className="empty-state">
                  <FileText size={42} />
                  <p>Select a shipment from the Exceptions tab first.</p>
                </div>
              )}
            </section>
          )}

          {adminView === 'tracking' && (
            <section className="panel admin-panel full">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Tracking control</p>
                  <h2>{activeBooking ? `${activeBooking.id} timeline` : 'No shipment selected.'}</h2>
                </div>
                <button className="secondary-action" type="button" onClick={handleAddEvent} disabled={loading || !activeBooking}>
                  <Truck size={17} />
                  Mark goods received
                </button>
              </div>
              {activeBooking ? (
                <>
                  <div className="admin-function-summary">
                    <DetailTile icon={<CalendarClock size={18} />} label="Warehouse cutoff" value={formatDateShort(activeBooking.warehouse_receipt_cutoff)} />
                    <DetailTile icon={<Ship size={18} />} label="Sailing" value={formatDateShort(activeContainer?.target_sailing_date)} />
                    <DetailTile icon={<MapPin size={18} />} label="Arrival" value={formatDateShort(activeContainer?.estimated_arrival)} />
                  </div>
                  <ol className="timeline event-timeline">
                    {events.map((event) => (
                      <li key={event.id} className={event.occurred_at ? 'done' : ''}>
                        <span>{event.occurred_at ? <Check size={15} /> : null}</span>
                        <p>{event.label}</p>
                        <small>{event.occurred_at?.slice(0, 10) ?? event.estimated_at?.slice(0, 10) ?? sourceLabel(event.confidence)}</small>
                      </li>
                    ))}
                  </ol>
                </>
              ) : (
                <div className="empty-state">
                  <Truck size={42} />
                  <p>Select a shipment from the Exceptions tab first.</p>
                </div>
              )}
            </section>
          )}

          {adminView === 'payments' && (
            <section className="panel admin-panel full">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Finance control</p>
                  <h2>{activeBooking ? `${activeBooking.id} invoice and release` : 'No shipment selected.'}</h2>
                </div>
                <Receipt size={24} />
              </div>
              {activeBooking ? (
                <div className="money-layout">
                  <div className="admin-function-summary">
                    <DetailTile icon={<CircleDollarSign size={18} />} label="Invoice total" value={formatMoney(invoice?.total_usd)} />
                    <DetailTile icon={<ShieldCheck size={18} />} label="Release status" value={releaseStatus ? sourceLabel(releaseStatus.release_status) : 'Loading'} />
                    <DetailTile icon={<Gauge size={18} />} label="Active holds" value={`${activeReleaseHolds.length}`} />
                  </div>
                  <InvoiceSheet invoice={invoice} booking={activeBooking} actionLabel="Mark paid" loading={loading} onPay={handleMarkPaid} />
                  <div className="action-panel release-panel">
                    <div>
                      <span className={`status-chip ${releaseStatus?.can_release ? 'green' : 'orange'}`}>
                        {releaseStatus?.can_release ? 'Ready to release' : 'Release blocked'}
                      </span>
                      <h3>{activeReleaseHolds.length ? `${activeReleaseHolds.length} hold${activeReleaseHolds.length === 1 ? '' : 's'} to clear` : 'No active holds'}</h3>
                      <p>Release unlocks automatically when payment, documents, customs, and team review are clear.</p>
                    </div>
                    <div className="hold-grid">
                      {(releaseStatus?.holds ?? []).length ? (
                        (releaseStatus?.holds ?? []).map((hold) => (
                          <span className={`hold-chip ${hold.status}`} key={hold.id}>
                            <small>{formatReleaseHold(hold.hold_type)}</small>
                            <b>{sourceLabel(hold.status)}</b>
                            <em>{hold.reason}</em>
                          </span>
                        ))
                      ) : (
                        <span className="hold-chip cleared">
                          <small>Release checks</small>
                          <b>Clear</b>
                          <em>No payment, document, customs, or review holds are active.</em>
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="empty-state">
                  <Receipt size={42} />
                  <p>Select a shipment from the Exceptions tab first.</p>
                </div>
              )}
            </section>
          )}

          {adminView === 'customs' && (
            <section className="panel admin-panel full">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Border clearance</p>
                  <h2>{activeBooking ? `${activeBooking.id} customs and border checks` : 'No shipment selected.'}</h2>
                </div>
                <button className="secondary-action" type="button" onClick={handleCustomsClear} disabled={loading || !activeBooking || customsProfile?.customs_status === 'cleared'}>
                  <ShieldCheck size={17} />
                  Mark cleared
                </button>
              </div>
              {activeBooking ? (
                <div className="customs-layout">
                  <div className="admin-function-summary">
                    <DetailTile icon={<CircleDollarSign size={18} />} label="Goods value" value={formatMoney(customsProfile?.goods_value_usd)} />
                    <DetailTile icon={<Receipt size={18} />} label="Import duty estimate" value={formatMoney(customsProfile?.duty_estimate_usd)} />
                    <DetailTile icon={<ShieldCheck size={18} />} label="GST estimate" value={formatMoney(customsProfile?.gst_estimate_usd)} />
                  </div>
                  <div className="customs-fact-grid">
                    <span>
                      <small>Buying term</small>
                      <b>{formatIncoterm(customsProfile?.incoterm)}</b>
                    </span>
                    <span>
                      <small>Product classification code</small>
                      <b>{customsProfile?.hs_code ?? 'Not confirmed yet'}</b>
                    </span>
                    <span>
                      <small>Who handles customs</small>
                      <b>{formatBrokerPreference(customsProfile?.broker_preference)}</b>
                    </span>
                    <span>
                      <small>Special border checks</small>
                      <b>{formatBiosecurityFlags(customsProfile?.biosecurity_flags)}</b>
                    </span>
                  </div>
                </div>
              ) : (
                <div className="empty-state">
                  <ShieldCheck size={42} />
                  <p>Select a shipment from the Exceptions tab first.</p>
                </div>
              )}
            </section>
          )}

          {adminView === 'automation' && (
            <div className="workspace admin-workspace">
              <section className="panel admin-panel full">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Automation engine</p>
                    <h2>Shipment lifecycle and partner chase.</h2>
                  </div>
                  <button
                    className="primary-action"
                    type="button"
                    disabled={loading}
                    onClick={async () => {
                      setLoading(true)
                      try {
                        const result = await runAllAutomation()
                        setAutomationResult(result)
                        const alerts = await getStaleChecks()
                        setStaleAlerts(alerts)
                      } catch {}
                      setLoading(false)
                    }}
                  >
                    <RefreshCw size={17} />
                    Run automation cycle
                  </button>
                </div>

                {automationResult && (
                  <div className="ops-grid">
                    <div className="ops-card">
                      <strong>Shipments processed</strong>
                      <span>{automationResult.shipments_processed}</span>
                    </div>
                    <div className="ops-card">
                      <strong>Chase messages queued</strong>
                      <span>{automationResult.total_chase_messages}</span>
                    </div>
                    <div className="ops-card">
                      <strong>Missing data items</strong>
                      <span>{automationResult.total_missing_items}</span>
                    </div>
                  </div>
                )}

                {automationResult && (
                  <div className="notification-list">
                    {Object.entries(automationResult.states).map(([bookingId, state]) => (
                      <div className="notification-item" key={bookingId}>
                        <strong>{bookingId}</strong>
                        <span>{state.replaceAll('_', ' ')}</span>
                      </div>
                    ))}
                  </div>
                )}
              </section>

              {staleAlerts.length > 0 && (
                <section className="panel admin-panel full">
                  <div className="panel-heading">
                    <div>
                      <p className="eyebrow">Stale data alerts</p>
                      <h2>{staleAlerts.length} shipment{staleAlerts.length === 1 ? '' : 's'} need attention.</h2>
                    </div>
                    <Scale size={24} />
                  </div>
                  <div className="notification-list">
                    {staleAlerts.map((alert, index) => (
                      <div className="notification-item" key={`${alert.booking_id}-${index}`}>
                        <strong>
                          {alert.booking_id} · {alert.severity}
                        </strong>
                        <span>{alert.message}</span>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              <section className="panel admin-panel full">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Per-shipment automation</p>
                    <h2>Run automation for a single shipment.</h2>
                  </div>
                  <ClipboardCheck size={24} />
                </div>
                <div className="ops-grid">
                  {bookings.slice(0, 6).map((booking) => (
                    <div className="ops-card" key={booking.id}>
                      <strong>{booking.id}</strong>
                      <span>{booking.cargo_description ?? booking.cargo_category}</span>
                      <span>{shipmentStates[booking.id]?.lifecycle_state?.replaceAll('_', ' ') ?? 'Not checked'}</span>
                      <button
                        className="secondary-action small"
                        type="button"
                        disabled={loading}
                        onClick={async () => {
                          setLoading(true)
                          try {
                            const stateResult = await getShipmentState(booking.id)
                            setShipmentStates((prev) => ({ ...prev, [booking.id]: stateResult }))
                          } catch {}
                          setLoading(false)
                        }}
                      >
                        Check state
                      </button>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          )}

          {adminView === 'audit' && (
            <div className="workspace admin-workspace">
              <section className="panel admin-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Notifications</p>
                    <h2>System notifications.</h2>
                  </div>
                  <Bell size={23} />
                </div>
                <div className="notification-list">
                  {(summary?.notifications ?? []).map((notification) => (
                    <NotificationCard notification={notification} key={notification.id} />
                  ))}
                </div>
              </section>

              <section className="panel admin-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Decision log</p>
                    <h2>Recent decisions.</h2>
                  </div>
                  <ClipboardCheck size={24} />
                </div>
                <div className="notification-list">
                  {(summary?.audit_events ?? []).map((event) => (
                    <div className="notification-item" key={event.id}>
                      <strong>
                        {event.event_type.replaceAll('_', ' ')} / {event.actor_role}
                      </strong>
                      <span>{event.message}</span>
                    </div>
                  ))}
                </div>
              </section>

              <section className="panel admin-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Audit search</p>
                    <h2>Filter the full audit log.</h2>
                  </div>
                  <ClipboardCheck size={24} />
                </div>
                <form
                  className="audit-filter-form"
                  onSubmit={async (event) => {
                    event.preventDefault()
                    setAuditLoading(true)
                    setAuditError(null)
                    try {
                      const cleaned: AuditEventFilters = {}
                      for (const [key, value] of Object.entries(auditFilterDraft)) {
                        if (value !== undefined && value !== null && value !== '') {
                          ;(cleaned as Record<string, unknown>)[key] = value
                        }
                      }
                      setAuditFilters(cleaned)
                      const events = await getAuditEvents(cleaned)
                      setAuditResults(events)
                    } catch (err) {
                      setAuditError(err instanceof Error ? err.message : 'Could not load audit events.')
                    } finally {
                      setAuditLoading(false)
                    }
                  }}
                  style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', alignItems: 'end' }}
                >
                  <label>
                    <span style={{ display: 'block', fontSize: 12, color: '#64748b' }}>Actor id</span>
                    <input
                      type="text"
                      value={auditFilterDraft.actor_id ?? ''}
                      placeholder="any"
                      onChange={(e) => setAuditFilterDraft((d) => ({ ...d, actor_id: e.target.value }))}
                    />
                  </label>
                  <label>
                    <span style={{ display: 'block', fontSize: 12, color: '#64748b' }}>Actor role</span>
                    <select
                      value={auditFilterDraft.actor_role ?? ''}
                      onChange={(e) =>
                        setAuditFilterDraft((d) => ({
                          ...d,
                          actor_role: (e.target.value || undefined) as AuditEventFilters['actor_role'],
                        }))
                      }
                    >
                      <option value="">any</option>
                      <option value="importer">importer</option>
                      <option value="admin">admin</option>
                      <option value="system">system</option>
                    </select>
                  </label>
                  <label>
                    <span style={{ display: 'block', fontSize: 12, color: '#64748b' }}>Event type</span>
                    <input
                      type="text"
                      value={auditFilterDraft.event_type ?? ''}
                      placeholder="e.g. approval_decided"
                      onChange={(e) => setAuditFilterDraft((d) => ({ ...d, event_type: e.target.value }))}
                    />
                  </label>
                  <label>
                    <span style={{ display: 'block', fontSize: 12, color: '#64748b' }}>Entity type</span>
                    <input
                      type="text"
                      value={auditFilterDraft.entity_type ?? ''}
                      placeholder="e.g. booking"
                      onChange={(e) => setAuditFilterDraft((d) => ({ ...d, entity_type: e.target.value }))}
                    />
                  </label>
                  <label>
                    <span style={{ display: 'block', fontSize: 12, color: '#64748b' }}>Entity id</span>
                    <input
                      type="text"
                      value={auditFilterDraft.entity_id ?? ''}
                      placeholder="e.g. BKG-0001"
                      onChange={(e) => setAuditFilterDraft((d) => ({ ...d, entity_id: e.target.value }))}
                    />
                  </label>
                  <label>
                    <span style={{ display: 'block', fontSize: 12, color: '#64748b' }}>Since</span>
                    <input
                      type="date"
                      value={auditFilterDraft.since ?? ''}
                      onChange={(e) => setAuditFilterDraft((d) => ({ ...d, since: e.target.value }))}
                    />
                  </label>
                  <label>
                    <span style={{ display: 'block', fontSize: 12, color: '#64748b' }}>Until</span>
                    <input
                      type="date"
                      value={auditFilterDraft.until ?? ''}
                      onChange={(e) => setAuditFilterDraft((d) => ({ ...d, until: e.target.value }))}
                    />
                  </label>
                  <label>
                    <span style={{ display: 'block', fontSize: 12, color: '#64748b' }}>Limit</span>
                    <input
                      type="number"
                      min={1}
                      max={1000}
                      value={auditFilterDraft.limit ?? ''}
                      placeholder="200"
                      onChange={(e) =>
                        setAuditFilterDraft((d) => ({
                          ...d,
                          limit: e.target.value ? Number(e.target.value) : undefined,
                        }))
                      }
                    />
                  </label>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button type="submit" className="primary" disabled={auditLoading}>
                      {auditLoading ? 'Filtering' : 'Filter'}
                    </button>
                    <button
                      type="button"
                      className="ghost"
                      onClick={() => {
                        setAuditFilterDraft({})
                        setAuditFilters({})
                        setAuditResults(null)
                        setAuditError(null)
                      }}
                    >
                      Reset
                    </button>
                  </div>
                </form>
                {auditError && <p style={{ color: '#dc2626', marginTop: 12 }}>{auditError}</p>}
                {auditResults !== null && (
                  <div style={{ marginTop: 16 }}>
                    <p style={{ fontSize: 13, color: '#64748b' }}>
                      {auditResults.length} event{auditResults.length === 1 ? '' : 's'}
                      {Object.keys(auditFilters).length > 0 ? ' match the filters.' : '.'}
                    </p>
                    {auditResults.length === 0 ? (
                      <p>No matching audit events.</p>
                    ) : (
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>When</th>
                            <th>Actor</th>
                            <th>Event</th>
                            <th>Entity</th>
                            <th>Message</th>
                          </tr>
                        </thead>
                        <tbody>
                          {auditResults.map((event) => (
                            <tr key={event.id}>
                              <td>{new Date(event.created_at).toLocaleString()}</td>
                              <td>
                                {event.actor_role} / {event.actor_id}
                              </td>
                              <td>{event.event_type}</td>
                              <td>
                                {event.entity_type} / {event.entity_id}
                              </td>
                              <td>{event.message}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                )}
              </section>
            </div>
          )}
        </main>
        </div>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <header className="topbar customer-topbar">
        <Logo />
        <div className="customer-header-controls">
          <div className="order-switcher" aria-label="Active order">
            <span>
              <ClipboardCheck size={17} />
              Orders
            </span>
            {orderSwitcherBookings.length ? (
              <select
                value={activeBooking?.id ?? ''}
                onChange={(event) => {
                  if (event.target.value) void openOpsBooking(event.target.value)
                }}
              >
                {orderSwitcherBookings.map((booking) => (
                  <option value={booking.id} key={booking.id}>
                    {booking.id} · {booking.supplier_city} to {booking.delivery_city}
                  </option>
                ))}
              </select>
            ) : (
              <button type="button" disabled>
                No orders yet
              </button>
            )}
          </div>
          <button
            className={`customer-account-button ${activeCustomerPhase.id === 'account' ? 'active' : ''}`}
            type="button"
            onClick={() => setView('profile')}
          >
            <UserRound size={18} />
            Account
          </button>
          <button
            className={`customer-help-button ${view === 'help' ? 'active' : ''}`}
            type="button"
            onClick={() => setView('help')}
          >
            <CircleHelp size={18} />
            Help
          </button>
          <button
            className={`customer-help-button ${view === 'inbox' ? 'active' : ''}`}
            type="button"
            onClick={() => setView('inbox')}
            aria-label="Inbox: forwarded supplier and partner messages"
          >
            <FileText size={18} />
            Inbox
          </button>
          <button
            className={`customer-help-button notifications-bell ${view === 'notifications' ? 'active' : ''}`}
            type="button"
            onClick={() => setView('notifications')}
            aria-label={`Notifications${unreadNotificationCount ? ` (${unreadNotificationCount} unread)` : ''}`}
          >
            <Bell size={18} />
            {unreadNotificationCount > 0 && (
              <span className="notifications-count">{unreadNotificationCount}</span>
            )}
          </button>
        </div>
        <div className="customer-nav-shell">
          <nav className="phase-nav" aria-label="Order fulfilment phases">
            {customerWorkflowPhases.map((phase) => (
              <button
                className={phase.id === activeCustomerPhase.id ? 'active' : ''}
                key={phase.id}
                onClick={() => setView(phase.defaultView)}
                aria-label={phase.number ? `${phase.number}. ${phase.label}: ${phase.summary}` : `${phase.label}: ${phase.summary}`}
                type="button"
              >
                {phase.number ? <span>{phase.number}</span> : <UserRound size={16} />}
                <strong>{phase.label}</strong>
              </button>
            ))}
          </nav>
          <nav className="phase-subnav" aria-label={`${activeCustomerPhase.label} tools`}>
            {activeCustomerPhase.views.map((item) => (
              <button
                className={view === item.view ? 'active' : ''}
                key={item.view}
                onClick={() => setView(item.view)}
                type="button"
              >
                {item.icon}
                {item.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main>
        <section className="intro-band tab-intro-band">
          <div>
            <p className="eyebrow">{activeViewIntro.eyebrow}</p>
            <h1>{activeViewIntro.title}</h1>
            <p className="tab-intro-copy">{activeViewIntro.summary}</p>
          </div>
        </section>

        {error && (
          <div className="notice error" role="alert">
            {error}
          </div>
        )}
        {releaseMessage && <div className="notice success">{releaseMessage}</div>}

        {activeBooking && activeShipmentState && view !== 'admin' && view !== 'profile' && view !== 'help' && view !== 'inbox' && (
          <section className="panel next-steps-banner">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Where this shipment is</p>
                <h2>{activeShipmentState.lifecycle_state.replaceAll('_', ' ')}</h2>
                <p className="next-action-line">
                  <strong>Next:</strong> {activeShipmentState.next_action}
                </p>
              </div>
              <Truck size={22} />
            </div>
            {activeMissingData.length > 0 && (
              <div className="missing-data-grid">
                <strong>Missing items ({activeMissingData.length}):</strong>
                <ul>
                  {activeMissingData.slice(0, 6).map((item) => (
                    <li key={item.field}>
                      <span className={`status-chip ${item.urgency === 'high' ? 'orange' : 'blue'}`}>
                        {item.urgency}
                      </span>
                      {item.label} <small>({item.responsible_party})</small>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>
        )}

        {allPendingApprovals.length > 0 && view !== 'admin' && (
          <section className="panel approvals-banner">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Action needed</p>
                <h2>
                  {allPendingApprovals.length} approval{allPendingApprovals.length === 1 ? '' : 's'} waiting on you
                </h2>
              </div>
              <Bell size={22} />
            </div>
            <ul className="approvals-list">
              {allPendingApprovals.slice(0, 5).map((approval) => (
                <li className="approval-item" key={approval.id}>
                  <div className="approval-summary">
                    <strong>{approval.title}</strong>
                    <span>{approval.plain_language_summary}</span>
                    {approval.amount_usd != null && (
                      <em>USD ${approval.amount_usd.toLocaleString()}</em>
                    )}
                    {approval.related_booking_id && (
                      <small>Shipment {approval.related_booking_id}</small>
                    )}
                  </div>
                  <div className="approval-actions">
                    <button
                      className="primary-action small"
                      type="button"
                      onClick={() => handleApprovalDecision(approval.id, 'approve')}
                    >
                      <Check size={14} />
                      Approve
                    </button>
                    <button
                      className="secondary-action small"
                      type="button"
                      onClick={() => handleApprovalDecision(approval.id, 'reject')}
                    >
                      Reject
                    </button>
                  </div>
                </li>
              ))}
            </ul>
            {allPendingApprovals.length > 5 && (
              <p className="approvals-overflow">
                +{allPendingApprovals.length - 5} more pending. Open each shipment to review.
              </p>
            )}
          </section>
        )}

        {view !== 'admin' ? (
          <>
          <PhaseOverview phase={activeCustomerPhase} activeView={view} items={customerPhaseItems} onOpen={setView} />

          <div className="workspace importer-workspace">
            {view === 'profile' && (
              <section className="panel profile-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Profile</p>
                    <h2>Saved booking details.</h2>
                  </div>
                  <UserRound size={24} />
                </div>

                <div className="clarity-hero profile-hero">
                  <div className="clarity-hero-main">
                    <span className="hero-icon">
                      <UserRound size={22} />
                    </span>
                    <div>
                      <span className="status-chip orange">Used on every new booking</span>
                      <h3>{profile.importer_company_name}</h3>
                      <p>
                        {profile.importer_contact_name} · {profile.importer_email}
                      </p>
                    </div>
                  </div>
                  <div className="hero-summary-grid">
                    <DetailTile icon={<MapPin size={18} />} label="Default delivery" value={`${profile.delivery_city}, ${profile.delivery_country}`} />
                    <DetailTile icon={<PackageCheck size={18} />} label="Default pickup mode" value={deliveryModeLabels[form.delivery_mode]} />
                    <DetailTile icon={<Truck size={18} />} label="Current supplier" value={supplierLocationInput || 'Not set'} />
                  </div>
                </div>

                <form className="profile-form" onSubmit={handleProfileSave}>
                  <div className="form-section">
                    <div className="form-section-heading">
                      <span>1</span>
                      <div>
                        <strong>Importer details</strong>
                        <small>Saved once so each sailing search starts faster.</small>
                      </div>
                    </div>
                    <div className="form-grid two">
                      <label>
                        <span>Company</span>
                        <input
                          value={profile.importer_company_name}
                          onChange={(event) => updateProfileField('importer_company_name', event.target.value)}
                        />
                      </label>
                      <label>
                        <span>Main contact</span>
                        <input
                          value={profile.importer_contact_name}
                          onChange={(event) => updateProfileField('importer_contact_name', event.target.value)}
                        />
                      </label>
                    </div>

                    <div className="form-grid two">
                      <label>
                        <span>Email</span>
                        <input
                          type="email"
                          value={profile.importer_email}
                          onChange={(event) => updateProfileField('importer_email', event.target.value)}
                        />
                      </label>
                      <label>
                        <span>Phone</span>
                        <input
                          value={profile.importer_phone}
                          onChange={(event) => updateProfileField('importer_phone', event.target.value)}
                        />
                      </label>
                    </div>
                  </div>

                  <div className="form-section">
                    <div className="form-section-heading">
                      <span>2</span>
                      <div>
                        <strong>Default delivery point</strong>
                        <small>This is copied into the Book tab and can still be changed per shipment.</small>
                      </div>
                    </div>
                    <div className="form-grid three">
                      <label>
                        <span>Default delivery city</span>
                        <input
                          value={profile.delivery_city}
                          onChange={(event) => updateProfileField('delivery_city', event.target.value)}
                        />
                      </label>
                      <label>
                        <span>Postcode</span>
                        <input
                          value={profile.delivery_postcode}
                          onChange={(event) => updateProfileField('delivery_postcode', event.target.value)}
                        />
                      </label>
                      <label>
                        <span>Country</span>
                        <input
                          value={profile.delivery_country}
                          onChange={(event) => updateProfileField('delivery_country', event.target.value)}
                        />
                      </label>
                    </div>
                  </div>

                  <button className="primary-action" type="submit">
                    <Check size={18} />
                    Save profile
                  </button>
                </form>
              </section>
            )}

            {view === 'integrations' && (
              <section className="panel tracking-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Account integrations</p>
                    <h2>Connect existing workflows only when useful.</h2>
                  </div>
                  <ArrowRight size={24} />
                </div>

                <div className="clarity-hero profile-hero">
                  <div className="clarity-hero-main">
                    <span className="hero-icon">
                      <ArrowRight size={22} />
                    </span>
                    <div>
                      <span className="status-chip orange">Optional</span>
                      <h3>Alibaba is an account integration, not an Order tab.</h3>
                      <p>Ship Hoppa should prompt for a marketplace connection only when it can save typing or verify an order.</p>
                    </div>
                  </div>
                  <div className="hero-summary-grid">
                    <DetailTile
                      icon={<Check size={18} />}
                      label="Connected"
                      value={`${accountIntegrations.filter((integration) => integration.status === 'connected').length}`}
                    />
                    <DetailTile
                      icon={<CircleHelp size={18} />}
                      label="Prompt only when useful"
                      value={`${accountIntegrations.filter((integration) => integration.status !== 'connected').length}`}
                    />
                    <DetailTile icon={<ShieldCheck size={18} />} label="Storage" value="Railway + R2" />
                  </div>
                </div>

                <div className="document-review-grid account-integration-grid">
                  {accountIntegrations.map((integration) => (
                    <div className="action-panel" key={integration.id}>
                      <span className={`status-chip ${integrationStatusClass(integration.status)}`}>
                        {sourceLabel(integration.status)}
                      </span>
                      <h3>{integration.display_name}</h3>
                      <p>{integration.notes ?? integration.category}</p>
                      <div className="integration-prompt-list">
                        {integration.prompt_when.slice(0, 2).map((prompt) => (
                          <span key={prompt}>{prompt}</span>
                        ))}
                      </div>
                      <button
                        className="secondary-action small"
                        type="button"
                        onClick={() => handleIntegrationStatus(integration.provider, integration.status !== 'connected')}
                        disabled={loading || integration.connection_mode === 'system_managed'}
                      >
                        {integrationIcon(integration.provider)}
                        {integration.status === 'connected' ? 'Disconnect' : 'Mark connected'}
                      </button>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {view === 'inbox' && (
              <section className="panel tracking-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Inbox</p>
                    <h2>Forwarded supplier and partner messages.</h2>
                  </div>
                  <Bell size={24} />
                </div>
                <p className="tab-intro-copy">
                  Forward emails from suppliers, forwarders, brokers, or warehouses to your Ship Hoppa
                  inbox. Ship Hoppa parses each message, extracts shipment facts, and attaches them to
                  the right order automatically.
                </p>

                {inboxMessages.length === 0 ? (
                  <div className="empty-state">
                    <Bell size={42} />
                    <p>No forwarded messages yet. Once you forward your first supplier email, it will appear here.</p>
                  </div>
                ) : (
                  <ul className="inbox-list">
                    {inboxMessages.map((message) => (
                      <li className="inbox-item" key={message.id}>
                        <div className="inbox-row">
                          <div className="inbox-meta">
                            <strong>{message.subject || '(no subject)'}</strong>
                            <span>From: {message.from_address}</span>
                            <small>{formatDateFriendly(message.received_at)}</small>
                          </div>
                          <span className={`status-chip ${message.extraction_status === 'matched' ? 'green' : message.extraction_status === 'needs_review' ? 'orange' : 'gray'}`}>
                            {sourceLabel(message.extraction_status)}
                          </span>
                        </div>
                        {message.body && (
                          <p className="inbox-body">{message.body.length > 240 ? `${message.body.slice(0, 240)}…` : message.body}</p>
                        )}
                        {message.attachments && message.attachments.length > 0 && (
                          <div className="inbox-attachments">
                            {message.attachments.map((name: string) => (
                              <span className="inbox-attachment" key={name}>
                                <FileText size={13} />
                                {name}
                              </span>
                            ))}
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            )}

            {view === 'notifications' && (
              <section className="panel tracking-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Notifications</p>
                    <h2>{notifications.length ? `${notifications.length} recent` : 'No notifications yet'}</h2>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    {unreadNotificationCount > 0 && (
                      <button
                        className="secondary-action small"
                        type="button"
                        onClick={async () => {
                          try {
                            await markAllNotificationsRead()
                            const refreshed = await getNotifications()
                            setNotifications(refreshed)
                          } catch (err) {
                            setError(err instanceof Error ? err.message : 'Could not mark notifications read')
                          }
                        }}
                      >
                        Mark all read
                      </button>
                    )}
                    <Bell size={24} />
                  </div>
                </div>
                {notifications.length === 0 ? (
                  <div className="empty-state">
                    <Bell size={42} />
                    <p>No notifications yet. As shipments move through their lifecycle, updates will appear here.</p>
                  </div>
                ) : (
                  <ul className="notifications-list">
                    {notifications.slice(0, 50).map((notification) => (
                      <li className={`notification-item ${notification.read ? '' : 'unread'}`} key={notification.id}>
                        <div className="notification-row">
                          <div className="notification-meta">
                            <strong>{notification.message}</strong>
                            <small>
                              {sourceLabel(notification.trigger)} {' . '} {formatDateFriendly(notification.created_at)}
                            </small>
                          </div>
                          {!notification.read && <span className="status-chip orange">Unread</span>}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            )}

            {view === 'help' && (
              <section className="panel tracking-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Help</p>
                    <h2>What happens next, in plain English.</h2>
                  </div>
                  <CircleHelp size={24} />
                </div>

                <div className="clarity-hero profile-hero">
                  <div className="clarity-hero-main">
                    <span className="hero-icon">
                      <CircleHelp size={22} />
                    </span>
                    <div>
                      <span className="status-chip orange">Guided handoffs</span>
                      <h3>{activeBooking ? activeBooking.id : 'Start with your supplier order'}</h3>
                      <p>Ship Hoppa should show only the next useful action for the importer, supplier, courier, broker, or Ship Hoppa team.</p>
                    </div>
                  </div>
                  <div className="hero-summary-grid">
                    <DetailTile icon={<ClipboardCheck size={18} />} label="Current phase" value={activeCustomerPhase.label} />
                    <DetailTile icon={<Gauge size={18} />} label="Open blockers" value={`${activeReleaseHolds.length}`} />
                    <DetailTile icon={<Bell size={18} />} label="Next action" value={projectWorkspace?.project.next_action ?? 'Create an order'} />
                  </div>
                </div>

                <div className="supplier-workflow-grid">
                  <section className="form-section document-step">
                    <div className="form-section-heading">
                      <span>1</span>
                      <div>
                        <strong>Ship Hoppa automates</strong>
                        <small>These tasks should happen in the background unless a decision or missing detail blocks them.</small>
                      </div>
                    </div>
                    <div className="document-review-grid">
                      <DetailTile icon={<FileText size={18} />} label="Emails and files" value="Extract and match" />
                      <DetailTile icon={<Ship size={18} />} label="Shipping options" value="Cutoff checked" />
                      <DetailTile icon={<ShieldCheck size={18} />} label="Release checks" value="Always running" />
                    </div>
                  </section>

                  <section className="form-section document-step">
                    <div className="form-section-heading">
                      <span>2</span>
                      <div>
                        <strong>Partners update Ship Hoppa</strong>
                        <small>Supplier, courier, broker, and trucker links keep data flowing without the importer chasing every email.</small>
                      </div>
                    </div>
                    <div className="document-review-grid">
                      <DetailTile icon={<UserRound size={18} />} label="Supplier" value="Production and packing" />
                      <DetailTile icon={<Truck size={18} />} label="Courier / trucker" value="Invoices and POD" />
                      <DetailTile icon={<ShieldCheck size={18} />} label="Broker" value="Customs status" />
                    </div>
                  </section>

                  <section className="form-section document-step">
                    <div className="form-section-heading">
                      <span>3</span>
                      <div>
                        <strong>You decide only when needed</strong>
                        <small>Approvals stay clear: supplier payment, inspection failures, sailing changes, customs questions, and delivery release.</small>
                      </div>
                    </div>
                    <div className="action-panel-buttons">
                      <button className="secondary-action small" type="button" onClick={() => setView('supplier')}>
                        <UserRound size={15} />
                        Start with supplier
                      </button>
                      <button className="secondary-action small" type="button" onClick={() => setView('tracking')}>
                        <Truck size={15} />
                        Track order
                      </button>
                      <button className="secondary-action small" type="button" onClick={() => setView('delivery')}>
                        <MapPin size={15} />
                        Plan delivery
                      </button>
                    </div>
                  </section>
                </div>
              </section>
            )}

            {view === 'supplier' && (
              <section className="panel tracking-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Supplier</p>
                    <h2>Supplier, order source, and buyer handoff.</h2>
                  </div>
                  <UserRound size={24} />
                </div>

                <div className="clarity-hero production-hero">
                  <div className="clarity-hero-main">
                    <span className="hero-icon">
                      <UserRound size={22} />
                    </span>
                    <div>
                      <span className="status-chip orange">Order intake</span>
                      <h3>{activeBooking?.supplier_name ?? form.supplier_name ?? 'Add the supplier first'}</h3>
                      <p>{supplierLocationInput || 'Supplier city, country, contact, and order source should be captured once.'}</p>
                    </div>
                  </div>
                  <div className="hero-summary-grid">
                    <DetailTile icon={<MapPin size={18} />} label="Supplier city" value={form.supplier_city || activeBooking?.supplier_city || 'TBC'} />
                    <DetailTile icon={<PackageCheck size={18} />} label="Goods" value={activeBooking?.cargo_description ?? form.cargo_description ?? 'TBC'} />
                    <DetailTile icon={<ArrowRight size={18} />} label="Alibaba" value="Prompt if useful" />
                  </div>
                </div>

                <div className="supplier-workflow-grid">
                  <section className="form-section document-step">
                    <div className="form-section-heading">
                      <span>1</span>
                      <div>
                        <strong>Supplier details</strong>
                        <small>Saved into the order so shipping, pickup, production, and documents use the same source data.</small>
                      </div>
                    </div>
                    <div className="form-grid two">
                      <label>
                        <span>Supplier name</span>
                        <input
                          value={form.supplier_name ?? ''}
                          onChange={(event) => updateField('supplier_name', event.target.value)}
                        />
                      </label>
                      <label>
                        <span>Supplier city</span>
                        <input
                          list="supplier-city-options"
                          value={supplierLocationInput}
                          onChange={(event) => updateSupplierLocation(event.target.value)}
                        />
                      </label>
                    </div>
                    <button className="secondary-action small" type="button" onClick={() => setView('book')}>
                      <Ship size={15} />
                      Use these details for shipping
                    </button>
                  </section>

                  <section className="form-section document-step">
                    <div className="form-section-heading">
                      <span>2</span>
                      <div>
                        <strong>Forward supplier emails</strong>
                        <small>Email ingestion turns pro formas, order updates, and attachments into order data without changing the supplier workflow.</small>
                      </div>
                    </div>
                    <div className="document-review-grid">
                      <DetailTile icon={<FileText size={18} />} label="Messages matched" value={`${activeSourceMessages.length}`} />
                      <DetailTile
                        icon={<Check size={18} />}
                        label="Last extraction"
                        value={activeSourceMessages[0] ? sourceLabel(activeSourceMessages[0].extraction_status) : 'Waiting'}
                      />
                      <DetailTile
                        icon={<ShieldCheck size={18} />}
                        label="Confidence"
                        value={activeSourceMessages[0] ? sourceLabel(activeSourceMessages[0].confidence) : 'Estimated'}
                      />
                    </div>
                    <form className="source-message-form" onSubmit={handleSourceMessageIngest}>
                      <div className="form-grid two">
                        <label>
                          <span>Supplier email</span>
                          <input
                            type="email"
                            value={sourceMessageDraft.from_address}
                            onChange={(event) => updateSourceMessageDraft('from_address', event.target.value)}
                          />
                        </label>
                        <label>
                          <span>Email subject</span>
                          <input
                            value={sourceMessageDraft.subject}
                            onChange={(event) => updateSourceMessageDraft('subject', event.target.value)}
                          />
                        </label>
                      </div>
                      <label>
                        <span>Message contents</span>
                        <textarea
                          value={sourceMessageDraft.body}
                          onChange={(event) => updateSourceMessageDraft('body', event.target.value)}
                          rows={4}
                        />
                      </label>
                      <button className="primary-action" type="submit" disabled={loading || !activeBooking}>
                        {loading ? <Loader2 className="spin" size={16} /> : <FileText size={16} />}
                        Ingest supplier email
                      </button>
                    </form>
                  </section>

                  <section className="form-section document-step">
                    <div className="form-section-heading">
                      <span>3</span>
                      <div>
                        <strong>Supplier portal</strong>
                        <small>Suppliers get a free update link so they can confirm readiness and upload files without seeing pricing.</small>
                      </div>
                    </div>
                    <div className="document-review-grid">
                      <DetailTile icon={<UserRound size={18} />} label="Supplier access" value={supplierLink ? 'Link created' : 'Not invited'} />
                      <DetailTile icon={<CalendarClock size={18} />} label="Ready date" value={formatDateShort(activeBooking?.cargo_ready_date_latest)} />
                      <DetailTile icon={<FileText size={18} />} label="Supplier files" value={`${supplierPortal?.checklist.documents.length ?? 0}`} />
                    </div>
                    <div className="action-panel-buttons">
                      <button className="secondary-action small" type="button" onClick={handleSupplierLink} disabled={loading || !activeBooking}>
                        <ArrowRight size={15} />
                        Create supplier link
                      </button>
                      <button className="secondary-action small" type="button" onClick={handleSupplierUpload} disabled={loading || !supplierLink}>
                        <FileText size={15} />
                        Demo supplier upload
                      </button>
                      <button className="secondary-action small" type="button" onClick={() => setView('integrations')}>
                        <ArrowRight size={15} />
                        Account integrations
                      </button>
                    </div>
                  </section>
                </div>
              </section>
            )}

            {view === 'book' && (
              <>
            <section className="panel booking-panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Book a shared container</p>
                  <h2>Shipment details, dimensions, pickup.</h2>
                </div>
                <Ship size={24} />
              </div>

              <form onSubmit={handleSubmit}>
                <div className="profile-summary">
                  <div>
                    <small>Booking as</small>
                    <strong>{profile.importer_company_name}</strong>
                    <span>
                      {profile.importer_contact_name} · {profile.importer_email}
                    </span>
                  </div>
                  <div>
                    <small>Default delivery</small>
                    <strong>{profile.delivery_city}</strong>
                    <span>
                      {profile.delivery_postcode}, {profile.delivery_country}
                    </span>
                  </div>
                  <button className="secondary-action small" type="button" onClick={() => setView('profile')}>
                    <UserRound size={15} />
                    Edit profile
                  </button>
                </div>

                <div className="form-section">
                  <div className="form-section-heading">
                    <span>1</span>
                    <div>
                      <strong>Supplier</strong>
                      <small>Where the stock is coming from.</small>
                    </div>
                  </div>
                  <div className="form-grid two">
                    <label>
                      <span>Supplier name</span>
                      <input
                        value={form.supplier_name ?? ''}
                        onChange={(event) => updateField('supplier_name', event.target.value)}
                      />
                    </label>
                    <label>
                      <span>Supplier city</span>
                      <input
                        list="supplier-city-options"
                        autoComplete="address-level2"
                        placeholder="Start typing city, province, country"
                        value={supplierLocationInput}
                        onChange={(event) => updateSupplierLocation(event.target.value)}
                      />
                      <datalist id="supplier-city-options">
                        {supplierLocations.map((location) => (
                          <option key={`${location.city}-${location.country}`} value={locationLabel(location)} />
                        ))}
                      </datalist>
                    </label>
                  </div>
                </div>

                <div className="form-section">
                  <div className="form-section-heading">
                    <span>2</span>
                    <div>
                      <strong>Cargo</strong>
                      <small>The product itself, not how it is packed.</small>
                    </div>
                  </div>
                  <div className="form-grid two">
                    <label>
                      <span>Goods category</span>
                      <select
                        value={form.cargo_category}
                        onChange={(event) => updateCategory(event.target.value as CargoCategory)}
                      >
                        {cargoOptions.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      <span>Description</span>
                      <input
                        value={form.cargo_description}
                        onChange={(event) => updateField('cargo_description', event.target.value)}
                      />
                    </label>
                  </div>
                </div>

                <div className="form-section">
                  <div className="form-section-heading">
                    <span>3</span>
                    <div>
                      <strong>Packages and size</strong>
                      <small>How the goods are packed and measured.</small>
                    </div>
                  </div>
                  <div className="form-grid five">
                    <label>
                      <span>Packages</span>
                      <input
                        type="number"
                        min="1"
                        step="1"
                        value={form.number_of_packages ?? ''}
                        onChange={(event) =>
                          updatePackageField('number_of_packages', event.target.value ? Number(event.target.value) : undefined)
                        }
                      />
                    </label>
                    <label>
                      <span>Packaging</span>
                      <select
                        value={form.package_type ?? ''}
                        onChange={(event) => updateField('package_type', event.target.value)}
                      >
                        {packagingOptions.map((option) => (
                          <option key={option} value={option}>
                            {option}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      <span>Length cm</span>
                      <input
                        type="number"
                        min="1"
                        step="1"
                        value={form.package_length_cm ?? ''}
                        onChange={(event) =>
                          updatePackageField('package_length_cm', event.target.value ? Number(event.target.value) : undefined)
                        }
                      />
                    </label>
                    <label>
                      <span>Width cm</span>
                      <input
                        type="number"
                        min="1"
                        step="1"
                        value={form.package_width_cm ?? ''}
                        onChange={(event) =>
                          updatePackageField('package_width_cm', event.target.value ? Number(event.target.value) : undefined)
                        }
                      />
                    </label>
                    <label>
                      <span>Height cm</span>
                      <input
                        type="number"
                        min="1"
                        step="1"
                        value={form.package_height_cm ?? ''}
                        onChange={(event) =>
                          updatePackageField('package_height_cm', event.target.value ? Number(event.target.value) : undefined)
                        }
                      />
                    </label>
                  </div>

                  <div className="form-grid two">
                    <label>
                      <span>Shipment volume (CBM)</span>
                      <input type="number" value={form.cbm_estimate} readOnly />
                      <small className="field-note">Calculated from package count and dimensions.</small>
                    </label>
                    <label>
                      <span>Total weight kg</span>
                      <input
                        type="number"
                        min="1"
                        step="1"
                        value={form.weight_kg_estimate}
                        onChange={(event) => updateField('weight_kg_estimate', Number(event.target.value))}
                      />
                    </label>
                  </div>
                </div>

                <div className="form-section">
                  <div className="form-section-heading">
                    <span>4</span>
                    <div>
                      <strong>Readiness</strong>
                      <small>When the supplier can release all goods.</small>
                    </div>
                  </div>
                  <div className="form-grid three">
                    <label>
                      <span>Earliest stock ready date</span>
                      <input
                        type="date"
                        value={form.cargo_ready_date_earliest}
                        onChange={(event) => updateField('cargo_ready_date_earliest', event.target.value)}
                      />
                      <small className="field-note">The first date pickup might be possible.</small>
                    </label>
                    <label>
                      <span>Latest stock ready date</span>
                      <input
                        type="date"
                        value={form.cargo_ready_date_latest}
                        onChange={(event) => updateField('cargo_ready_date_latest', event.target.value)}
                      />
                      <small className="field-note">The date all stock will definitely be ready.</small>
                    </label>
                    <label>
                      <span>Service</span>
                      <select
                        value={form.service_level}
                        onChange={(event) => updateField('service_level', event.target.value as 'standard' | 'express')}
                      >
                        <option value="standard">Standard</option>
                        <option value="express">Express</option>
                      </select>
                    </label>
                  </div>
                </div>

                <div className="form-section">
                  <div className="form-section-heading">
                    <span>5</span>
                    <div>
                      <strong>Pickup or warehouse delivery</strong>
                      <small>How the cargo gets to Ship Hoppa before cutoff.</small>
                    </div>
                  </div>

                  <div className="delivery-section">
                    <span className="field-label">Delivery mode</span>
                    <div className="segmented-control" role="group" aria-label="Delivery mode">
                      {(['ship_hoppa_pickup', 'self_delivery'] as DeliveryMode[]).map((mode) => (
                        <button
                          type="button"
                          key={mode}
                          className={form.delivery_mode === mode ? 'active' : ''}
                          onClick={() => updateField('delivery_mode', mode)}
                        >
                          {mode === 'ship_hoppa_pickup' ? <Truck size={16} /> : <MapPin size={16} />}
                          {deliveryModeLabels[mode]}
                        </button>
                      ))}
                    </div>
                  </div>

                  {form.delivery_mode === 'ship_hoppa_pickup' && (
                    <>
                      <label>
                        <span>Pickup address</span>
                        <input
                          list="pickup-address-options"
                          autoComplete="street-address"
                          value={form.pickup_address ?? ''}
                          onChange={(event) => updateField('pickup_address', event.target.value)}
                        />
                        <datalist id="pickup-address-options">
                          {supplierLocations.map((location) => (
                            <option key={`${location.city}-pickup`} value={location.pickupAddress} />
                          ))}
                        </datalist>
                      </label>
                      <div className="form-grid two">
                        <label>
                          <span>Pickup contact</span>
                          <input
                            value={form.pickup_contact_name ?? ''}
                            onChange={(event) => updateField('pickup_contact_name', event.target.value)}
                          />
                        </label>
                        <label>
                          <span>Contact phone</span>
                          <input
                            value={form.pickup_contact_phone ?? ''}
                            onChange={(event) => updateField('pickup_contact_phone', event.target.value)}
                          />
                        </label>
                      </div>
                      <div className="form-grid two">
                        <label>
                          <span>Pickup window start</span>
                          <input
                            type="date"
                            value={form.pickup_window_start ?? ''}
                            onChange={(event) => updateField('pickup_window_start', event.target.value)}
                          />
                        </label>
                        <label>
                          <span>Pickup window end</span>
                          <input
                            type="date"
                            value={form.pickup_window_end ?? ''}
                            onChange={(event) => updateField('pickup_window_end', event.target.value)}
                          />
                        </label>
                      </div>
                    </>
                  )}
                </div>

                <button className="primary-action" type="submit" disabled={loading}>
                  {loading ? <Loader2 className="spin" size={18} /> : <ArrowRight size={18} />}
                  Find my container
                </button>
              </form>
            </section>

            <section className="panel result-panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">{match?.container ? 'Best result' : 'Match result'}</p>
                  <h2>{match?.container ? `Container ${match.container.id}` : 'Ready when you are.'}</h2>
                </div>
                <Bell size={23} />
              </div>

              {match?.container ? (
                <>
                  <div className="match-card best-result-card">
                    <div className="best-option-header">
                      <div className="best-option-topline compact-option-top">
                        <div>
                          <span className="option-number">Option 1</span>
                          <strong>Best match</strong>
                        </div>
                        <b>Recommended</b>
                      </div>
                      <div className="best-option-mainline option-hero">
                        <CalendarClock size={20} />
                        <div>
                          <small>Leaves origin</small>
                          <strong>{formatDateFriendly(match.container.target_sailing_date)}</strong>
                        </div>
                        <div className={`feasibility-pill ${match.booking.feasibility_status ?? 'admin_review'}`}>
                          {statusLabels[match.booking.feasibility_status ?? 'admin_review']}
                        </div>
                      </div>
                    </div>
                    {match.booking.feasibility_reason && <p className="match-note">{match.booking.feasibility_reason}</p>}

                    <div className="price-row">
                      <div>
                        <small>Ship Hoppa price</small>
                        <strong>{formatMoney(match.booking.total_cost_usd)}</strong>
                      </div>
                      <ChevronRight size={20} />
                      <div>
                        <small>Typical LCL</small>
                        <strong>{formatMoney(match.lcl_estimate_usd)}</strong>
                      </div>
                    </div>
                    <div className="saving">
                      Saving {formatMoney(match.saving_usd)} ({match.saving_percent}%)
                    </div>

                    <RouteVisual origin={form.supplier_city} destination={profile.delivery_city} />

                    <div className="visual-detail-grid">
                      <DetailTile
                        icon={<CalendarClock size={18} />}
                        label="Sailing"
                        value={formatDateShort(match.container.target_sailing_date)}
                      />
                      <DetailTile
                        icon={<MapPin size={18} />}
                        label="Warehouse cutoff"
                        value={formatDateShort(match.booking.warehouse_receipt_cutoff ?? match.container.warehouse_receipt_cutoff_date)}
                      />
                      <DetailTile
                        icon={<Truck size={18} />}
                        label="Supplier ready"
                        value={formatDateShort(match.booking.latest_supplier_ready_date)}
                      />
                    </div>

                    <div className="cost-breakdown">
                      <div className="cost-breakdown-head">
                        <div>
                          <small>Price breakdown</small>
                          <strong>{formatMoney(match.booking.total_cost_usd)}</strong>
                        </div>
                        <span>{sourceLabel(match.container.sailing_source_confidence)}</span>
                      </div>
                      <div className="cost-line-grid">
                        <div className="cost-line">
                          <span className="cost-icon">
                            <ContainerIcon size={16} />
                          </span>
                          <div>
                            <small>Container share</small>
                            <b>{formatMoney(match.booking.cbm_cost_usd)}</b>
                          </div>
                          <em>Pro-rata</em>
                        </div>
                        <div className="cost-line">
                          <span className="cost-icon">
                            <Receipt size={16} />
                          </span>
                          <div>
                            <small>Ship Hoppa service fee</small>
                            <b>{formatMoney(serviceFeeTotal(match.booking))}</b>
                          </div>
                          <em>{serviceFeeCategory(match.booking.urgency_fee_usd)}</em>
                        </div>
                        <div className="cost-line">
                          <span className="cost-icon">
                            <Truck size={16} />
                          </span>
                          <div>
                            <small>Pickup</small>
                            <b>{formatMoney(match.booking.pickup_fee_usd)}</b>
                          </div>
                          <em>Supplier</em>
                        </div>
                      </div>
                      <div className="cost-source">
                        <span>Last checked</span>
                        <strong>{match.container.sailing_source_last_verified_at?.slice(0, 10) ?? 'TBC'}</strong>
                      </div>
                    </div>

                    <BookingCapacityLedger booking={match.booking} container={match.container} />
                    <BookingWeightLedger booking={match.booking} container={match.container} />

                    {isConfirmed ? (
                      <div className="instructions-box">
                        <strong>
                          <Check size={17} />
                          Booking confirmed
                        </strong>
                        <p>{supplierInstructions ?? 'Supplier delivery instructions are ready for this booking.'}</p>
                      </div>
                    ) : (
                      <button
                        className="primary-action confirm"
                        type="button"
                        onClick={handleConfirm}
                        disabled={loading || match.booking.admin_review_required}
                      >
                        <Check size={18} />
                        {match.booking.admin_review_required ? 'Awaiting team review' : 'Confirm booking'}
                      </button>
                    )}
                  </div>

                  {alternativeSailings.length > 0 && (
                    <div className="other-options">
                      <div className="other-options-heading">
                        <div>
                          <span>Compare alternatives</span>
                          <strong>Other sailing options</strong>
                        </div>
                        <p>Later sailings if you want more time before the warehouse deadline.</p>
                      </div>
                      <div className="compact-option-grid">
                        {alternativeSailings.map((sailing, index) => (
                          <article className="compact-option-card" key={sailing.sailing_option_id}>
                            <div className="option-ticket-header">
                              <div className="compact-option-top">
                                <div>
                                  <span className="option-number">Option {index + 2}</span>
                                  <strong>Alternative sailing</strong>
                                </div>
                                <span className={`confidence-badge ${sailing.source_confidence}`}>{sourceLabel(sailing.source_confidence)}</span>
                              </div>
                              <div className="option-hero">
                                <CalendarClock size={20} />
                                <div>
                                <small>Leaves origin</small>
                                  <strong>{formatDateFriendly(sailing.etd)}</strong>
                                </div>
                              </div>
                            </div>
                            <div className="option-ticket-body">
                              <RouteVisual origin="Origin port" destination={profile.delivery_city} />
                              <div className="option-fact-grid">
                                <span>
                                  <MapPin size={15} />
                                  <small>Warehouse deadline</small>
                                  <b>{formatDateFriendly(sailing.warehouse_receipt_cutoff_date)}</b>
                                </span>
                                <span>
                                  <Ship size={15} />
                                  <small>Arrives destination</small>
                                  <b>{formatDateFriendly(sailing.eta)}</b>
                                </span>
                                <span>
                                  <PackageCheck size={15} />
                                  <small>Space open</small>
                                  <b>{sailing.available_cbm} CBM</b>
                                </span>
                                <span>
                                  <Gauge size={15} />
                                  <small>Transit time</small>
                                  <b>{sailing.transit_days} days</b>
                                </span>
                              </div>
                              <div className="carrier-note">
                                <span>Shipping line</span>
                                <strong>
                                  {sailing.carrier_name} · {sailing.service_name}
                                </strong>
                              </div>
                              <button className="secondary-action small" type="button" onClick={() => checkAlternativeSailing(sailing)} disabled={loading}>
                                See if this sailing works
                              </button>
                            </div>
                          </article>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="empty-state">
                  <ContainerIcon size={42} />
                  <p>Submit the form to find your container.</p>
                </div>
              )}
            </section>
              </>
            )}

            {view === 'production' && (
              <section className="panel tracking-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Production</p>
                    <h2>Order, factory progress, and Supplier Pay.</h2>
                  </div>
                  <ClipboardCheck size={24} />
                </div>

                <div className="production-layout">
                  <div className="clarity-hero production-hero">
                    <div className="clarity-hero-main">
                      <span className="hero-icon">
                        <PackageCheck size={22} />
                      </span>
                      <div>
                        <span className={`status-chip ${activePurchaseOrder ? 'green' : 'orange'}`}>
                          {activePurchaseOrder ? sourceLabel(activePurchaseOrder.status) : 'No production plan yet'}
                        </span>
                        <h3>{activePurchaseOrder?.order_reference ?? activeBooking?.cargo_description ?? 'Create the order plan'}</h3>
                        <p>
                          {activePurchaseOrder
                            ? `${activePurchaseOrder.supplier_name} · ready target ${formatDateShort(activePurchaseOrder.cargo_ready_target_date)}`
                            : 'Turn the shipment into a production workflow before the goods are ready to ship.'}
                        </p>
                      </div>
                    </div>
                    <div className="hero-summary-grid">
                      <DetailTile icon={<ClipboardCheck size={18} />} label="Milestones" value={`${activeProductionMilestones.length}`} />
                      <DetailTile icon={<Receipt size={18} />} label="Supplier Pay" value={activeSupplierPayRequest ? sourceLabel(activeSupplierPayRequest.status) : 'Not started'} />
                      <DetailTile icon={<Bell size={18} />} label="Approvals" value={`${openApprovals.length}`} />
                    </div>
                  </div>

                  {!activeBooking ? (
                    <div className="empty-state">
                      <PackageCheck size={42} />
                      <p>Create or choose a booking before adding production control.</p>
                    </div>
                  ) : !activePurchaseOrder ? (
                    <div className="action-panel production-empty-panel">
                      <div>
                        <span className="status-chip orange">One-click setup</span>
                        <h3>Create production control for this shipment.</h3>
                        <p>
                          Ship Hoppa will create the purchase order, production milestones, QC step, Supplier Pay estimate,
                          and approval card from the booking.
                        </p>
                      </div>
                      <button className="primary-action" type="button" onClick={handleCreateProductionPlan} disabled={loading}>
                        {loading ? <Loader2 size={16} className="spin" /> : <ClipboardCheck size={16} />}
                        Create plan
                      </button>
                    </div>
                  ) : (
                    <>
                      <section className="form-section document-step production-card">
                        <div className="form-section-heading">
                          <span>1</span>
                          <div>
                            <strong>Order details</strong>
                            <small>The order record feeds production, payment, pickup readiness, and shipping timing.</small>
                          </div>
                        </div>
                        <div className="document-review-grid">
                          <DetailTile icon={<MapPin size={18} />} label="Supplier" value={activePurchaseOrder.supplier_name} />
                          <DetailTile icon={<CircleDollarSign size={18} />} label="Goods value" value={formatMoney(activePurchaseOrder.goods_value)} />
                          <DetailTile icon={<CalendarClock size={18} />} label="Ready target" value={formatDateShort(activePurchaseOrder.cargo_ready_target_date)} />
                        </div>
                      </section>

                      <section className="form-section document-step production-card">
                        <div className="form-section-heading">
                          <span>2</span>
                          <div>
                            <strong>Production milestones</strong>
                            <small>Earlier steps tick off automatically as payment, QC, and readiness updates come in.</small>
                          </div>
                        </div>
                        <div className="production-step-grid">
                          {activeProductionMilestones.map((milestone, index) => (
                            <article className={`production-step-card ${milestone.status}`} key={milestone.id}>
                              <span>{milestone.status === 'complete' ? <Check size={15} /> : index + 1}</span>
                              <div>
                                <small>{sourceLabel(milestone.owner)}</small>
                                <strong>{milestone.label}</strong>
                                <em>{formatDateShort(milestone.completed_at ?? milestone.due_date)}</em>
                              </div>
                              {milestone.status !== 'complete' && (
                                <button
                                  className="secondary-action small"
                                  type="button"
                                  onClick={() => handleCompleteMilestone(milestone.id, milestone.label)}
                                  disabled={loading}
                                >
                                  <Check size={14} />
                                  Mark done
                                </button>
                              )}
                            </article>
                          ))}
                        </div>
                      </section>

                      <section className="invoice-sheet supplier-pay-sheet">
                        <div className="invoice-sheet-head">
                          <div>
                            <small>Supplier Pay</small>
                            <strong>
                              {activeSupplierPayRequest ? `${activeSupplierPayRequest.currency} ${activeSupplierPayRequest.amount.toLocaleString()}` : 'No supplier payment'}
                            </strong>
                            <span>
                              {activeSupplierPayRequest
                                ? `${sourceLabel(activeSupplierPayRequest.payment_stage)} payment · ${sourceLabel(activeSupplierPayRequest.status)}`
                                : 'Supplier payment requests appear here when order payments are due.'}
                            </span>
                          </div>
                          <span className={`status-chip ${activeSupplierPayRequest?.status === 'marked_paid_outside_app' ? 'green' : 'orange'}`}>
                            {activeSupplierPayRequest ? sourceLabel(activeSupplierPayRequest.status) : 'Waiting'}
                          </span>
                        </div>
                        <div className="invoice-lines">
                          <div className="invoice-row invoice-row-header">
                            <span>Provider</span>
                            <span>Estimated total</span>
                          </div>
                          {activeSupplierPayQuotes.length ? (
                            activeSupplierPayQuotes.map((quote) => (
                              <div className="invoice-row" key={quote.id}>
                                <div className="invoice-line-label">
                                  <strong>
                                    {quote.provider.toUpperCase()}
                                    {quote.selected && <span className="invoice-service-tier"> · recommended</span>}
                                  </strong>
                                  <small>{quote.source_name}</small>
                                </div>
                                <b>{formatMoney(quote.estimated_total)}</b>
                              </div>
                            ))
                          ) : (
                            <div className="invoice-row muted">
                              <span>No quote has been created yet.</span>
                              <b>-</b>
                            </div>
                          )}
                        </div>
                        <div className="invoice-sheet-foot">
                          <p>Proof is optional when payment happens outside Ship Hoppa. The importer can simply mark it paid.</p>
                          {activeSupplierPayRequest && (
                            <button
                              className="primary-action"
                              type="button"
                              onClick={handleSupplierPayMarkPaid}
                              disabled={loading || activeSupplierPayRequest.status === 'marked_paid_outside_app'}
                            >
                              {loading ? <Loader2 size={16} className="spin" /> : <Check size={16} />}
                              Mark supplier paid
                            </button>
                          )}
                        </div>
                      </section>
                    </>
                  )}
                </div>
              </section>
            )}

            {view === 'inspection' && (
              <section className="panel tracking-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Inspection</p>
                    <h2>Quality check before the cargo is released.</h2>
                  </div>
                  <Scale size={24} />
                </div>
                <div className="clarity-hero production-hero">
                  <div className="clarity-hero-main">
                    <span className="hero-icon">
                      <Scale size={22} />
                    </span>
                    <div>
                      <span className={`status-chip ${activeQualityInspection ? 'green' : 'orange'}`}>
                        {activeQualityInspection ? sourceLabel(activeQualityInspection.result) : 'Not set yet'}
                      </span>
                      <h3>{activeQualityInspection?.inspection_required ? 'Inspection required' : 'Supplier photo check'}</h3>
                      <p>Inspection is part of Order because it proves the goods are acceptable before Ship Hoppa moves them.</p>
                    </div>
                  </div>
                  <div className="hero-summary-grid">
                    <DetailTile icon={<CalendarClock size={18} />} label="Inspection date" value={formatDateShort(activeQualityInspection?.inspection_date)} />
                    <DetailTile icon={<MapPin size={18} />} label="Location" value={activeQualityInspection?.inspection_location ?? form.supplier_city} />
                    <DetailTile icon={<Check size={18} />} label="Buyer approval" value={activeQualityInspection?.buyer_approval_required ? 'Required' : 'Not required'} />
                  </div>
                </div>
                <div className="supplier-workflow-grid">
                  <section className="form-section document-step">
                    <div className="form-section-heading">
                      <span>1</span>
                      <div>
                        <strong>Evidence check</strong>
                        <small>Supplier photos and product evidence prove the order is worth moving before freight money is spent.</small>
                      </div>
                    </div>
                    <div className="document-review-grid">
                      <DetailTile icon={<FileText size={18} />} label="Supplier photos" value={`${orderApprovedDocumentCount} approved`} />
                      <DetailTile icon={<PackageCheck size={18} />} label="Product proof" value={activePurchaseOrder?.product_summary ?? form.cargo_description ?? 'Waiting'} />
                      <DetailTile icon={<ShieldCheck size={18} />} label="Gate status" value={activeQualityInspection ? sourceLabel(activeQualityInspection.result) : 'Waiting'} />
                    </div>
                  </section>

                  <section className="form-section document-step">
                    <div className="form-section-heading">
                      <span>2</span>
                      <div>
                        <strong>Inspection decision</strong>
                        <small>Use supplier photos for simple orders and third-party QC when value, product risk, or buyer rules justify it.</small>
                      </div>
                    </div>
                    <div className="document-review-grid">
                      <DetailTile icon={<Scale size={18} />} label="Inspection required" value={activeQualityInspection?.inspection_required ? 'Yes' : 'Photo check'} />
                      <DetailTile icon={<CalendarClock size={18} />} label="Inspection date" value={formatDateShort(activeQualityInspection?.inspection_date)} />
                      <DetailTile icon={<MapPin size={18} />} label="Inspection location" value={activeQualityInspection?.inspection_location ?? form.supplier_city} />
                    </div>
                    {activeInspections.length > 0 && (
                      <div className="inspection-booking-grid">
                        {activeInspections.map((inspection) => (
                          <div key={inspection.id} className="inspection-row">
                            <div>
                              <span className={`status-chip ${inspection.result === 'passed' ? 'green' : inspection.result === 'failed' || inspection.result === 'rework_required' ? 'orange' : 'blue'}`}>
                                {sourceLabel(inspection.result)}
                              </span>
                              <strong>{inspection.inspection_provider ?? 'No inspector booked'}</strong>
                              <small>{inspection.inspection_date ?? 'No date'} . {inspection.inspection_location ?? 'No location'}</small>
                              {inspection.defects_summary && <em>{inspection.defects_summary}</em>}
                            </div>
                            {(!inspection.inspection_provider || inspection.result === 'pending') && (
                              <div className="inspection-book-form">
                                <input
                                  type="text"
                                  placeholder="Provider (e.g. SGS)"
                                  value={inspectionDraft.provider}
                                  onChange={(event) => setInspectionDraft({ ...inspectionDraft, provider: event.target.value })}
                                />
                                <input
                                  type="date"
                                  value={inspectionDraft.inspection_date}
                                  onChange={(event) => setInspectionDraft({ ...inspectionDraft, inspection_date: event.target.value })}
                                />
                                <input
                                  type="text"
                                  placeholder="Location"
                                  value={inspectionDraft.location}
                                  onChange={(event) => setInspectionDraft({ ...inspectionDraft, location: event.target.value })}
                                />
                                <button
                                  className="primary-action small"
                                  type="button"
                                  onClick={() => handleBookInspector(inspection.id)}
                                >
                                  <CalendarClock size={14} />
                                  Book inspector
                                </button>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                    <div className="action-panel-buttons">
                      {activeQcMilestone && activeQcMilestone.status !== 'complete' && (
                        <button
                          className="primary-action small"
                          type="button"
                          onClick={() => handleCompleteMilestone(activeQcMilestone.id, activeQcMilestone.label)}
                          disabled={loading}
                        >
                          <Check size={15} />
                          Mark inspection passed
                        </button>
                      )}
                      {!activePurchaseOrder && (
                        <button className="secondary-action small" type="button" onClick={handleCreateProductionPlan} disabled={loading || !activeBooking}>
                          <ClipboardCheck size={15} />
                          Create production plan
                        </button>
                      )}
                      <button className="secondary-action small" type="button" onClick={() => setView('order_docs')}>
                        <FileText size={15} />
                        Open proof files
                      </button>
                    </div>
                  </section>

                  <section className="form-section document-step">
                    <div className="form-section-heading">
                      <span>3</span>
                      <div>
                        <strong>Release gate</strong>
                        <small>Failed or missing inspection evidence keeps the order here until the buyer approves a fix or waiver.</small>
                      </div>
                    </div>
                    <div className="action-panel inspection-gate-panel">
                      <div>
                        <span className={`status-chip ${activeQualityInspection?.result === 'passed' ? 'green' : 'orange'}`}>
                          {activeQualityInspection?.result === 'passed' ? 'Ready for shipping' : 'Do not ship failed goods'}
                        </span>
                        <h3>{activeQualityInspection?.result === 'passed' ? 'Quality gate passed.' : 'Quality gate still protects the shipment.'}</h3>
                        <p>Once inspection passes, Ship Hoppa can keep moving the order into pickup, container matching, and sailing selection.</p>
                      </div>
                    </div>
                  </section>
                </div>
              </section>
            )}

            {view === 'supplier_pay' && (
              <section className="panel tracking-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Supplier Pay</p>
                    <h2>Supplier invoice and payment tracking.</h2>
                  </div>
                  <CircleDollarSign size={24} />
                </div>
                <div className="clarity-hero money-hero">
                  <div className="clarity-hero-main">
                    <span className="hero-icon">
                      <CircleDollarSign size={22} />
                    </span>
                    <div>
                      <span className={`status-chip ${activeSupplierPayRequest?.marked_paid_at ? 'green' : 'orange'}`}>
                        {activeSupplierPayRequest ? sourceLabel(activeSupplierPayRequest.status) : 'No supplier payment'}
                      </span>
                      <h3>
                        {activeSupplierPayRequest
                          ? `${activeSupplierPayRequest.currency} ${activeSupplierPayRequest.amount.toLocaleString()}`
                          : 'Capture supplier invoice first'}
                      </h3>
                      <p>Supplier invoice and payment stay in Order. Ship Hoppa freight invoices stay in Clear.</p>
                    </div>
                  </div>
                  <div className="hero-summary-grid">
                    <DetailTile icon={<Receipt size={18} />} label="Payment stage" value={activeSupplierPayRequest ? sourceLabel(activeSupplierPayRequest.payment_stage) : 'TBC'} />
                    <DetailTile icon={<CircleDollarSign size={18} />} label="Best quote" value={formatMoney(activeSupplierPayQuotes.find((quote) => quote.selected)?.estimated_total)} />
                    <DetailTile icon={<Check size={18} />} label="Outside app" value={activeSupplierPayRequest?.marked_paid_at ? 'Marked paid' : 'Available'} />
                  </div>
                </div>
                <section className="invoice-sheet supplier-pay-sheet">
                  <div className="invoice-sheet-head">
                    <div>
                      <small>Supplier invoice</small>
                      <strong>
                        {activeSupplierPayRequest
                          ? `${activeSupplierPayRequest.currency} ${activeSupplierPayRequest.amount.toLocaleString()}`
                          : 'Waiting for invoice'}
                      </strong>
                      <span>{activeSupplierPayRequest ? activeSupplierPayRequest.supplier_name : 'Supplier invoice capture will create the payment request.'}</span>
                    </div>
                    <span className={`status-chip ${activeSupplierPayRequest?.marked_paid_at ? 'green' : 'orange'}`}>
                      {activeSupplierPayRequest ? sourceLabel(activeSupplierPayRequest.status) : 'Waiting'}
                    </span>
                  </div>
                  <div className="invoice-lines">
                    <div className="invoice-row invoice-row-header">
                      <span>Payment option</span>
                      <span>Estimated total</span>
                    </div>
                    {activeSupplierPayQuotes.length ? (
                      activeSupplierPayQuotes.map((quote) => (
                        <div className="invoice-row" key={quote.id}>
                          <div className="invoice-line-label">
                            <strong>
                              {quote.provider.toUpperCase()}
                              {quote.selected && <span className="invoice-service-tier"> · recommended</span>}
                            </strong>
                            <small>{quote.source_name}</small>
                          </div>
                          <b>{formatMoney(quote.estimated_total)}</b>
                        </div>
                      ))
                    ) : (
                      <div className="invoice-row muted">
                        <span>No supplier payment quote yet.</span>
                        <b>-</b>
                      </div>
                    )}
                  </div>
                  <div className="invoice-sheet-foot">
                    <p>Proof is optional for outside-app payments. The user can mark it paid when they know it has been paid.</p>
                    <button className="primary-action small" type="button" onClick={handleSupplierPayMarkPaid} disabled={loading || !activeSupplierPayRequest}>
                      {loading ? <Loader2 size={16} className="spin" /> : <Check size={16} />}
                      Mark paid outside app
                    </button>
                  </div>
                </section>

                <section className="invoice-extractor">
                  <div className="panel-heading">
                    <div>
                      <p className="eyebrow">Read invoice</p>
                      <h2>Paste a supplier invoice and let Ship Hoppa do the rest.</h2>
                    </div>
                    <Receipt size={22} />
                  </div>
                  <p className="tab-intro-copy">
                    Forward or paste the supplier's invoice text. Ship Hoppa pulls out the invoice
                    number, amount, currency, due date, and bank details, matches it to the right
                    purchase order, and creates a payment request for you to approve.
                  </p>
                  <textarea
                    className="invoice-paste-area"
                    rows={8}
                    placeholder={`Example:\nINVOICE No: INV-2026-0042\nIssued: 2026-05-01\nDue Date: 2026-05-15\nPO Number: SH-2026-0044\nTotal: USD 4,250.00\nBeneficiary: Foshan Tiles Co Ltd\nBank: HSBC Hong Kong\nAccount No: 1234-5678-9012`}
                    value={invoiceText}
                    onChange={(event) => setInvoiceText(event.target.value)}
                  />
                  <div className="invoice-extractor-actions">
                    <button
                      className="secondary-action"
                      type="button"
                      onClick={handleInvoicePreview}
                      disabled={parsingInvoice || !invoiceText.trim()}
                    >
                      {parsingInvoice ? <Loader2 size={16} className="spin" /> : <FileText size={16} />}
                      Preview parse
                    </button>
                    <button
                      className="primary-action"
                      type="button"
                      onClick={handleInvoiceApply}
                      disabled={parsingInvoice || !invoiceText.trim()}
                    >
                      {parsingInvoice ? <Loader2 size={16} className="spin" /> : <Check size={16} />}
                      Apply to shipment
                    </button>
                    <label className="secondary-action invoice-pdf-upload">
                      <FileText size={16} />
                      <span>Upload PDF and apply</span>
                      <input
                        type="file"
                        accept="application/pdf,.pdf"
                        style={{ display: 'none' }}
                        onChange={(event) => {
                          const file = event.target.files?.[0]
                          if (file) {
                            void handleInvoicePdfUpload(file, true)
                          }
                          event.target.value = ''
                        }}
                      />
                    </label>
                  </div>
                  {parsedInvoice && (
                    <div className="parsed-invoice-card">
                      <strong>Parsed fields</strong>
                      <div className="parsed-invoice-grid">
                        <DetailTile icon={<FileText size={16} />} label="Invoice number" value={parsedInvoice.invoice_number ?? 'Not found'} />
                        <DetailTile icon={<Receipt size={16} />} label="Amount" value={parsedInvoice.total_amount != null && parsedInvoice.currency ? `${parsedInvoice.currency} ${parsedInvoice.total_amount.toLocaleString()}` : 'Not found'} />
                        <DetailTile icon={<CalendarClock size={16} />} label="Due date" value={parsedInvoice.due_date ?? 'Not found'} />
                        <DetailTile icon={<UserRound size={16} />} label="Beneficiary" value={parsedInvoice.beneficiary_name ?? 'Not found'} />
                        <DetailTile icon={<CircleDollarSign size={16} />} label="Bank" value={parsedInvoice.bank_name ?? 'Not found'} />
                        <DetailTile icon={<ShieldCheck size={16} />} label="SWIFT" value={parsedInvoice.swift_code ?? 'Not found'} />
                        <DetailTile icon={<ShieldCheck size={16} />} label="Account (last 4)" value={parsedInvoice.account_number_last4 ?? 'Not found'} />
                        <DetailTile icon={<ClipboardCheck size={16} />} label="PO reference" value={parsedInvoice.purchase_order_reference ?? 'Not found'} />
                      </div>
                      <small>Confidence: {parsedInvoice.confidence}</small>
                    </div>
                  )}
                </section>
              </section>
            )}

            {view === 'handoff' && (
              <section className="panel tracking-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Pickup</p>
                    <h2>Factory handoff to Ship Hoppa.</h2>
                  </div>
                  <Truck size={24} />
                </div>
                <div className="clarity-hero tracking-hero">
                  <div className="clarity-hero-main">
                    <span className="hero-icon">
                      <Truck size={22} />
                    </span>
                    <div>
                      <span className="status-chip orange">{deliveryModeLabels[activeBooking?.delivery_mode ?? form.delivery_mode]}</span>
                      <h3>{activeBooking?.pickup_address ?? form.pickup_address ?? 'Pickup address needed'}</h3>
                      <p>Pickup belongs in Ship because it controls warehouse receipt, cutoff feasibility, and container loading.</p>
                    </div>
                  </div>
                  <div className="hero-summary-grid">
                    <DetailTile icon={<CalendarClock size={18} />} label="Warehouse cutoff" value={formatDateShort(activeBooking?.warehouse_receipt_cutoff ?? selectedContainer?.warehouse_receipt_cutoff_date)} />
                    <DetailTile icon={<Truck size={18} />} label="Pickup window" value={`${formatDateShort(activeBooking?.pickup_window_start ?? form.pickup_window_start)} - ${formatDateShort(activeBooking?.pickup_window_end ?? form.pickup_window_end)}`} />
                    <DetailTile icon={<UserRound size={18} />} label="Contact" value={activeBooking?.pickup_contact_name ?? form.pickup_contact_name ?? 'TBC'} />
                  </div>
                </div>
                <div className="supplier-workflow-grid">
                  <section className="form-section document-step">
                    <div className="form-section-heading">
                      <span>1</span>
                      <div>
                        <strong>Pickup details</strong>
                        <small>Origin trucking uses the same supplier address, contact, cargo dimensions, and cutoff data from the booking.</small>
                      </div>
                    </div>
                    <div className="document-review-grid">
                      <DetailTile icon={<MapPin size={18} />} label="Pickup address" value={activeBooking?.pickup_address ?? form.pickup_address ?? 'Needed'} />
                      <DetailTile icon={<UserRound size={18} />} label="Pickup contact" value={activeBooking?.pickup_contact_name ?? form.pickup_contact_name ?? 'Needed'} />
                      <DetailTile icon={<PackageCheck size={18} />} label="Cargo size" value={`${formatQuantity(activeBooking?.cbm_estimate ?? form.cbm_estimate)} CBM`} />
                    </div>
                    <button className="secondary-action small" type="button" onClick={() => setView('book')}>
                      <PackageCheck size={15} />
                      Edit cargo and pickup
                    </button>
                  </section>

                  <section className="form-section document-step">
                    <div className="form-section-heading">
                      <span>2</span>
                      <div>
                        <strong>Cutoff protection</strong>
                        <small>Pickup should only proceed if it can reach Ship Hoppa before warehouse receipt cutoff.</small>
                      </div>
                    </div>
                    <div className="document-review-grid">
                      <DetailTile icon={<CalendarClock size={18} />} label="Warehouse cutoff" value={formatDateShort(activeBooking?.warehouse_receipt_cutoff ?? selectedContainer?.warehouse_receipt_cutoff_date)} />
                      <DetailTile icon={<Truck size={18} />} label="Latest supplier ready" value={formatDateShort(activeBooking?.latest_supplier_ready_date)} />
                      <DetailTile icon={<Gauge size={18} />} label="Feasibility" value={activeBooking?.feasibility_status ? statusLabels[activeBooking.feasibility_status] : 'Not checked'} />
                    </div>
                  </section>

                  <section className="form-section document-step">
                    <div className="form-section-heading">
                      <span>3</span>
                      <div>
                        <strong>Origin movement events</strong>
                        <small>Each click creates a tracking event so the importer can see the cargo moving toward the container.</small>
                      </div>
                    </div>
                    <div className="action-panel-buttons">
                      <button
                        className="secondary-action small"
                        type="button"
                        onClick={() => handleShipmentEvent('pickup_scheduled', 'Pickup scheduled', 'Pickup scheduled.')}
                        disabled={loading || !activeBooking}
                      >
                        <CalendarClock size={15} />
                        Schedule pickup
                      </button>
                      <button
                        className="secondary-action small"
                        type="button"
                        onClick={() => handleShipmentEvent('picked_up', 'Cargo picked up', 'Cargo marked picked up.')}
                        disabled={loading || !activeBooking}
                      >
                        <Truck size={15} />
                        Mark picked up
                      </button>
                      <button
                        className="secondary-action small"
                        type="button"
                        onClick={handleAddEvent}
                        disabled={loading || !activeBooking}
                      >
                        <Check size={15} />
                        Warehouse received
                      </button>
                    </div>
                  </section>

                  {activeBooking && activeBooking.delivery_mode !== 'ship_hoppa_pickup' && (
                    <section className="form-section document-step">
                      <div className="form-section-heading">
                        <span>4</span>
                        <div>
                          <strong>Bring your warehouse into the workspace</strong>
                          <small>
                            Send a self-serve link your warehouse can open without an account. They confirm receipt with actual
                            CBM, weight, and a photo, and the cargo timeline updates here.
                          </small>
                        </div>
                      </div>
                      <div className="broker-invite-block">
                        <button
                          className="primary-action small"
                          type="button"
                          onClick={handleInviteWarehouse}
                          disabled={loading || !activeBooking}
                        >
                          <UserRound size={16} />
                          Invite warehouse
                        </button>
                        {warehouseInviteMessage && <p className="muted">{warehouseInviteMessage}</p>}
                        {warehouseLink && (
                          <label className="broker-invite-url">
                            <span>Warehouse link</span>
                            <input
                              readOnly
                              value={`${globalThis.location?.origin ?? ''}/warehouse/${warehouseLink.token}`}
                              onFocus={(event) => event.target.select()}
                            />
                          </label>
                        )}
                      </div>
                    </section>
                  )}
                </div>
              </section>
            )}

            {view === 'sailings' && (
            <section className="panel sailing-panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Sailings</p>
                  <h2>Choose a container window.</h2>
                </div>
                <CalendarClock size={24} />
              </div>
              <div className="clarity-hero sailings-hero">
                <div className="clarity-hero-main">
                  <span className="hero-icon">
                    <CalendarClock size={22} />
                  </span>
	                  <div>
	                    <span className="status-chip blue">{selectedSailing ? 'Selected sailing' : 'Open sailings'}</span>
	                    <h3>{selectedSailing ? selectedSailing.carrier_name : 'Find a sailing window'}</h3>
	                    <p>{selectedSailing ? `${selectedSailing.service_name} · ${sourceLabel(selectedSailing.source_confidence)}` : 'Choose the route and date range before booking.'}</p>
	                  </div>
	                </div>
	                <div className="hero-summary-grid">
	                  <DetailTile icon={<MapPin size={18} />} label="Origin" value={sailingOrigin === 'all' ? sailingOriginPort(visibleSailing) : sailingOrigin} />
	                  <DetailTile icon={<Ship size={18} />} label="Destination" value={sailingDestination === 'all' ? sailingDestinationPort(visibleSailing) : sailingDestination} />
	                  <DetailTile icon={<CalendarClock size={18} />} label="Calendar window" value={`${formatDateShort(sailingWindowStart)} - ${formatDateShort(sailingWindowEnd)}`} />
	                </div>
	              </div>
	              <div className="sailing-search-panel">
	                <div className="sailing-filter-head">
	                  <span className="sailing-filter-icon">
	                    <CalendarClock size={18} />
	                  </span>
	                  <div>
	                    <strong>Search sailings</strong>
	                    <small>Pick an origin, destination, and sailing date window.</small>
	                  </div>
	                </div>
	                <div className="sailing-filter-grid">
	                  <label>
	                    <span className="field-label">Origin</span>
	                    <select value={sailingOrigin} onChange={(event) => setSailingOrigin(event.target.value)}>
	                      <option value="all">All origins</option>
	                      {sailingOriginOptions.map((origin) => (
	                        <option value={origin} key={origin}>
	                          {origin}
	                        </option>
	                      ))}
	                    </select>
	                  </label>
	                  <label>
	                    <span className="field-label">Destination</span>
	                    <select value={sailingDestination} onChange={(event) => setSailingDestination(event.target.value)}>
	                      <option value="all">All destinations</option>
	                      {sailingDestinationOptions.map((destination) => (
	                        <option value={destination} key={destination}>
	                          {destination}
	                        </option>
	                      ))}
	                    </select>
	                  </label>
	                  <label>
	                    <span className="field-label">From date</span>
	                    <input type="date" value={sailingWindowStart} onChange={(event) => setSailingWindowStart(event.target.value)} />
	                  </label>
	                  <label>
	                    <span className="field-label">To date</span>
	                    <input type="date" value={sailingWindowEnd} onChange={(event) => setSailingWindowEnd(event.target.value)} />
	                  </label>
	                </div>
	                <div className="sailing-filter-summary">
	                  <CalendarClock size={17} />
	                  <strong>{filteredSailings.length} sailing{filteredSailings.length === 1 ? '' : 's'} in this window</strong>
	                  <span>
	                    {sailingOrigin === 'all' ? 'All origins' : sailingOrigin} to {sailingDestination === 'all' ? 'all destinations' : sailingDestination}
	                  </span>
	                </div>
	              </div>
	              <div className="sailing-card-grid">
	                {filteredSailings.length ? (
	                  filteredSailings.slice(0, 6).map((sailing) => (
	                    <SailingCard
	                      key={sailing.sailing_option_id}
	                      sailing={sailing}
	                      selected={sailing.sailing_option_id === selectedSailing?.sailing_option_id}
	                      onSelect={() => bookSailing(sailing)}
	                    />
	                  ))
	                ) : (
	                  <div className="empty-state sailing-empty-state">
	                    <CalendarClock size={42} />
	                    <p>No sailings match this origin, destination, and calendar window.</p>
	                  </div>
	                )}
	              </div>
              {activeBooking?.container_id && (
                <div className="broker-invite-block">
                  <div>
                    <strong>Bring your carrier into the workspace</strong>
                    <p>
                      Send a self-serve link your carrier can open without an account. They confirm ETA, mark loaded /
                      departed / arrived, and upload the bill of lading. The existing ETA monitoring automation fires
                      when arrival shifts, so you do not need to chase by email.
                    </p>
                  </div>
                  <button
                    className="primary-action small"
                    type="button"
                    onClick={handleInviteCarrier}
                    disabled={loading || !activeBooking}
                  >
                    <Ship size={16} />
                    Invite carrier
                  </button>
                  {carrierInviteMessage && <p className="muted">{carrierInviteMessage}</p>}
                  {carrierLink && (
                    <label className="broker-invite-url">
                      <span>Carrier link</span>
                      <input
                        readOnly
                        value={`${globalThis.location?.origin ?? ''}/carrier/${carrierLink.token}`}
                        onFocus={(event) => event.target.select()}
                      />
                    </label>
                  )}
                </div>
              )}
            </section>
            )}

            {view === 'tracking' && (
            <section className="panel tracking-panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Track orders</p>
                  <h2>{activeBooking ? `${activeBooking.id} live journey` : 'Choose an order to track'}</h2>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <button
                    className="primary-action"
                    type="button"
                    onClick={() => setView('book')}
                    aria-label="Start a new shipment"
                  >
                    <PackageCheck size={16} />
                    New shipment
                  </button>
                  <Truck size={24} />
                </div>
              </div>

              {bookings.length ? (
                <div className="tracking-workspace">
                  <aside className="tracking-order-list" aria-label="Orders to track">
                    <div className="tracking-order-list-head">
                      <span className="status-chip blue">{bookings.length} orders</span>
                      <strong>Choose an order</strong>
                    </div>
                    {bookings.map((booking) => {
                      const orderContainer = containers.find((container) => container.id === booking.container_id) ?? null
                      const orderSailing = sailingForContainer(orderContainer, sailings)
                      const cardApprovalCount = allPendingApprovals.filter(
                        (approval) => approval.related_booking_id === booking.id,
                      ).length
                      return (
                        <TrackingOrderCard
                          key={booking.id}
                          booking={booking}
                          container={orderContainer}
                          sailing={orderSailing}
                          selected={booking.id === activeBooking?.id}
                          pendingApprovalCount={cardApprovalCount}
                          onOpen={openOpsBooking}
                        />
                      )
                    })}
                  </aside>

		                  {activeBooking && (
		                    <div className="tracking-detail-stack">
		                      <ShipmentJourneyMap booking={activeBooking} container={activeContainer} events={events} sailing={activeSailing} />
		                      <SpareSpacePanel
		                        opportunities={spaceOpportunities}
		                        onDetect={handleDetectSpareSpace}
		                        onList={handleListSpareSpace}
		                      />
		                    </div>
	                  )}
                  </div>
              ) : (
                <div className="empty-state">
                  <Truck size={42} />
                  <p>No orders to track yet. Submit a booking first, then this tab will show the journey and ETA.</p>
                </div>
              )}
            </section>
            )}

            {(view === 'order_docs' || view === 'ship_docs') && activeBooking && (
              <section className="panel tracking-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">{view === 'order_docs' ? 'Commercial proof' : 'Shipping documents'}</p>
                    <h2>{view === 'order_docs' ? 'Supplier and product files.' : 'Movement and release files.'}</h2>
                  </div>
                  <FileText size={24} />
                </div>

                <div className="clarity-hero documents-hero">
                  <div className="clarity-hero-main">
                    <span className="hero-icon">
                      <FileText size={22} />
                    </span>
                    <div>
                      <span className={`status-chip ${checklist?.checklist_status === 'complete' ? 'green' : 'orange'}`}>
                        {checklist ? sourceLabel(checklist.checklist_status) : 'Loading checklist'}
                      </span>
                      <h3>{activeBooking.id} {view === 'order_docs' ? 'order documents' : 'shipping documents'}</h3>
                      <p>
                        {view === 'order_docs'
                          ? 'Commercial proof stays with the supplier, invoice, production, and inspection workflow.'
                          : 'Packing, handoff, and shipping files move with the cargo and protect the sailing.'}
                      </p>
                    </div>
                  </div>
                  <div className="hero-summary-grid">
                    <DetailTile icon={<ClipboardCheck size={18} />} label="Required" value={`${activeDocumentRequiredCount}`} />
                    <DetailTile icon={<FileText size={18} />} label="Uploaded" value={`${activeDocumentUploadedCount}`} />
                    <DetailTile icon={<Check size={18} />} label="Approved" value={`${activeDocumentApprovedCount}`} />
                  </div>
                </div>

                <div className="document-step-sections">
                  <section className="form-section document-step">
                    <div className="form-section-heading">
                      <span>1</span>
                      <div>
                        <strong>{view === 'order_docs' ? 'Upload supplier and product files' : 'Upload shipping files'}</strong>
                        <small>
                          {view === 'order_docs'
                            ? 'These documents prove what was ordered and produced.'
                            : 'These documents let Ship Hoppa receive, load, and release the cargo.'}
                        </small>
                      </div>
                    </div>
                    <div className="document-grid">
                      {activeDocumentRequirements.map((requirement) => (
                        <article className={`document-card ${requirement.status}`} key={requirement.id}>
                          <span className="document-icon">
                            <FileText size={18} />
                          </span>
                          <div>
                            <strong>{requirement.label}</strong>
                            <small>{requirement.reason}</small>
                          </div>
                          <button
                            className={requirement.status === 'approved' ? 'secondary-action small selected' : 'secondary-action small'}
                            type="button"
                            onClick={() => handleDocumentUpload(requirement.document_type)}
                            disabled={loading || requirement.status === 'approved'}
                          >
                            {sourceLabel(requirement.status)}
                          </button>
                        </article>
                      ))}
                    </div>
                  </section>

                  <section className="form-section document-step">
                    <div className="form-section-heading">
                      <span>2</span>
                      <div>
                        <strong>Invite the supplier</strong>
                        <small>Let the supplier confirm readiness and upload packing files.</small>
                      </div>
                    </div>
                    <div className="action-panel supplier-panel document-supplier-panel">
                      <div>
                        <span className="status-chip blue">Supplier portal</span>
                        <h3>{supplierLink ? `Link active · ${supplierLink.token.slice(0, 8)}...` : 'Create supplier link'}</h3>
                        <p>Supplier can confirm readiness, see pickup instructions, and upload packing files without seeing pricing.</p>
                      </div>
                      <div className="action-panel-buttons">
                        <button className="secondary-action small" type="button" onClick={handleSupplierLink} disabled={loading}>
                          <ArrowRight size={15} />
                          Create link
                        </button>
                        <button className="secondary-action small" type="button" onClick={handleSupplierUpload} disabled={loading || !supplierLink}>
                          <FileText size={15} />
                          Supplier upload
                        </button>
                      </div>
                      {supplierPortal && <small>{supplierPortal.supplier_instructions}</small>}
                    </div>
                  </section>

                  <section className="form-section document-step">
                    <div className="form-section-heading">
                      <span>3</span>
                      <div>
                        <strong>Ship Hoppa checks and approves</strong>
                        <small>{activeDocumentMissingCount ? `${activeDocumentMissingCount} still missing.` : 'This document group is ready.'}</small>
                      </div>
                    </div>
                    <div className="document-review-grid">
                      <DetailTile icon={<ClipboardCheck size={18} />} label="Still missing" value={`${activeDocumentMissingCount}`} />
                      <DetailTile icon={<FileText size={18} />} label="Uploaded" value={`${activeDocumentUploadedCount}`} />
                      <DetailTile icon={<Check size={18} />} label="Approved" value={`${activeDocumentApprovedCount}`} />
                    </div>
                  </section>
                </div>
              </section>
            )}

            {view === 'money' && activeBooking && (
              <section className="panel tracking-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Payments</p>
                    <h2>Invoice, payment, and release.</h2>
                  </div>
                  <Receipt size={24} />
                </div>
                <div className="money-layout">
                  <div className="clarity-hero money-hero">
                    <div className="clarity-hero-main">
                      <span className="hero-icon">
                        <Receipt size={22} />
                      </span>
                      <div>
                        <span className={`status-chip ${invoice?.status === 'paid' ? 'green' : 'orange'}`}>
                          {invoice ? sourceLabel(invoice.status) : 'Invoice loading'}
                        </span>
                        <h3>{formatMoney(invoice?.total_usd)}</h3>
                        <p>Invoice for {activeBooking.id} · due {formatDateShort(invoice?.due_date)}</p>
                      </div>
                    </div>
                    <div className="hero-summary-grid">
                      <DetailTile icon={<CircleDollarSign size={18} />} label="Invoice total" value={formatMoney(invoice?.total_usd)} />
                      <DetailTile icon={<ShieldCheck size={18} />} label="Release status" value={releaseStatus ? sourceLabel(releaseStatus.release_status) : 'Loading'} />
                      <DetailTile icon={<Gauge size={18} />} label="Active holds" value={`${activeReleaseHolds.length}`} />
                    </div>
                  </div>

                  <InvoiceSheet invoice={invoice} booking={activeBooking} actionLabel="Pay invoice" loading={loading} onPay={handleMarkPaid} />

                  {landedCost && landedCost.lines.length > 0 && (
                    <section className="action-panel landed-cost-panel">
                      <div>
                        <span className="status-chip blue">Landed cost</span>
                        <h3>{formatMoney(landedCost.total_landed_cost_usd)} estimated total</h3>
                        <p>
                          Paid so far: {formatMoney(landedCost.paid_to_date_usd)} · Remaining estimate:{' '}
                          {formatMoney(landedCost.remaining_estimate_usd)}
                        </p>
                      </div>
                      <table className="landed-cost-table">
                        <thead>
                          <tr>
                            <th>Cost line</th>
                            <th>Status</th>
                            <th style={{ textAlign: 'right' }}>Amount (USD)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {landedCost.lines.map((line) => (
                            <tr key={line.category}>
                              <td>{line.label}</td>
                              <td>
                                <span className={`status-chip ${line.status === 'actual' ? 'green' : 'orange'}`}>
                                  {line.status === 'actual' ? 'Actual' : 'Estimate'}
                                </span>
                              </td>
                              <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                                {formatMoney(line.amount_usd)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                        <tfoot>
                          <tr>
                            <td colSpan={2}><strong>Total landed cost</strong></td>
                            <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                              <strong>{formatMoney(landedCost.total_landed_cost_usd)}</strong>
                            </td>
                          </tr>
                        </tfoot>
                      </table>
                    </section>
                  )}

                  <div className="action-panel release-panel">
                    <div>
                      <span className={`status-chip ${releaseStatus?.can_release ? 'green' : 'orange'}`}>
                        {releaseStatus?.can_release ? 'Ready to release' : 'Release blocked'}
                      </span>
                      <h3>{activeReleaseHolds.length ? `${activeReleaseHolds.length} hold${activeReleaseHolds.length === 1 ? '' : 's'} to clear` : 'No active holds'}</h3>
                      <p>Freight can be released once payment, documents, and customs checks are clear.</p>
                    </div>
                    <div className="hold-grid">
                      {(releaseStatus?.holds ?? []).length ? (
                        (releaseStatus?.holds ?? []).map((hold) => (
                          <span className={`hold-chip ${hold.status}`} key={hold.id}>
                            <small>{formatReleaseHold(hold.hold_type)}</small>
                            <b>{sourceLabel(hold.status)}</b>
                            <em>{hold.reason}</em>
                          </span>
                        ))
                      ) : (
                        <span className="hold-chip cleared">
                          <small>Release checks</small>
                          <b>Clear</b>
                          <em>No payment, document, customs, or review holds are active.</em>
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </section>
            )}

            {view === 'customs' && activeBooking && (
              <section className="panel tracking-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Customs</p>
                    <h2>Border costs and clearance, in plain English.</h2>
                  </div>
                  <ShieldCheck size={24} />
                </div>
                <div className="customs-layout">
                  <div className="clarity-hero customs-hero">
                    <div className="clarity-hero-main">
                      <span className="hero-icon">
                        <ShieldCheck size={22} />
                      </span>
                      <div>
                        <span className={`status-chip ${customsProfile?.customs_status === 'cleared' ? 'green' : 'orange'}`}>
                          {formatCustomsStatus(customsProfile?.customs_status)}
                        </span>
                        <h3>{formatMoney(customsProfile?.landed_cost_estimate_usd)} estimated at the border</h3>
                        <p>{customsStatusDescription(customsProfile?.customs_status)}</p>
                      </div>
                    </div>
                  </div>

                  <div className="customs-step-grid">
                    <article className="customs-step-card">
                      <div className="customs-step-head">
                        <span>1</span>
                        <div>
                          <small>What the shipment is</small>
                          <strong>Goods details</strong>
                        </div>
                      </div>
                      <p>The broker uses these details to classify the goods and prepare the entry.</p>
                      <div className="customs-simple-list">
                        <span>
                          <small>Declared goods value</small>
                          <b>{formatMoney(customsProfile?.goods_value_usd)}</b>
                        </span>
                        <span>
                          <small>Product classification code</small>
                          <b>{customsProfile?.hs_code ?? 'Not confirmed yet'}</b>
                        </span>
                        <span>
                          <small>Buying term</small>
                          <b>{formatIncoterm(customsProfile?.incoterm)}</b>
                        </span>
                      </div>
                      {hsSuggestions && hsSuggestions.suggestions.length > 0 && !customsProfile?.hs_code && (
                        <div className="hs-suggestion-block">
                          <small>Suggested classification (review before lodging):</small>
                          <div className="hs-suggestion-grid">
                            {hsSuggestions.suggestions.slice(0, 3).map((s) => (
                              <div className="hs-suggestion-card" key={s.hs_code}>
                                <strong>{s.hs_code}</strong>
                                <span className={`status-chip ${s.confidence === 'verified' ? 'green' : 'orange'}`}>{s.confidence}</span>
                                <p>{s.description}</p>
                                <small>{s.rationale}</small>
                              </div>
                            ))}
                          </div>
                          <button className="primary-action small" type="button" onClick={handleAcceptHsSuggestion}>
                            <Check size={14} />
                            Use {hsSuggestions.suggestions[0].hs_code}
                          </button>
                        </div>
                      )}
                    </article>

                    <article className="customs-step-card highlighted">
                      <div className="customs-step-head">
                        <span>2</span>
                        <div>
                          <small>What may be payable</small>
                          <strong>Estimated border charges</strong>
                        </div>
                      </div>
                      <p>These are estimates only. The final amount is confirmed after the broker lodges the customs entry.</p>
                      <div className="customs-money-grid">
                        <DetailTile icon={<Receipt size={18} />} label="Import duty estimate" value={formatMoney(customsProfile?.duty_estimate_usd)} />
                        <DetailTile icon={<ShieldCheck size={18} />} label="GST estimate" value={formatMoney(customsProfile?.gst_estimate_usd)} />
                        <DetailTile icon={<CircleDollarSign size={18} />} label="Broker estimate" value={formatMoney(customsProfile?.brokerage_fee_usd)} />
                      </div>
                    </article>

                    <article className="customs-step-card">
                      <div className="customs-step-head">
                        <span>3</span>
                        <div>
                          <small>What happens before release</small>
                          <strong>Clearance checks</strong>
                        </div>
                      </div>
                      <p>Freight can only be released after customs, payment, and document checks are clear.</p>
                      <div className="customs-simple-list">
                        <span>
                          <small>Who handles customs</small>
                          <b>{formatBrokerPreference(customsProfile?.broker_preference)}</b>
                        </span>
                        <span>
                          <small>Special border checks</small>
                          <b>{formatBiosecurityFlags(customsProfile?.biosecurity_flags)}</b>
                        </span>
                        <span>
                          <small>Current customs step</small>
                          <b>{formatCustomsStatus(customsProfile?.customs_status)}</b>
                        </span>
                      </div>
                    </article>
                  </div>

                  <div className="broker-invite-block">
                    <div>
                      <strong>Bring your customs broker into the workspace</strong>
                      <p>
                        Send a self-serve link your broker can open without creating an account. They will see the goods,
                        importer ABN, holds, and documents, and can submit clearance status updates back to this shipment.
                      </p>
                    </div>
                    <button
                      className="primary-action small"
                      type="button"
                      onClick={handleInviteBroker}
                      disabled={loading || !activeBooking}
                    >
                      <UserRound size={16} />
                      Invite broker
                    </button>
                    {brokerInviteMessage && <p className="muted">{brokerInviteMessage}</p>}
                    {brokerLink && (
                      <label className="broker-invite-url">
                        <span>Broker link</span>
                        <input
                          readOnly
                          value={`${globalThis.location?.origin ?? ''}/broker/${brokerLink.token}`}
                          onFocus={(event) => event.target.select()}
                        />
                      </label>
                    )}
                  </div>

                  <div className="customs-plain-note">
                    <span className="status-chip blue">Estimate only</span>
                    <p>
                      The container price is separate from border costs. Customs duty, GST, broker fees, and any inspection charges are
                      shown separately so the freight share stays transparent.
                    </p>
                  </div>
                </div>
              </section>
            )}

            {view === 'delivery' && (
              <section className="panel tracking-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Delivery</p>
                    <h2>Release and final delivery.</h2>
                  </div>
                  <MapPin size={24} />
                </div>
                <div className="clarity-hero tracking-hero">
                  <div className="clarity-hero-main">
                    <span className="hero-icon">
                      <MapPin size={22} />
                    </span>
                    <div>
                      <span className={`status-chip ${releaseStatus?.can_release ? 'green' : 'orange'}`}>
                        {releaseStatus?.can_release ? 'Ready to deliver' : 'Waiting for release'}
                      </span>
                      <h3>{profile.delivery_city}, {profile.delivery_country}</h3>
                      <p>Delivery belongs in Clear because it should only book once customs, payment, and release holds are clear.</p>
                    </div>
                  </div>
                  <div className="hero-summary-grid">
                    <DetailTile icon={<ShieldCheck size={18} />} label="Release status" value={releaseStatus ? sourceLabel(releaseStatus.release_status) : 'Loading'} />
                    <DetailTile icon={<Gauge size={18} />} label="Active holds" value={`${activeReleaseHolds.length}`} />
                    <DetailTile icon={<Truck size={18} />} label="Delivery method" value={deliveryPlan ? deliveryPlanMethodLabels[deliveryPlan.delivery_method] : 'Loading'} />
                  </div>
                </div>
                {deliveryPlan ? (
                  <div className="supplier-workflow-grid">
                    <section className="form-section document-step">
                      <div className="form-section-heading">
                        <span>1</span>
                        <div>
                          <strong>Delivery details</strong>
                          <small>Saved destination, unloading needs, delivery window, and trucker choice for this shipment.</small>
                        </div>
                      </div>
                      <div className="form-grid two">
                        <label>
                          <span>Delivery method</span>
                          <select
                            value={deliveryPlan.delivery_method}
                            onChange={(event) =>
                              setDeliveryPlan((current) =>
                                current ? { ...current, delivery_method: event.target.value as DeliveryPlanMethod } : current,
                              )
                            }
                          >
                            {(Object.keys(deliveryPlanMethodLabels) as DeliveryPlanMethod[]).map((method) => (
                              <option value={method} key={method}>
                                {deliveryPlanMethodLabels[method]}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label>
                          <span>Contact phone</span>
                          <input
                            value={deliveryPlan.destination_contact_phone ?? ''}
                            onChange={(event) =>
                              setDeliveryPlan((current) => (current ? { ...current, destination_contact_phone: event.target.value } : current))
                            }
                          />
                        </label>
                      </div>
                      <label>
                        <span>Delivery address</span>
                        <input
                          value={deliveryPlan.destination_address}
                          onChange={(event) =>
                            setDeliveryPlan((current) => (current ? { ...current, destination_address: event.target.value } : current))
                          }
                        />
                      </label>
                      <div className="form-grid three">
                        <label>
                          <span>Delivery contact</span>
                          <input
                            value={deliveryPlan.destination_contact_name}
                            onChange={(event) =>
                              setDeliveryPlan((current) => (current ? { ...current, destination_contact_name: event.target.value } : current))
                            }
                          />
                        </label>
                        <label>
                          <span>Window start</span>
                          <input
                            type="date"
                            value={deliveryPlan.delivery_window_start ?? ''}
                            onChange={(event) =>
                              setDeliveryPlan((current) => (current ? { ...current, delivery_window_start: event.target.value || null } : current))
                            }
                          />
                        </label>
                        <label>
                          <span>Window end</span>
                          <input
                            type="date"
                            value={deliveryPlan.delivery_window_end ?? ''}
                            onChange={(event) =>
                              setDeliveryPlan((current) => (current ? { ...current, delivery_window_end: event.target.value || null } : current))
                            }
                          />
                        </label>
                      </div>
                      <label>
                        <span>Equipment needed</span>
                        <input
                          value={deliveryPlan.equipment_required.join(', ')}
                          onChange={(event) =>
                            setDeliveryPlan((current) =>
                              current
                                ? {
                                    ...current,
                                    equipment_required: event.target.value
                                      .split(',')
                                      .map((item) => item.trim())
                                      .filter(Boolean),
                                  }
                                : current,
                            )
                          }
                        />
                      </label>
                      <button className="secondary-action small" type="button" onClick={handleDeliveryPlanSave} disabled={loading}>
                        <Check size={15} />
                        Save delivery details
                      </button>
                    </section>

                    <section className="form-section document-step">
                      <div className="form-section-heading">
                        <span>2</span>
                        <div>
                          <strong>Release gate</strong>
                          <small>Delivery booking stays blocked until customs, documents, payment, and review holds are clear.</small>
                        </div>
                      </div>
                      <div className="document-review-grid">
                        <DetailTile icon={<ShieldCheck size={18} />} label="Delivery status" value={sourceLabel(deliveryPlan.status)} />
                        <DetailTile icon={<CircleDollarSign size={18} />} label="Trucking estimate" value={formatMoney(deliveryPlan.trucking_quote_usd)} />
                        <DetailTile icon={<Gauge size={18} />} label="Release blockers" value={`${activeReleaseHolds.length}`} />
                      </div>
                      <div className="hold-grid">
                        {activeReleaseHolds.length ? (
                          activeReleaseHolds.map((hold) => (
                            <span className={`hold-chip ${hold.status}`} key={hold.id}>
                              <small>{formatReleaseHold(hold.hold_type)}</small>
                              <b>{sourceLabel(hold.status)}</b>
                              <em>{hold.reason}</em>
                            </span>
                          ))
                        ) : (
                          <span className="hold-chip cleared">
                            <small>Release gate</small>
                            <b>Clear</b>
                            <em>Delivery can be booked.</em>
                          </span>
                        )}
                      </div>
                      <div className="action-panel-buttons">
                        <button
                          className="primary-action small"
                          type="button"
                          onClick={handleBookDelivery}
                          disabled={loading || !releaseStatus?.can_release || deliveryPlan.status === 'booked' || deliveryPlan.status === 'delivered'}
                        >
                          <Truck size={15} />
                          Book delivery
                        </button>
                        <button
                          className="secondary-action small"
                          type="button"
                          onClick={handleMarkDelivered}
                          disabled={loading || deliveryPlan.status !== 'booked'}
                        >
                          <Check size={15} />
                          Mark delivered
                        </button>
                      </div>
                    </section>

                    <section className="form-section document-step">
                      <div className="form-section-heading">
                        <span>3</span>
                        <div>
                          <strong>Trucker and proof</strong>
                          <small>Courier invoices and proof of delivery should be uploaded by the partner or ingested from email.</small>
                        </div>
                      </div>
                      <div className="document-review-grid">
                        <DetailTile icon={<Receipt size={18} />} label="Courier invoice" value={deliveryPlan.courier_invoice_storage_key ? 'Stored' : 'Waiting'} />
                        <DetailTile icon={<FileText size={18} />} label="Proof of delivery" value={deliveryPlan.proof_of_delivery_storage_key ? 'Stored' : 'Waiting'} />
                        <DetailTile icon={<Check size={18} />} label="Delivered" value={deliveryPlan.delivered_at ? formatDateShort(deliveryPlan.delivered_at) : 'Not yet'} />
                      </div>
                      <div className="broker-invite-block">
                        <div>
                          <strong>Bring your destination trucker into the workspace</strong>
                          <p>
                            Send a self-serve link your trucker can open without an account. They mark pickup scheduled,
                            picked up from port, and delivered, then upload the proof of delivery. The release status gates
                            the delivered marker so the trucker cannot close out a shipment with outstanding holds.
                          </p>
                        </div>
                        <button
                          className="primary-action small"
                          type="button"
                          onClick={handleInviteTrucker}
                          disabled={loading || !activeBooking}
                        >
                          <Truck size={16} />
                          Invite trucker
                        </button>
                        {truckerInviteMessage && <p className="muted">{truckerInviteMessage}</p>}
                        {truckerLink && (
                          <label className="broker-invite-url">
                            <span>Trucker link</span>
                            <input
                              readOnly
                              value={`${globalThis.location?.origin ?? ''}/trucker/${truckerLink.token}`}
                              onFocus={(event) => event.target.select()}
                            />
                          </label>
                        )}
                      </div>
                    </section>
                  </div>
                ) : (
                  <div className="empty-state">
                    <MapPin size={42} />
                    <p>Create or choose a shipment before planning delivery.</p>
                  </div>
                )}
              </section>
            )}
          </div>
          </>
        ) : (
          <div className="workspace admin-workspace ops-workspace">
            <section className="panel admin-panel full ops-command-panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Ship Hoppa team</p>
                  <h2>Shared container sailings.</h2>
                </div>
                <button className="secondary-action" onClick={handleReleaseCheck} disabled={loading}>
                  <RefreshCw size={17} />
                  Check delivery blockers
                </button>
              </div>

              <div className="clarity-hero ops-hero">
                <div className="clarity-hero-main">
                  <span className="hero-icon">
                    <Gauge size={22} />
                  </span>
                  <div>
                    <span className="status-chip blue">Ship Hoppa team view</span>
                    <h3>{containers.length} planned shared containers</h3>
                    <p>
                      This tab shows the containers Ship Hoppa is filling or operating, plus the customer shipments assigned to each one.
                    </p>
                  </div>
                </div>
                <div className="hero-summary-grid">
                  <DetailTile icon={<ContainerIcon size={18} />} label="Planned containers" value={`${containers.length}`} />
                  <DetailTile icon={<ClipboardCheck size={18} />} label="Matched shipments" value={`${bookings.length}`} />
                  <DetailTile
                    icon={<ShieldCheck size={18} />}
                    label="Blocked deliveries"
                    value={`${bookings.filter((booking) => booking.release_status === 'blocked').length}`}
                  />
                </div>
              </div>

              <OpsWorldMap
                containers={containers}
                bookings={bookings}
                onOpenBooking={(bookingId) => {
                  void openOpsBooking(bookingId)
                }}
              />

              <div className="section-subhead ops-list-heading">
                <strong>List view</strong>
                <span>Same containers, with the details needed to run them.</span>
              </div>
              <div className="ops-sailing-grid">
                {containers.map((container) => {
                  const options = carrierOptions[container.id] ?? []
                  const shipmentBookings = bookings.filter((booking) => booking.container_id === container.id)
                  return (
                    <OpsSailingCard
                      key={container.id}
                      container={container}
                      shipmentBookings={shipmentBookings}
                      options={options}
                      loading={loading}
                      onLoadCarrierOptions={loadCarrierOptions}
                      onCommit={handleCommit}
                      onOpenBooking={(bookingId) => {
                        void openOpsBooking(bookingId)
                      }}
                    />
                  )
                })}
              </div>
            </section>

            <section className="panel admin-panel full">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Shipment work</p>
                  <h2>Customer shipments matched to containers.</h2>
                </div>
                <ClipboardCheck size={24} />
              </div>
              <div className="ops-shipment-grid">
                {bookings.slice(0, 8).map((booking) => (
                  <OpsShipmentCard
                    booking={booking}
                    key={booking.id}
                    selected={booking.id === activeBooking?.id}
                    onOpen={(bookingId) => {
                      void openOpsBooking(bookingId)
                    }}
                  />
                ))}
              </div>
            </section>

            <section className="panel admin-panel full">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Selected shipment</p>
                  <h2>{activeBooking ? `${activeBooking.id} shipment work` : 'No shipment selected.'}</h2>
                </div>
                <button
                  className="secondary-action"
                  type="button"
                  onClick={() => activeBooking && loadOperatingData(activeBooking.id)}
                  disabled={!activeBooking || loading}
                >
                  <RefreshCw size={17} />
                  Refresh work cards
                </button>
              </div>

              {activeBooking ? (
                <div className="ops-selected-layout">
                  <div className="clarity-hero ops-selected-hero">
                    <div className="clarity-hero-main">
                      <span className="hero-icon">
                        <PackageCheck size={22} />
                      </span>
                      <div>
                        <span className={`status-chip ${activeBooking.release_status === 'blocked' ? 'orange' : 'green'}`}>
                          {sourceLabel(activeBooking.release_status)}
                        </span>
                        <h3>{activeBooking.cargo_description ?? sourceLabel(activeBooking.cargo_category)}</h3>
                        <p>
                          {activeBooking.supplier_city} to {activeBooking.delivery_city} · {formatQuantity(activeBooking.cbm_estimate)} CBM
                        </p>
                      </div>
                    </div>
                    <div className="hero-summary-grid">
                      <DetailTile icon={<FileText size={18} />} label="Documents" value={checklist ? sourceLabel(checklist.checklist_status) : 'Loading'} />
                      <DetailTile icon={<Truck size={18} />} label="Tracking" value={sourceLabel(activeBooking.tracking_status)} />
                      <DetailTile icon={<Receipt size={18} />} label="Payment" value={sourceLabel(activeBooking.payment_status)} />
                    </div>
                  </div>

                  <div className="ops-grid">
                  <div className="ops-card">
                    <strong>Documents</strong>
                    <span>{checklist ? sourceLabel(checklist.checklist_status) : 'Not loaded'}</span>
                    <div className="mini-list">
                      {(checklist?.documents ?? []).slice(0, 4).map((document) => (
                        <div className="mini-row" key={document.id}>
                          <span>
                            {documentTypeLabels[document.document_type]} ({sourceLabel(document.status)})
                          </span>
                          <button
                            className="primary-action small"
                            type="button"
                            onClick={() => handleApproveDocument(document.id)}
                            disabled={loading || document.status === 'approved'}
                          >
                            Approve
                          </button>
                        </div>
                      ))}
                      {!checklist?.documents.length && <small>No uploads yet.</small>}
                    </div>
                  </div>

                  <div className="ops-card">
                    <strong>Movement</strong>
                    <span>{events.length ? `${events.length} events` : 'No events loaded'}</span>
                    <button className="secondary-action small" type="button" onClick={handleAddEvent} disabled={loading}>
                      <Truck size={15} />
                      Mark goods received
                    </button>
                  </div>

                  <div className="ops-card">
                    <strong>Supplier link</strong>
                    <span>{supplierLink ? `Token ${supplierLink.token.slice(0, 8)}...` : 'No link generated'}</span>
                    <button className="secondary-action small" type="button" onClick={handleSupplierLink} disabled={loading}>
                      <ArrowRight size={15} />
                      Create link
                    </button>
                    <button className="secondary-action small" type="button" onClick={handleSupplierUpload} disabled={loading || !supplierLink}>
                      <FileText size={15} />
                      Supplier upload
                    </button>
                    {supplierPortal && <small>{supplierPortal.supplier_instructions}</small>}
                  </div>

                  <div className="ops-card">
                    <strong>Delivery blockers</strong>
                    <span>{releaseStatus ? sourceLabel(releaseStatus.release_status) : 'Not loaded'}</span>
                    <span>
                      {releaseStatus
                        ? `${releaseStatus.holds.filter((hold) => hold.status === 'active').length} active holds`
                        : 'Awaiting hold check'}
                    </span>
                  </div>
                </div>
                </div>
              ) : (
                <div className="empty-state">
                  <ClipboardCheck size={42} />
                  <p>Select a shipment card to load its document, tracking, supplier, and release work.</p>
                </div>
              )}
            </section>

            <section className="panel admin-panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Notifications</p>
                  <h2>Operational feed.</h2>
                </div>
                <Bell size={23} />
              </div>
              <div className="notification-list">
                {(summary?.notifications ?? []).map((notification) => (
                  <NotificationCard notification={notification} key={notification.id} />
                ))}
              </div>
            </section>

            <section className="panel admin-panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Decision log</p>
                  <h2>Recent engine and operator decisions.</h2>
                </div>
                <ClipboardCheck size={24} />
              </div>
              <div className="notification-list">
                {(summary?.audit_events ?? []).map((event) => (
                  <div className="notification-item" key={event.id}>
                    <strong>
                      {event.event_type.replaceAll('_', ' ')} / {event.actor_role}
                    </strong>
                    <span>{event.message}</span>
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
