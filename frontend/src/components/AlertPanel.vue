<script setup lang="ts">
import { inject } from 'vue'
import type { useDashboard } from '../composables/useDashboard'

const dashboard = inject<ReturnType<typeof useDashboard>>('dashboard')!
</script>

<template>
  <el-card shadow="never">
    <template #header>
      硫化预警（硫化单板占比 &gt; 5%）
    </template>
    <el-table :data="dashboard.alerts.value" size="small" max-height="360" empty-text="暂无硫化预警">
      <el-table-column prop="province" label="省" width="100" />
      <el-table-column prop="city" label="市" width="120" />
      <el-table-column prop="fault_count" label="硫化单板数" width="110" />
      <el-table-column prop="total_count" label="单板总数" width="100" />
      <el-table-column prop="ratio" label="比例" width="90">
        <template #default="{ row }">{{ row.ratio }}%</template>
      </el-table-column>
    </el-table>
  </el-card>
</template>
