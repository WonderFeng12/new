<template>
  <div>
    <h2>工艺单详情</h2>
    <el-card v-loading="loading" style="margin:16px 0">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>工艺单号: {{ sheet?.sheet_no }}</span>
          <span>
            <el-tag :type="statusType(sheet?.status)" size="small">{{ sheet?.status }}</el-tag>
            <el-button size="small" type="success" style="margin-left:8px" @click="handleConfirm" :disabled="sheet?.status!=='草稿'">确认工艺单</el-button>
            <el-button size="small" type="primary" @click="handleDispatch" :disabled="sheet?.status!=='保存'">下发工艺单</el-button>
          </span>
        </div>
      </template>

      <el-descriptions :column="3" border>
        <el-descriptions-item label="合同号">{{ sheet?.contract?.contract_no }}</el-descriptions-item>
        <el-descriptions-item label="合同版本">V{{ sheet?.confirm_version_no }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ sheet?.status }}</el-descriptions-item>
        <el-descriptions-item label="创建人">{{ sheet?.created_by }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ sheet?.created_at }}</el-descriptions-item>
      </el-descriptions>

      <el-divider>合同信息（基于合同 V{{ sheet?.confirm_version_no }}）</el-divider>

      <el-descriptions :column="3" border v-if="sheet?.contract">
        <el-descriptions-item label="客户名称">{{ sheet.contract.customer?.name }}</el-descriptions-item>
        <el-descriptions-item label="合同日期">{{ sheet.contract.contract_date }}</el-descriptions-item>
        <el-descriptions-item label="交货日期">{{ sheet.contract.delivery_date }}</el-descriptions-item>
        <el-descriptions-item label="规格描述">{{ sheet.contract.spec_description }}</el-descriptions-item>
        <el-descriptions-item label="是否压花">{{ sheet.contract.is_pressed ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="包装方式">{{ sheet.contract.packaging_type }}</el-descriptions-item>
        <el-descriptions-item label="包边材料">{{ sheet.contract.binding_material }}</el-descriptions-item>
        <el-descriptions-item label="包边宽度">{{ sheet.contract.binding_width }}</el-descriptions-item>
        <el-descriptions-item label="包边色号">{{ sheet.contract.binding_color_no }}</el-descriptions-item>
        <el-descriptions-item label="压花模型">{{ sheet.contract.emboss_model }}</el-descriptions-item>
        <el-descriptions-item label="总金额">¥{{ sheet.contract.total_amount?.toFixed(2) }}</el-descriptions-item>
      </el-descriptions>

      <el-divider>工艺说明</el-divider>
      <el-descriptions :column="2" border v-if="sheet?.contract">
        <el-descriptions-item v-for="i in 10" :key="'tn'+i" :label="'说明'+i">
          {{ sheet.contract[`tech_note_${i}`] }}
        </el-descriptions-item>
      </el-descriptions>

      <el-divider>辅料信息</el-divider>
      <el-table :data="accessories" stripe size="small" v-if="accessories.length">
        <el-table-column prop="desc" label="辅料名称" />
        <el-table-column prop="size" label="规格" />
        <el-table-column prop="qty" label="数量" />
      </el-table>

      <el-divider>包装箱单</el-divider>
      <el-descriptions :column="2" border v-if="sheet?.contract">
        <el-descriptions-item v-for="i in 5" :key="'pn'+i" :label="'包装'+i">
          {{ sheet.contract[`pack_note_${i}`] }}
        </el-descriptions-item>
      </el-descriptions>
      <el-descriptions :column="3" border v-if="sheet?.contract" style="margin-top:8px">
        <el-descriptions-item v-for="i in 3" :key="'bn'+i" :label="'箱单'+i">
          {{ sheet.contract[`box_note_${i}`] }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getSheet, confirmSheet, dispatchSheet } from '../../api/processSheet'

const route = useRoute()
const router = useRouter()
const sheet = ref(null)
const loading = ref(false)

const accessories = computed(() => {
  if (!sheet.value?.contract) return []
  const c = sheet.value.contract
  const result = []
  for (let i = 1; i <= 6; i++) {
    if (c[`accessory_desc_${i}`]) {
      result.push({ desc: c[`accessory_desc_${i}`], size: c[`accessory_size_${i}`], qty: c[`accessory_qty_${i}`] })
    }
  }
  return result
})

function statusType(s) {
  if (s === '草稿') return 'warning'
  if (s === '保存') return 'success'
  return 'info'
}

async function handleConfirm() {
  try {
    await confirmSheet(route.params.id)
    ElMessage.success('已确认')
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
}

async function handleDispatch() {
  try {
    await dispatchSheet(route.params.id)
    ElMessage.success('已下发')
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
}

async function loadData() {
  loading.value = true
  try {
    const res = await getSheet(route.params.id)
    sheet.value = res.data
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

onMounted(loadData)
</script>
