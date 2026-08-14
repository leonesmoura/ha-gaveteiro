export interface Module {
  id: number
  name: string
  rows: number
  cols: number
  grid_col: number
  grid_row: number
}

export interface Category {
  id: number
  name: string
  color: string
}

export interface Part {
  id: number
  name: string
  description: string
  category_id: number | null
  category_name: string | null
  category_color: string | null
  package: string
  value: string
  manufacturer_code: string
  image_path: string | null
  datasheet_url: string
  min_qty: number
  notes: string
  total_quantity: number
  drawer_labels: string[]
  low_stock: boolean
}

export interface Drawer {
  id: number
  module_id: number
  module_name: string
  row: number
  col: number
  label: string
  description: string
  total_quantity: number
  part_count: number
  low_stock: boolean
  primary_color: string | null
}

export interface StockEntry {
  part: Part
  quantity: number
}

export interface DrawerDetail extends Drawer {
  entries: StockEntry[]
}

export interface Movement {
  id: number
  part_id: number
  part_name: string
  drawer_id: number
  drawer_label: string
  delta: number
  resulting_quantity: number
  reason: string
  created_at: string
}

export interface SearchResult {
  parts: Part[]
  drawer_ids: number[]
}

export interface AuthStatus {
  authenticated: boolean
  via_ingress: boolean
  username: string | null
}

export interface ModuleLayoutItem {
  id: number
  grid_col: number
  grid_row: number
  name?: string
}

export interface RenumberInput {
  modo: 'continuo' | 'por_modulo'
  inicio: number
  ordem: 'linha' | 'coluna'
  prefixo: string
}

export interface PartInput {
  name: string
  description?: string
  category_id?: number | null
  package?: string
  value?: string
  manufacturer_code?: string
  datasheet_url?: string
  min_qty?: number
  notes?: string
}
