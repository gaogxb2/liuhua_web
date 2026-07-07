<script setup lang="ts">
import { inject } from 'vue'
import FilterBar from '../components/FilterBar.vue'
import MapChart from '../components/MapChart.vue'
import AlertPanel from '../components/AlertPanel.vue'
import CodeBarChart from '../components/CodeBarChart.vue'
import CodeSumTrendChart from '../components/CodeSumTrendChart.vue'
import type { useDashboard } from '../composables/useDashboard'

const dashboard = inject<ReturnType<typeof useDashboard>>('dashboard')!
</script>

<template>
  <div class="container">
    <header class="header">
      <h1>单板硫化问题分析</h1>
      <p>按地域与单板sn筛选，查看硫化比例与硫化预警</p>
    </header>

    <FilterBar />

    <section v-if="dashboard.analyzed.value && dashboard.canShowDetail.value" class="summary">
      <el-card shadow="never">
        <div class="metrics">
          <div class="metric">
            <div class="value">{{ dashboard.totalBoards.value }}</div>
            <div class="label">单板总数</div>
          </div>
          <div class="metric">
            <div class="value">{{ dashboard.mapStats.value?.overall.ratio ?? 0 }}%</div>
            <div class="label">整体硫化比例</div>
          </div>
          <div class="metric">
            <div class="value">{{ dashboard.alerts.value.length }}</div>
            <div class="label">硫化预警条数</div>
          </div>
        </div>
      </el-card>
    </section>

    <template v-if="dashboard.canShowDetail.value">
      <section class="panel">
        <MapChart />
      </section>

      <section class="panel">
        <AlertPanel />
      </section>

      <section class="panel">
        <CodeBarChart />
      </section>
    </template>

    <section v-else-if="dashboard.analyzed.value && dashboard.detailHint.value" class="panel">
      <el-card shadow="never">
        <p class="hint">{{ dashboard.detailHint.value }}</p>
      </el-card>
    </section>

    <section v-if="dashboard.analyzed.value" class="panel">
      <CodeSumTrendChart />
    </section>
  </div>
</template>

<style scoped>
.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px;
}

.header h1 {
  margin: 0 0 8px;
  font-size: 24px;
}

.header p {
  margin: 0 0 20px;
  color: #6b7280;
}

.summary {
  margin-bottom: 16px;
}

.metrics {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.metric .value {
  font-size: 28px;
  font-weight: 700;
  color: #dc2626;
}

.metric .label {
  font-size: 13px;
  color: #6b7280;
}

.panel {
  margin-bottom: 16px;
}

.hint {
  margin: 0;
  color: #6b7280;
  text-align: center;
  padding: 24px 0;
}
</style>
