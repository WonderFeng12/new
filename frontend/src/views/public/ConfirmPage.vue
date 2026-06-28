<template>
  <div style="max-width:960px;margin:0 auto;padding:20px">
    <el-card v-loading="loading">
      <template #header>
        <div style="text-align:center">
          <h2 v-if="alreadyConfirmed" style="color:#909399">合同已确认</h2>
          <h2 v-else>合同确认</h2>
          <div v-if="contract" style="font-size:14px;color:#666">合同号: {{ contract.contract_no }}</div>
        </div>
      </template>

      <template v-if="alreadyConfirmed">
        <el-result icon="success" title="已确认" :sub-title="`合同 ${contract?.contract_no} 已被确认，状态: ${contract?.status}`" />
      </template>

      <template v-else-if="contract">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="客户">{{ contract.customer_name }}</el-descriptions-item>
          <el-descriptions-item label="合同日期">{{ contract.contract_date }}</el-descriptions-item>
          <el-descriptions-item label="交货日期">{{ contract.delivery_date || '—' }}</el-descriptions-item>
          <el-descriptions-item label="总金额">¥{{ contract.total_amount?.toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="包边材料">{{ contract.binding_material || '—' }}</el-descriptions-item>
          <el-descriptions-item label="包边宽度">{{ contract.binding_width || '—' }}</el-descriptions-item>
          <el-descriptions-item label="包边色号">{{ contract.binding_color_no || '—' }}</el-descriptions-item>
          <el-descriptions-item label="压花模型">{{ contract.emboss_model || '—' }}</el-descriptions-item>
        </el-descriptions>

        <el-divider>行项目</el-divider>
        <el-table :data="contract.items" stripe size="small">
          <el-table-column type="expand">
            <template #default="{ row }">
              <div style="padding:8px 16px">
                <div v-if="row.pattern_data?.length">
                  <div style="font-weight:bold;margin-bottom:4px">花型</div>
                  <div v-for="(p, pi) in row.pattern_data" :key="pi" style="display:flex;gap:8px;align-items:center;margin:4px 0;padding:4px 8px;background:#f5f7fa;border-radius:4px">
                    <el-tag size="small">{{ p.code }}</el-tag>
                    <span style="font-size:12px;color:#666">颜色: {{ p.color || '无色' }}</span>
                    <span style="font-size:12px;color:#666">数量: ×{{ p.qty }}</span>
                    <span style="font-size:12px;color:#666">包边色号: {{ p.binding_color_no || contract.binding_color_no || '—' }}</span>
                    <el-image v-if="p.image" :src="p.image" style="width:100px;height:100px;border-radius:4px;object-fit:cover;border:1px solid #dcdfe6;cursor:pointer" :preview-src-list="[p.image]" preview-teleported />
                  </div>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="line_no" label="行号" width="60" />
          <el-table-column label="毛毯规格" min-width="140">
            <template #default="{ row }">{{ row.spec_description }}</template>
          </el-table-column>
          <el-table-column label="包装方式" width="90">
            <template #default="{ row }">{{ row.packaging_type || '—' }}</template>
          </el-table-column>
          <el-table-column label="压花" width="60">
            <template #default="{ row }">{{ row.is_pressed ? '是' : '否' }}</template>
          </el-table-column>
          <el-table-column prop="unit_price" label="单价" width="70" />
          <el-table-column prop="qty" label="数量" width="60" />
          <el-table-column prop="amount" label="金额" width="80" />
        </el-table>

        <el-divider />
        <div v-if="contract.tech_notes?.length" style="margin-bottom:16px">
          <h4>技术要求</h4>
          <div v-for="(note, i) in contract.tech_notes" :key="i" style="padding:4px 0;font-size:13px">{{ note }}</div>
        </div>

        <el-divider />
        <h4>客户确认意见</h4>
        <el-input v-model="comment" type="textarea" :rows="4" placeholder="请输入您的确认意见（可选）" style="margin-bottom:16px" />

        <div style="text-align:center;margin:24px 0">
          <el-button type="primary" size="large" @click="handleConfirm" :loading="submitting" style="width:200px">确认合同</el-button>
        </div>
      </template>

      <template v-else-if="!loading">
        <el-result icon="error" title="无效链接" sub-title="该确认链接无效或合同已被删除" />
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const contract = ref(null)
const alreadyConfirmed = ref(false)
const loading = ref(true)
const submitting = ref(false)
const comment = ref('')

async function loadContract() {
  loading.value = true
  try {
    const res = await axios.get(`/api/public/contract/${route.params.token}`)
    if (res.data.already_confirmed) {
      alreadyConfirmed.value = true
      contract.value = res.data
    } else {
      contract.value = res.data
    }
  } catch {
    contract.value = null
  } finally {
    loading.value = false
  }
}

async function handleConfirm() {
  submitting.value = true
  try {
    await axios.post(`/api/public/confirm/${route.params.token}`, { comment: comment.value })
    await loadContract()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '确认失败')
  } finally {
    submitting.value = false
  }
}

onMounted(loadContract)
</script>
