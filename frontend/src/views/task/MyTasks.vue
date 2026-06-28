<template>
  <div>
    <h2>我的任务</h2>
    <el-table :data="tasks" stripe size="small" v-loading="loading" style="margin-top:16px">
      <el-table-column prop="contract_no" label="合同号" width="150" />
      <el-table-column prop="line_no" label="行号" width="60" />
      <el-table-column prop="spec_description" label="毛毯规格" min-width="160" />
      <el-table-column prop="qty" label="数量" width="80" />
      <el-table-column label="生产状态" width="120">
        <template #default="{ row }">
          <el-tag v-if="row.production_status === 'yarn_plan'" type="info">坯布计划已下达</el-tag>
          <el-tag v-else-if="row.production_status === 'weaving'" type="warning">织造中</el-tag>
          <el-tag v-else-if="row.production_status === 'cancelled'" type="danger">已取消</el-tag>
          <el-tag v-else type="success">{{ row.production_status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button
            v-if="row.production_status === 'weaving'"
            size="small"
            type="primary"
            @click="handleAdvance(row)"
          >推进</el-button>
          <span v-else-if="row.production_status === 'yarn_plan'" style="color:#999">等待开始</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getMyTasks, advanceItem } from '../../api/production'
import { ElMessage } from 'element-plus'

const tasks = ref([])
const loading = ref(false)

async function handleAdvance(row) {
  try {
    await advanceItem(row.id, { remark: '' })
    ElMessage.success('已推进')
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
}

async function loadData() {
  loading.value = true
  try {
    const res = await getMyTasks()
    tasks.value = res.data
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

onMounted(loadData)
</script>
