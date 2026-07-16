import axios from 'axios'
import { ElMessage } from 'element-plus'
import { computed, reactive, ref } from 'vue'
import {
  analyze,
  fetchAlerts,
  fetchCodeBar,
  fetchCodeSumTrend,
  fetchDefaultFolder,
  fetchFilters,
  fetchMap,
} from '../api/client'
import type {
  AlertItem,
  CodeBarItem,
  CodeSumTrendSeries,
  DashboardFilters,
  FilterOptions,
  MapStats,
} from '../types'

const MAX_TREND_CHIPS = 10

export function useDashboard() {
  const loading = ref(false)
  const statusText = ref('就绪')
  const analyzed = ref(false)
  const totalBoards = ref(0)

  const filters = reactive<DashboardFilters>({
    folderPath: '',
    chips: [],
    provinces: [],
    cities: [],
    siteNames: [],
    years: [],
    months: [],
  })

  const filterOptions = ref<FilterOptions>({
    chips: [],
    provinces: [],
    city_map: {},
    standalone_cities: [],
    years: [],
    year_month_map: {},
    site_names: [],
    latest_year: null,
    latest_month: null,
    folder_path: '',
  })

  const cityOptions = computed(() => {
    const cities = new Set<string>()
    const selectedProvinces = filters.provinces.length
      ? filters.provinces
      : filterOptions.value.provinces
    for (const p of selectedProvinces) {
      for (const c of filterOptions.value.city_map[p] || []) {
        cities.add(c)
      }
    }
    for (const c of filterOptions.value.standalone_cities || []) {
      cities.add(c)
    }
    return Array.from(cities).sort()
  })

  const monthOptions = computed(() => {
    const map = filterOptions.value.year_month_map as Record<string, number[]>
    const months = new Set<number>()
    const selectedYears = filters.years.length
      ? filters.years
      : filterOptions.value.years
    for (const y of selectedYears) {
      for (const m of map[String(y)] || []) {
        months.add(m)
      }
    }
    return Array.from(months).sort((a, b) => a - b)
  })

  const canShowDetail = computed(
    () => filters.years.length === 1 && filters.months.length >= 1,
  )

  const detailHint = computed(() => {
    if (!analyzed.value) return ''
    if (filters.years.length === 0 || filters.months.length === 0) {
      return '请选择单个年份，并至少选择一个月份以查看地图、硫化预警与单板数量分布。'
    }
    if (filters.years.length > 1) {
      return '地图、硫化预警与单板数量分布仅支持单个年份（可多选月份），请只保留一年。'
    }
    return ''
  })

  const canShowTrend = computed(
    () => filters.chips.length >= 1 && filters.chips.length <= MAX_TREND_CHIPS,
  )

  const mapStats = ref<MapStats | null>(null)
  const alerts = ref<AlertItem[]>([])
  const codeBarData = ref<CodeBarItem[]>([])
  const trendSeries = ref<CodeSumTrendSeries[]>([])

  function limitTrendChips() {
    if (filters.chips.length > MAX_TREND_CHIPS) {
      filters.chips = filters.chips.slice(0, MAX_TREND_CHIPS)
      ElMessage.warning(`硫化趋势最多同时展示 ${MAX_TREND_CHIPS} 个单板 sn`)
    }
  }

  function syncMonthsAfterYearChange() {
    const valid = new Set(monthOptions.value)
    filters.months = filters.months.filter((m) => valid.has(m))
  }

  async function init() {
    filters.folderPath = await fetchDefaultFolder()
  }

  async function refreshFilterOptions() {
    const options = await fetchFilters(
      filters.chips,
      filters.provinces,
      filters.cities,
      filters.siteNames,
      filters.years,
      filters.months,
    )
    filterOptions.value = {
      ...filterOptions.value,
      ...options,
      site_names: options.site_names ?? [],
    }
    const validChips = new Set(filterOptions.value.chips)
    filters.chips = filters.chips.filter((c) => validChips.has(c))
    const validSites = new Set(filterOptions.value.site_names)
    filters.siteNames = filters.siteNames.filter((s) => validSites.has(s))
    const validProvinces = new Set(filterOptions.value.provinces)
    filters.provinces = filters.provinces.filter((p) => validProvinces.has(p))
    const validCities = new Set(cityOptions.value)
    filters.cities = filters.cities.filter((c) => validCities.has(c))
    const validYears = new Set(filterOptions.value.years)
    filters.years = filters.years.filter((y) => validYears.has(y))
    syncMonthsAfterYearChange()
    // #region agent log
    fetch('http://127.0.0.1:7294/ingest/d453560c-d6b4-4b8f-badc-3989933f19f1',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c939a3'},body:JSON.stringify({sessionId:'c939a3',runId:'post-fix',hypothesisId:'H3-H5',location:'useDashboard.ts:refreshFilterOptions',message:'cascading options refreshed',data:{chips:filters.chips,sites:filters.siteNames,provinces:filters.provinces,years:filters.years,months:filters.months,optChips:options.chips?.length,optSites:options.site_names?.length,optProvinces:options.provinces,optYears:options.years,optMonthsMap:options.year_month_map},timestamp:Date.now()})}).catch(()=>{});
    // #endregion
  }

  async function refreshTrend() {
    if (!analyzed.value || !canShowTrend.value) {
      trendSeries.value = []
      return
    }
    const { chips, provinces, cities, siteNames } = filters
    // 趋势图默认展示全时间序列；仅多选年/月时才按时间范围过滤
    const trendYears = filters.years.length > 1 || filters.months.length > 1 ? filters.years : []
    const trendMonths = filters.years.length > 1 || filters.months.length > 1 ? filters.months : []
    const result = await fetchCodeSumTrend(chips, provinces, cities, siteNames, trendYears, trendMonths)
    trendSeries.value = result.series
    // #region agent log
    fetch('http://127.0.0.1:7257/ingest/360fc412-7e43-42e5-b0ab-c12f332c6785',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'a5fec5'},body:JSON.stringify({sessionId:'a5fec5',hypothesisId:'T1',location:'useDashboard.ts:refreshTrend',message:'trend fetched',data:{chips,trendYears,trendMonths,seriesCount:result.series.length,pointCounts:result.series.map(s=>s.points.length)},timestamp:Date.now()})}).catch(()=>{});
    // #endregion
  }

  async function refreshCharts() {
    if (!analyzed.value) return

    await refreshTrend()

    // #region agent log
    fetch('http://127.0.0.1:7294/ingest/d453560c-d6b4-4b8f-badc-3989933f19f1',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c939a3'},body:JSON.stringify({sessionId:'c939a3',runId:'pre-fix',hypothesisId:'H1-H2',location:'useDashboard.ts:refreshCharts',message:'detail gate before map/alerts/bar',data:{canShowDetail:canShowDetail.value,years:filters.years,months:filters.months,yearsLen:filters.years.length,monthsLen:filters.months.length},timestamp:Date.now()})}).catch(()=>{});
    // #endregion

    if (!canShowDetail.value) {
      mapStats.value = null
      alerts.value = []
      codeBarData.value = []
      totalBoards.value = 0
      return
    }

    const { chips, provinces, cities, siteNames } = filters
    const year = filters.years[0]
    const months = [...filters.months].sort((a, b) => a - b)
    const [map, alertList, bar] = await Promise.all([
      fetchMap(chips, provinces, cities, siteNames, year, months),
      fetchAlerts(chips, provinces, cities, siteNames, year, months),
      fetchCodeBar(chips, provinces, cities, siteNames, year, months),
    ])
    mapStats.value = map
    alerts.value = alertList
    codeBarData.value = bar
    totalBoards.value = map.overall.total_count
    // #region agent log
    fetch('http://127.0.0.1:7294/ingest/d453560c-d6b4-4b8f-badc-3989933f19f1',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c939a3'},body:JSON.stringify({sessionId:'c939a3',runId:'post-fix',hypothesisId:'H1-H4',location:'useDashboard.ts:refreshCharts',message:'frontend totalBoards from map',data:{totalBoards:map.overall.total_count,year,months,fault:map.overall.fault_count,chips,provinces,cities,siteNames},timestamp:Date.now()})}).catch(()=>{});
    // #endregion
  }

  async function runAnalyze(extractZip = false) {
    loading.value = true
    statusText.value = '正在分析...'
    try {
      const result = await analyze(filters.folderPath, extractZip)
      analyzed.value = true
      filterOptions.value = {
        ...filterOptions.value,
        ...result.filters,
        site_names: result.filters.site_names ?? [],
      }
      filters.chips = []
      filters.provinces = []
      filters.cities = []
      filters.siteNames = []
      filters.years = result.filters.latest_year != null ? [result.filters.latest_year] : []
      filters.months = result.filters.latest_month != null ? [result.filters.latest_month] : []
      // 默认最近年月后，按年月收窄其余下拉可选项
      await refreshFilterOptions()
      await refreshCharts()
      const y = filters.years[0]
      const ms = [...filters.months].sort((a, b) => a - b)
      const monthLabel = ms.length === 1 ? `${ms[0]}月` : ms.map((m) => `${m}月`).join('、')
      statusText.value = `分析完成，共 ${totalBoards.value} 块单板（${y}年${monthLabel}）`
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        statusText.value = String(err.response?.data?.detail || '分析失败')
      } else if (err instanceof Error) {
        statusText.value = err.message
      } else {
        statusText.value = '分析失败'
      }
      analyzed.value = false
    } finally {
      loading.value = false
    }
  }

  async function onFilterChange() {
    if (!analyzed.value) return
    limitTrendChips()
    await refreshFilterOptions()
    await refreshCharts()
  }

  async function onYearMonthChange() {
    if (!analyzed.value) return
    await refreshFilterOptions()
    await refreshCharts()
  }

  function resetRegionFilters() {
    filters.provinces = []
    filters.cities = []
    onFilterChange()
  }

  function toggleProvince(province: string) {
    if (!filters.provinces.includes(province)) {
      filters.provinces = [...filters.provinces, province]
      filters.cities = []
    }
    onFilterChange()
  }

  function toggleCity(city: string) {
    if (!filters.cities.includes(city)) {
      filters.cities = [...filters.cities, city]
    }
    onFilterChange()
  }

  return {
    loading,
    statusText,
    analyzed,
    totalBoards,
    filters,
    filterOptions,
    cityOptions,
    monthOptions,
    canShowDetail,
    detailHint,
    canShowTrend,
    mapStats,
    alerts,
    codeBarData,
    trendSeries,
    init,
    runAnalyze,
    onFilterChange,
    onYearMonthChange,
    resetRegionFilters,
    toggleProvince,
    toggleCity,
    refreshCharts,
  }
}
