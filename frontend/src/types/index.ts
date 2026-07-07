export interface MapRegionItem {
  name: string
  ratio: number
  fault_count: number
  total_count: number
}

export interface MapStats {
  level: string
  items: MapRegionItem[]
  map_provinces: string[]
  display_year: number | null
  display_month: number | null
  overall: {
    ratio: number
    fault_count: number
    total_count: number
  }
}

export interface FilterOptions {
  chips: string[]
  provinces: string[]
  city_map: Record<string, string[]>
  years: number[]
  year_month_map: Record<number, number[]>
  site_names: string[]
  latest_year: number | null
  latest_month: number | null
  folder_path: string
}

export interface AlertItem {
  province: string
  city: string
  fault_count: number
  total_count: number
  ratio: number
}

export interface CodeBarItem {
  code_value: number
  code_hex: string
  board_count: number
}

export interface CodeSumTrendPoint {
  time_label: string
  year: number
  month: number
  code_sum: number
  site_name: string
}

export interface CodeSumTrendSeries {
  chip: string
  site_name: string
  label: string
  points: CodeSumTrendPoint[]
}

export interface CodeSumTrendResponse {
  series: CodeSumTrendSeries[]
}

export interface DashboardFilters {
  folderPath: string
  chips: string[]
  provinces: string[]
  cities: string[]
  siteNames: string[]
  years: number[]
  months: number[]
}
