<script setup lang="ts">
import { computed, inject, onMounted, ref, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { MapChart as EMapChart } from 'echarts/charts'
import {
  GeoComponent,
  TooltipComponent,
  VisualMapComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { useDashboard } from '../composables/useDashboard'
import { matchCityGeoName, matchProvinceGeoName, PROVINCE_ADCODE } from '../utils/geo'

const MUNICIPALITIES = ['北京市', '上海市', '天津市', '重庆市']
const RED_GRADIENT = ['#fecaca', '#fca5a5', '#f87171', '#ef4444', '#dc2626', '#991b1b', '#7f1d1d']

use([EMapChart, GeoComponent, TooltipComponent, VisualMapComponent, CanvasRenderer])

const dashboard = inject<ReturnType<typeof useDashboard>>('dashboard')!
const mapReady = ref(false)
const activeMapName = ref('china')
const geoCityNames = ref<string[]>([])

async function ensureChinaMap() {
  const echarts = await import('echarts')
  if (!echarts.getMap('china')) {
    const resp = await fetch('https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json')
    const geoJson = await resp.json()
    echarts.registerMap('china', geoJson)
  }
}

async function loadProvinceGeo(provinceName: string) {
  const geoProvince = matchProvinceGeoName(provinceName)
  const adcode = PROVINCE_ADCODE[geoProvince]
  if (!adcode) return null
  const echarts = await import('echarts')
  const mapName = `province_${adcode}`
  if (!echarts.getMap(mapName)) {
    const resp = await fetch(`https://geo.datav.aliyun.com/areas_v3/bound/${adcode}_full.json`)
    const geoJson = await resp.json()
    echarts.registerMap(mapName, geoJson)
    return geoJson
  }
  return echarts.getMap(mapName)?.geoJson || null
}

async function loadRegionMap(provinceNames: string[]) {
  const echarts = await import('echarts')
  if (!provinceNames.length) {
    activeMapName.value = 'china'
    geoCityNames.value = []
    return
  }

  if (provinceNames.length === 1) {
    const geoProvince = matchProvinceGeoName(provinceNames[0])
    const geoJson = await loadProvinceGeo(provinceNames[0])
    const adcode = PROVINCE_ADCODE[geoProvince]
    if (geoJson && adcode) {
      activeMapName.value = `province_${adcode}`
      geoCityNames.value = (geoJson.features || [])
        .map((f: { properties?: { name?: string } }) => f.properties?.name || '')
        .filter(Boolean)
      return
    }
  }

  const features: object[] = []
  const cityNames: string[] = []
  for (const name of provinceNames) {
    const geoJson = await loadProvinceGeo(name)
    if (geoJson?.features) {
      features.push(...geoJson.features)
      for (const f of geoJson.features) {
        const n = f.properties?.name
        if (n) cityNames.push(n)
      }
    }
  }
  if (features.length) {
    const merged = { type: 'FeatureCollection' as const, features }
    echarts.registerMap('custom_multi', merged as Parameters<typeof echarts.registerMap>[1])
    activeMapName.value = 'custom_multi'
    geoCityNames.value = cityNames
  } else {
    activeMapName.value = 'china'
    geoCityNames.value = []
  }
}

async function syncMapScope() {
  const stats = dashboard.mapStats.value
  const { provinces, cities } = dashboard.filters
  if (cities.length || provinces.length) {
    const mapProvinces = stats?.map_provinces?.length
      ? stats.map_provinces
      : provinces
    await loadRegionMap(mapProvinces)
  } else {
    await ensureChinaMap()
    activeMapName.value = 'china'
    geoCityNames.value = []
  }
}

const mapTitle = computed(() => {
  const stats = dashboard.mapStats.value
  const { provinces, cities } = dashboard.filters
  const yearLabel = stats?.display_year ? `${stats.display_year}年` : ''
  const months = (stats?.display_months?.length ? stats.display_months : (stats?.display_month != null ? [stats.display_month] : []))
    .slice()
    .sort((a, b) => a - b)
  const monthLabel = months.length ? months.map((m) => `${m}月`).join('、') : ''
  const periodLabel = yearLabel && monthLabel ? `${yearLabel}${monthLabel}` : yearLabel
  if (!stats) return '地域硫化比例地图'
  if (cities.length) {
    return `${periodLabel}已选城市硫化占比（${cities.join('、')}，整体 ${stats.overall.ratio}%）`
  }
  if (provinces.length) {
    return `${periodLabel}已选省份各地市硫化占比（${provinces.join('、')}，整体 ${stats.overall.ratio}%）`
  }
  return periodLabel ? `${periodLabel}全国各省硫化比例地图` : '全国各省硫化比例地图'
})

const option = computed(() => {
  const stats = dashboard.mapStats.value
  if (!stats) return {}

  const isRegionDrill = activeMapName.value !== 'china'
  const { provinces } = dashboard.filters

  let data = stats.items.map((item) => {
    let geoName = item.name
    if (isRegionDrill) {
      geoName = matchCityGeoName(item.name, geoCityNames.value)
    } else {
      geoName = matchProvinceGeoName(item.name)
    }
    return {
      name: geoName,
      value: item.ratio,
      rawName: item.name,
      fault_count: item.fault_count,
      total_count: item.total_count,
    }
  })

  if (
    isRegionDrill &&
    provinces.length === 1 &&
    MUNICIPALITIES.includes(provinces[0]) &&
    stats.items.length === 1 &&
    !geoCityNames.value.includes(stats.items[0].name)
  ) {
    const item = stats.items[0]
    data = geoCityNames.value.map((geoName) => ({
      name: geoName,
      value: item.ratio,
      rawName: item.name,
      fault_count: item.fault_count,
      total_count: item.total_count,
    }))
  }

  if (!isRegionDrill && provinces.length) {
    const provSet = new Set(provinces)
    data = data.filter((d) => provSet.has(d.rawName))
  }

  const values = data.map((d) => d.value).filter((v): v is number => v != null)
  const maxValue = values.length ? Math.max(...values, 0.01) : 100
  // #region agent log
  fetch('http://127.0.0.1:7257/ingest/360fc412-7e43-42e5-b0ab-c12f332c6785',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'a5fec5'},body:JSON.stringify({sessionId:'a5fec5',hypothesisId:'H2',location:'MapChart.vue:option',message:'map visualMap range',data:{values,maxValue,itemCount:data.length,overall:stats.overall},timestamp:Date.now()})}).catch(()=>{});
  // #endregion

  return {
    tooltip: {
      trigger: 'item',
      formatter: (params: { name: string; value?: number | null; data?: { fault_count: number; total_count: number } }) => {
        const d = params.data
        if (!d) return `${params.name}<br/>无数据`
        const val = params.value ?? 0
        return `${params.name}<br/>硫化比例：${val}%<br/>硫化单板/总数：${d.fault_count}/${d.total_count}`
      },
    },
    visualMap: {
      min: 0,
      max: maxValue,
      left: 'left',
      bottom: 20,
      text: ['高', '低'],
      inRange: { color: RED_GRADIENT },
      outOfRange: { color: '#f3f4f6' },
    },
    series: [
      {
        name: '硫化比例',
        type: 'map',
        map: activeMapName.value,
        roam: true,
        zoom: isRegionDrill ? 1.1 : 1,
        itemStyle: {
          areaColor: '#f3f4f6',
          borderColor: '#d1d5db',
        },
        label: {
          show: true,
          formatter: (params: { value?: number | null; data?: { fault_count: number; total_count: number } }) => {
            const d = params.data
            if (!d || params.value == null) return ''
            return `${params.value}%\n(${d.fault_count}/${d.total_count})`
          },
          fontSize: isRegionDrill ? 11 : 10,
        },
        emphasis: { label: { show: true } },
        data,
      },
    ],
  }
})

function onChartClick(params: unknown) {
  const p = params as { data?: { rawName?: string } }
  const stats = dashboard.mapStats.value
  if (!p.data?.rawName || !stats) return

  if (stats.level === 'province') {
    dashboard.toggleProvince(p.data.rawName)
  } else if (stats.level === 'city' || stats.level === 'city_focus') {
    dashboard.toggleCity(p.data.rawName)
  }
}

onMounted(async () => {
  try {
    await ensureChinaMap()
    mapReady.value = true
    await syncMapScope()
  } catch {
    dashboard.statusText.value = '中国地图数据加载失败'
  }
})

watch(
  () => [dashboard.filters.provinces, dashboard.filters.cities, dashboard.mapStats.value],
  async () => {
    if (mapReady.value) await syncMapScope()
  },
  { deep: true },
)
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <span>{{ mapTitle }}</span>
      <span v-if="dashboard.mapStats.value && !dashboard.filters.provinces.length" class="hint">
        （点击省份可筛选）
      </span>
      <span v-else-if="dashboard.mapStats.value?.level === 'city'" class="hint">
        （点击城市可筛选）
      </span>
    </template>
    <div v-if="!dashboard.analyzed.value" class="placeholder">请先执行分析</div>
    <VChart
      v-else-if="mapReady"
      class="chart"
      :option="option"
      autoresize
      @click="onChartClick"
    />
    <div v-else class="placeholder">地图加载中...</div>
  </el-card>
</template>

<style scoped>
.chart {
  width: 100%;
  height: 520px;
}

.placeholder {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
}

.hint {
  margin-left: 8px;
  font-size: 12px;
  color: #9ca3af;
}
</style>
