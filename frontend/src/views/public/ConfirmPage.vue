<template>
  <div style="max-width:960px;margin:0 auto;padding:20px">
    <el-card v-loading="loading">
      <template #header>
        <div style="text-align:center">
          <h2 v-if="alreadyConfirmed" style="color:#909399">工艺单已确认</h2>
          <h2 v-else>工艺单确认</h2>
          <div v-if="sheet" style="font-size:14px;color:#666">
            工艺单号: {{ sheet.sheet_no }} | 合同号: {{ sheet.contract_contract_no }}
          </div>
        </div>
      </template>

      <template v-if="alreadyConfirmed">
        <el-result icon="success" title="已确认" :sub-title="`工艺单 ${sheet?.sheet_no} 已被确认`" />
      </template>

      <template v-else-if="sheet">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="客户">{{ sheet.contract_customer_name }}</el-descriptions-item>
          <el-descriptions-item label="合同日期">{{ sheet.contract_date }}</el-descriptions-item>
          <el-descriptions-item label="版本">
            <el-tag size="small" v-if="sheet.confirm_version_no">{{ formatVersion(sheet.confirm_version_no) }}</el-tag>
            <span v-else>—</span>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider>行项目</el-divider>
        <el-table :data="sheet.items" stripe size="small">
          <el-table-column prop="line_no" label="行号" width="60" />
          <el-table-column label="毛毯规格" min-width="140">
            <template #default="{ row }">{{ row.spec_description }}</template>
          </el-table-column>
          <el-table-column label="包装方式" width="90">
            <template #default="{ row }">{{ row.packaging_type || '—' }}</template>
          </el-table-column>
          <el-table-column label="压花" width="55">
            <template #default="{ row }">{{ row.is_pressed ? '是' : '否' }}</template>
          </el-table-column>
          <el-table-column label="颜色" min-width="100">
            <template #default="{ row }">{{ [row.color_a, row.color_b].filter(Boolean).join(' / ') || '—' }}</template>
          </el-table-column>
          <el-table-column label="交货日期" width="100">
            <template #default="{ row }">{{ row.delivery_date || '—' }}</template>
          </el-table-column>
          <el-table-column prop="qty" label="数量(条)" width="75" />
          <el-table-column label="工艺备注" min-width="120">
            <template #default="{ row }">{{ row.process_remark || '—' }}</template>
          </el-table-column>
        </el-table>

        <el-divider />
        <h4>客户确认意见</h4>
        <el-input v-model="comment" type="textarea" :rows="4" placeholder="请输入您的确认意见（可选）" style="margin-bottom:16px" />

        <div style="text-align:center;margin:24px 0">
          <el-button type="primary" size="large" @click="handleConfirm" :loading="submitting" style="width:200px">确认工艺单</el-button>
        </div>
      </template>

      <template v-else-if="!loading">
        <el-result icon="error" title="无效链接" sub-title="该确认链接无效或工艺单已被删除" />
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const route = useRoute()
const sheet = ref(null)
const alreadyConfirmed = ref(false)
const loading = ref(true)
const submitting = ref(false)
const comment = ref('')

function formatVersion(v) {
  if (!v || v === 0) return ''
  if (Number.isInteger(v)) return `V${v}`
  return `V${v.toFixed(2)}`
}

async function loadSheet() {
  loading.value = true
  try {
    const res = await axios.get(`/api/public/process-sheet/${route.params.token}`)
    if (res.data.already_confirmed) {
      alreadyConfirmed.value = true
      sheet.value = res.data
    } else {
      sheet.value = res.data
    }
  } catch {
    sheet.value = null
  } finally {
    loading.value = false
  }
}

async function handleConfirm() {
  submitting.value = true
  try {
    await axios.post(`/api/public/process-sheet/${route.params.token}/confirm`, { comment: comment.value })
    ElMessage.success('确认成功')
    await loadSheet()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '确认失败')
  } finally {
    submitting.value = false
  }
}

onMounted(loadSheet)
</script>
