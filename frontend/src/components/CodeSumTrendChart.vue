<script setup lang="ts">
import { computed, inject } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { useDashboard } from '../composables/useDashboard'

use([LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const dashboard = inject<ReturnType<typeof useDashboard>>('dashboard')!

const hasTrendData = computed(
  () => dashboard.trendSeries.value.some((s) => s.points.length > 0),
)

const option = computed(() => {
  const series = dashboard.trendSeries.value
  const xLabels: string[] = []
  const labelSet = new Set<string>()
  for (const s of series) {
    for (const p of s.points) {
      if (!labelSet.has(p.time_label)) {
        labelSet.add(p.time_label)
        xLabels.push(p.time_label)
      }
    }
  }
  xLabels.sort((a, b) => {
    const pa = series.flatMap((s) => s.points).find((p) => p.time_label === a)
    const pb = series.flatMap((s) => s.points).find((p) => p.time_label === b)
    if (!pa || !pb) return a.localeCompare(b)
    return pa.year !== pb.year ? pa.year - pb.year : pa.month - pb.month
  })

  return {
    tooltip: {
      trigger: 'axis',
      formatter(params: { seriesName: string; value: number; axisValue: string }[]) {
        if (!params?.length) return ''
        const lines = [`${params[0].axisValue}`]
        for (const p of params) {
          if (p.value != null) {
            lines.push(`${p.seriesName}: code合数 ${p.value}`)
          }
        }
        return lines.join('<br/>')
      },
    },
    legend: { type: 'scroll', bottom: 0 },
    grid: { left: 48, right: 16, top: 24, bottom: 48 },
    xAxis: { type: 'category', data: xLabels, name: '时间' },
    yAxis: { type: 'value', name: 'code合数', minInterval: 1 },
    series: series.map((s) => ({
      name: s.label,
      type: 'line',
      smooth: true,
      showSymbol: true,
      symbolSize: 8,
      connectNulls: false,
      data: xLabels.map((label) => {
        const pt = s.points.find((p) => p.time_label === label)
        return pt ? pt.code_sum : null
      }),
    })),
  }
})
</script>

<template>
  <el-card shadow="never">
    <template #header>单板硫化趋势</template>
    <div v-if="!dashboard.canShowTrend.value" class="placeholder">
      请先选择单板 sn（最多 10 个）以查看 code 合数趋势
    </div>
    <div v-else-if="!hasTrendData" class="placeholder">所选单板 sn 暂无趋势数据</div>
    <VChart v-else class="chart" :option="option" autoresize />
  </el-card>
</template>

<style scoped>
.chart {
  width: 100%;
  height: 360px;
}

.placeholder {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
}
</style>
