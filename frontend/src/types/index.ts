export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface Category {
  id: number
  name: string
  description: string | null
  product_count: number
  created_at: string
}

export type ProductStatus = 'ACTIVE' | 'INACTIVE'

export interface Product {
  id: number
  sku: string
  name: string
  description: string | null
  category_id: number
  category_name: string
  cost_price: number
  selling_price: number
  unit: string
  safety_stock: number
  status: ProductStatus
  current_stock: number
  inventory_value: number
  created_at: string
  updated_at: string
}

export interface Warehouse {
  id: number
  code: string
  name: string
  location: string
  manager_name: string | null
  phone: string | null
  capacity: number
  status: ProductStatus
  sku_count: number
  total_units: number
  total_value: number
  utilization_percent: number
  created_at: string
}

export type InventoryStatus = 'IN_STOCK' | 'LOW_STOCK' | 'OUT_OF_STOCK'

export interface InventoryRecord {
  id: number
  product_id: number
  sku: string
  product_name: string
  category_name: string
  warehouse_id: number
  warehouse_code: string
  warehouse_name: string
  unit: string
  quantity: number
  reserved_quantity: number
  available_quantity: number
  safety_stock: number
  status: InventoryStatus
  updated_at: string
}

export interface WarehouseStock {
  warehouse_id: number
  warehouse_code: string
  warehouse_name: string
  quantity: number
}

export interface InventoryAlert {
  product_id: number
  sku: string
  product_name: string
  category_name: string
  unit: string
  current_stock: number
  safety_stock: number
  shortage: number
  suggested_replenishment: number
  status: Exclude<InventoryStatus, 'IN_STOCK'>
  warehouse_count: number
  warehouse_stock: WarehouseStock[]
}

export type TransactionType =
  | 'INBOUND'
  | 'OUTBOUND'
  | 'TRANSFER_IN'
  | 'TRANSFER_OUT'
  | 'ADJUSTMENT'

export interface InventoryTransaction {
  id: number
  transaction_no: string
  product_id: number
  sku: string
  product_name: string
  warehouse_id: number
  warehouse_name: string
  transaction_type: TransactionType
  quantity_change: number
  balance_after: number
  reference_type: string | null
  reference_id: number | null
  reference_no: string | null
  notes: string | null
  created_at: string
}

export interface DashboardSummary {
  total_units: number
  total_sku: number
  inventory_value: number
  low_stock_count: number
  out_of_stock_count: number
  warehouse_count: number
}

export interface TrendPoint {
  date: string
  inbound_quantity: number
  outbound_quantity: number
  net_change: number
}

export interface CategoryDistribution {
  category_id: number
  category_name: string
  units: number
  value: number
  product_count: number
}

export interface DashboardData {
  generated_at: string
  summary: DashboardSummary
  trend: TrendPoint[]
  category_distribution: CategoryDistribution[]
  low_stock: InventoryAlert[]
  recent_transactions: InventoryTransaction[]
}

export type DocumentStatus = 'DRAFT' | 'CONFIRMED' | 'COMPLETED' | 'CANCELLED'

export interface InboundItem {
  id: number
  product_id: number
  sku: string
  product_name: string
  unit: string
  quantity: number
  unit_cost: number
  line_total: number
}

export interface InboundOrder {
  id: number
  order_no: string
  warehouse_id: number
  warehouse_name: string
  supplier: string
  status: DocumentStatus
  notes: string | null
  created_by: string
  confirmed_at: string | null
  created_at: string
  item_count: number
  total_quantity: number
  total_value: number
  items: InboundItem[]
}

export interface OutboundItem {
  id: number
  product_id: number
  sku: string
  product_name: string
  unit: string
  quantity: number
  unit_price: number
  line_total: number
}

export interface OutboundOrder {
  id: number
  order_no: string
  warehouse_id: number
  warehouse_name: string
  customer: string
  status: DocumentStatus
  notes: string | null
  created_by: string
  confirmed_at: string | null
  created_at: string
  item_count: number
  total_quantity: number
  total_value: number
  items: OutboundItem[]
}

export interface TransferItem {
  id: number
  product_id: number
  sku: string
  product_name: string
  unit: string
  quantity: number
}

export interface StockTransfer {
  id: number
  transfer_no: string
  from_warehouse_id: number
  from_warehouse_name: string
  to_warehouse_id: number
  to_warehouse_name: string
  status: DocumentStatus
  notes: string | null
  created_by: string
  completed_at: string | null
  created_at: string
  item_count: number
  total_quantity: number
  items: TransferItem[]
}

export interface HealthData {
  status: string
  database: string
  version: string
  timestamp: string
}

export interface LineItemPayload {
  product_id: number
  quantity: number
  unit_cost?: number
  unit_price?: number
}

