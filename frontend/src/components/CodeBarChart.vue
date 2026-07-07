<script setup lang="ts">
import { computed, inject } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { useDashboard } from '../composables/useDashboard'

use([BarChart, GridComponent, TooltipComponent, CanvasRenderer])

const dashboard = inject<ReturnType<typeof useDashboard>>('dashboard')!

const option = computed(() => {
  const data = dashboard.codeBarData.value
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 16, top: 24, bottom: 48 },
    xAxis: {
      type: 'category',
      data: data.map((d) => d.code_hex),
      name: 'Code 值',
    },
    yAxis: {
      type: 'value',
      name: '单板数量',
      minInterval: 1,
    },
    series: [
      {
        type: 'bar',
        data: data.map((d) => d.board_count),
        itemStyle: { color: '#2563eb' },
      },
    ],
  }
})
</script>

<template>
  <el-card shadow="never">
    <template #header>单板数量分布</template>
    <div v-if="!dashboard.analyzed.value" class="placeholder">请先执行分析</div>
    <VChart v-else class="chart" :option="option" autoresize />
  </el-card>
</template>

<style scoped>
.chart {
  width: 100%;
  height: 320px;
}

.placeholder {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
}
</style>
