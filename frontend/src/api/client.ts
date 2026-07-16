import axios from 'axios'
import type {
  AlertItem,
  CodeBarItem,
  CodeSumTrendResponse,
  FilterOptions,
  MapStats,
} from '../types'

const http = axios.create({ baseURL: '/api' })

function joinList(values: string[]): string {
  return values.filter(Boolean).join(',')
}

function joinNums(values: number[]): string {
  return values.filter((v) => v != null).join(',')
}

export async function fetchDefaultFolder() {
  const { data } = await http.get<{ folder_path: string }>('/default-folder')
  return data.folder_path
}

export async function analyze(folderPath: string, extractZip = false) {
  const { data } = await http.post<{
    total_boards: number
    folder_path: string
    filters: FilterOptions
  }>('/analyze', { folder_path: folderPath, extract_zip: extractZip })
  return data
}

export async function fetchFilters(
  chips: string[] = [],
  provinces: string[] = [],
  cities: string[] = [],
  siteNames: string[] = [],
  years: number[] = [],
  months: number[] = [],
) {
  const { data } = await http.get<FilterOptions>('/filters', {
    params: {
      chip: chips.length ? joinList(chips) : undefined,
      province: provinces.length ? joinList(provinces) : undefined,
      city: cities.length ? joinList(cities) : undefined,
      site: siteNames.length ? joinList(siteNames) : undefined,
      years: years.length ? joinNums(years) : undefined,
      months: months.length ? joinNums(months) : undefined,
    },
  })
  return data
}

export async function fetchMap(
  chips: string[] = [],
  provinces: string[] = [],
  cities: string[] = [],
  siteNames: string[] = [],
  year: number | null = null,
  months: number[] = [],
) {
  const { data } = await http.get<MapStats>('/map', {
    params: {
      chip: joinList(chips),
      province: joinList(provinces),
      city: joinList(cities),
      site: joinList(siteNames),
      year,
      months: months.length ? joinNums(months) : undefined,
      month: months.length === 1 ? months[0] : undefined,
    },
  })
  return data
}

export async function fetchAlerts(
  chips: string[] = [],
  provinces: string[] = [],
  cities: string[] = [],
  siteNames: string[] = [],
  year: number | null = null,
  months: number[] = [],
) {
  const { data } = await http.get<AlertItem[]>('/alerts', {
    params: {
      chip: joinList(chips),
      province: joinList(provinces),
      city: joinList(cities),
      site: joinList(siteNames),
      year,
      months: months.length ? joinNums(months) : undefined,
      month: months.length === 1 ? months[0] : undefined,
    },
  })
  return data
}

export async function fetchCodeBar(
  chips: string[] = [],
  provinces: string[] = [],
  cities: string[] = [],
  siteNames: string[] = [],
  year: number | null = null,
  months: number[] = [],
) {
  const { data } = await http.get<CodeBarItem[]>('/charts/code-bar', {
    params: {
      chip: joinList(chips),
      province: joinList(provinces),
      city: joinList(cities),
      site: joinList(siteNames),
      year,
      months: months.length ? joinNums(months) : undefined,
      month: months.length === 1 ? months[0] : undefined,
    },
  })
  return data
}

export async function fetchCodeSumTrend(
  chips: string[] = [],
  provinces: string[] = [],
  cities: string[] = [],
  siteNames: string[] = [],
  years: number[] = [],
  months: number[] = [],
) {
  const { data } = await http.get<CodeSumTrendResponse>('/charts/code-sum-trend', {
    params: {
      chip: joinList(chips),
      province: joinList(provinces),
      city: joinList(cities),
      site: joinList(siteNames),
      years: years.length ? joinNums(years) : undefined,
      months: months.length ? joinNums(months) : undefined,
    },
  })
  return data
}

export function exportExcelUrl() {
  return '/api/export'
}
