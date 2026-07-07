<script setup lang="ts">
import { onMounted, provide } from 'vue'
import Dashboard from './views/Dashboard.vue'
import { useDashboard } from './composables/useDashboard'

const dashboard = useDashboard()
provide('dashboard', dashboard)

onMounted(() => {
  dashboard.init()
})
</script>

<template>
  <Dashboard />
</template>

<style>
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC',
    'Microsoft YaHei', sans-serif;
  background: #f5f7fa;
  color: #1f2937;
}
</style>
