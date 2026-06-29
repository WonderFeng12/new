<template>
  <el-table :data="logs" v-loading="loading" stripe size="small" max-height="500">
    <el-table-column
      v-if="columns.includes('时间')"
      prop="created_at"
      label="时间"
      width="160"
    />
    <el-table-column
      v-if="columns.includes('操作')"
      prop="operation_type"
      label="操作"
      width="100"
    />
    <el-table-column
      v-if="columns.includes('行号')"
      prop="item_no"
      label="行号"
      width="60"
    >
      <template #default="{ row }">
        {{ row.item_no || '─' }}
      </template>
    </el-table-column>
    <el-table-column
      v-if="columns.includes('从')"
      prop="from_status"
      label="从"
      width="100"
    />
    <el-table-column
      v-if="columns.includes('到')"
      prop="to_status"
      label="到"
      width="100"
    />
    <el-table-column
      v-if="columns.includes('操作人')"
      prop="operator_name"
      label="操作人"
      width="100"
    />
    <el-table-column
      prop="remark"
      label="备注"
      min-width="250"
    >
      <template #default="{ row }">
        <div style="white-space:pre-wrap">{{ row.remark }}</div>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
defineProps({
  logs: {
    type: Array,
    default: () => [],
  },
  columns: {
    type: Array,
    default: () => ['时间', '操作', '行号', '从', '到', '操作人', '备注'],
  },
  loading: {
    type: Boolean,
    default: false,
  },
})
</script>
