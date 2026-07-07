<script setup lang="ts">
import { inject, ref } from 'vue'
import { exportExcelUrl } from '../api/client'
import type { useDashboard } from '../composables/useDashboard'

const dashboard = inject<ReturnType<typeof useDashboard>>('dashboard')!
const extractZip = ref(false)

function handleExport() {
  window.open(exportExcelUrl(), '_blank')
}
</script>

<template>
  <el-card shadow="never" class="filter-bar">
    <div class="row">
      <label>分析目录</label>
      <el-input v-model="dashboard.filters.folderPath" style="flex: 1" />
      <el-checkbox v-model="extractZip">自动解压 zip</el-checkbox>
      <el-button type="primary" :loading="dashboard.loading.value" @click="dashboard.runAnalyze(extractZip)">
        开始分析
      </el-button>
      <el-button @click="handleExport">导出 Excel</el-button>
    </div>

    <div v-if="dashboard.analyzed.value" class="row filters">
      <label>单板sn</label>
      <el-select
        v-model="dashboard.filters.chips"
        multiple
        filterable
        clearable
        collapse-tags
        collapse-tags-tooltip
        placeholder="全部单板sn"
        style="width: 240px"
        @change="dashboard.onFilterChange"
      >
        <el-option v-for="c in dashboard.filterOptions.value.chips" :key="c" :label="c" :value="c" />
      </el-select>

      <label>网元名称</label>
      <el-select
        v-model="dashboard.filters.siteNames"
        multiple
        filterable
        clearable
        collapse-tags
        collapse-tags-tooltip
        placeholder="全部网元"
        style="width: 200px"
        @change="dashboard.onFilterChange"
      >
        <el-option
          v-for="s in dashboard.filterOptions.value.site_names"
          :key="s"
          :label="s"
          :value="s"
        />
      </el-select>

      <label>省份</label>
      <el-select
        v-model="dashboard.filters.provinces"
        multiple
        filterable
        clearable
        collapse-tags
        collapse-tags-tooltip
        placeholder="全部省份"
        style="width: 200px"
        @change="dashboard.onFilterChange"
      >
        <el-option
          v-for="p in dashboard.filterOptions.value.provinces"
          :key="p"
          :label="p"
          :value="p"
        />
      </el-select>

      <label>城市</label>
      <el-select
        v-model="dashboard.filters.cities"
        multiple
        filterable
        clearable
        collapse-tags
        collapse-tags-tooltip
        placeholder="全部城市"
        style="width: 200px"
        @change="dashboard.onFilterChange"
      >
        <el-option v-for="c in dashboard.cityOptions.value" :key="c" :label="c" :value="c" />
      </el-select>

      <label>年份</label>
      <el-select
        v-model="dashboard.filters.years"
        multiple
        filterable
        clearable
        collapse-tags
        collapse-tags-tooltip
        placeholder="请选择年份"
        style="width: 140px"
        @change="dashboard.onYearMonthChange"
      >
        <el-option
          v-for="y in dashboard.filterOptions.value.years"
          :key="y"
          :label="String(y)"
          :value="y"
        />
      </el-select>

      <label>月份</label>
      <el-select
        v-model="dashboard.filters.months"
        multiple
        filterable
        clearable
        collapse-tags
        collapse-tags-tooltip
        placeholder="请选择月份"
        style="width: 140px"
        @change="dashboard.onYearMonthChange"
      >
        <el-option
          v-for="m in dashboard.monthOptions.value"
          :key="m"
          :label="`${m}月`"
          :value="m"
        />
      </el-select>

      <el-button @click="dashboard.resetRegionFilters">重置地域</el-button>
    </div>

    <p class="status">{{ dashboard.statusText.value }}</p>
  </el-card>
</template>

<style scoped>
.filter-bar .row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.filters {
  margin-top: 16px;
}

label {
  font-size: 14px;
  color: #374151;
}

.status {
  margin: 12px 0 0;
  font-size: 13px;
  color: #6b7280;
}
</style>
