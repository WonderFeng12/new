<template>
  <div>
    <h2>合同详情</h2>
    <el-card v-loading="loading" style="margin:16px 0">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>合同号: {{ contract?.contract_no }}</span>
          <span>
            <el-tag :type="statusType(contract?.status)" size="small">{{ contract?.status }}</el-tag>
            <el-button size="small" style="margin-left:8px" @click="$router.push(`/contracts/${contract?.id}/edit`)" :disabled="contract?.status==='已下发'">编辑</el-button>
            <el-button size="small" type="warning" @click="handleGenerateImage" :disabled="contract?.status!=='草稿'">生成确认图</el-button>
            <el-button size="small" type="success" @click="handleConfirm" :disabled="contract?.status!=='草稿'">标记客户确认</el-button>
            <el-button size="small" type="primary" @click="handlePushDown" :disabled="contract?.status!=='保存' || contract?.is_pushed_down">下推工艺单</el-button>
          </span>
        </div>
      </template>

      <el-descriptions :column="3" border>
        <el-descriptions-item label="客户">{{ contract?.customer?.name }}</el-descriptions-item>
        <el-descriptions-item label="合同日期">{{ contract?.contract_date }}</el-descriptions-item>
        <el-descriptions-item label="交货日期">{{ contract?.delivery_date }}</el-descriptions-item>
        <el-descriptions-item label="规格描述">{{ contract?.spec_description }}</el-descriptions-item>
        <el-descriptions-item label="是否压花">{{ contract?.is_pressed ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="包装方式">{{ contract?.packaging_type }}</el-descriptions-item>
        <el-descriptions-item label="包边材料">{{ contract?.binding_material }}</el-descriptions-item>
        <el-descriptions-item label="包边宽度">{{ contract?.binding_width }}</el-descriptions-item>
        <el-descriptions-item label="包边色号">{{ contract?.binding_color_no }}</el-descriptions-item>
        <el-descriptions-item label="压花模型">{{ contract?.emboss_model }}</el-descriptions-item>
        <el-descriptions-item label="最新确认版本">V{{ contract?.latest_confirm_version }}</el-descriptions-item>
        <el-descriptions-item label="总金额">¥{{ contract?.total_amount?.toFixed(2) }}</el-descriptions-item>
      </el-descriptions>

      <el-divider>行项目</el-divider>
      <el-table :data="contract?.items || []" stripe size="small">
        <el-table-column prop="line_no" label="行号" width="60" />
        <el-table-column prop="pattern_code" label="花型代码" width="120" />
        <el-table-column prop="color_a" label="颜色A" width="80" />
        <el-table-column label="颜色A图片" min-width="180">
          <template #default="{ row }">
            <span v-for="(img, i) in [row.image_a_1, row.image_a_2, row.image_a_3].filter(Boolean)" :key="i">
              <el-image :src="img" style="width:40px;height:40px;margin:2px" :preview-src-list="[img]" />
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="color_b" label="颜色B" width="80" />
        <el-table-column label="颜色B图片" min-width="180">
          <template #default="{ row }">
            <span v-for="(img, i) in [row.image_b_1, row.image_b_2, row.image_b_3].filter(Boolean)" :key="i">
              <el-image :src="img" style="width:40px;height:40px;margin:2px" :preview-src-list="[img]" />
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="unit_price" label="单价" width="80" />
        <el-table-column prop="qty" label="数量" width="60" />
        <el-table-column prop="amount" label="金额" width="80" />
        <el-table-column prop="remark" label="备注" min-width="120" />
      </el-table>

      <el-divider>版本历史</el-divider>
      <el-table :data="versions" stripe size="small" v-if="versions.length">
        <el-table-column prop="version_no" label="版本" width="60">
          <template #default="{ row }">V{{ row.version_no }}</template>
        </el-table-column>
        <el-table-column prop="generated_at" label="生成时间" width="160" />
        <el-table-column prop="generated_by" label="生成人" width="100" />
        <el-table-column prop="change_log" label="变更说明" min-width="200" />
        <el-table-column prop="is_confirmed" label="已确认" width="70">
          <template #default="{ row }">{{ row.is_confirmed ? '是' : '否' }}</template>
        </el-table-column>
        <el-table-column prop="confirmed_at" label="确认时间" width="160" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getContract, generateConfirmImage, markConfirmed, getVersions } from '../../api/contract'
import { pushDownFromContract } from '../../api/processSheet'

const route = useRoute()
const router = useRouter()
const contract = ref(null)
const versions = ref([])
const loading = ref(false)

function statusType(s) {
  if (s === '草稿') return 'warning'
  if (s === '保存') return 'success'
  return 'info'
}

async function handleGenerateImage() {
  try {
    await generateConfirmImage(route.params.id)
    ElMessage.success('确认图已生成')
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '生成失败') }
}

async function handleConfirm() {
  try {
    await markConfirmed(route.params.id)
    ElMessage.success('已标记客户确认')
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
}

async function handlePushDown() {
  try {
    await pushDownFromContract(route.params.id)
    ElMessage.success('工艺单已下推')
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '下推失败') }
}

async function loadData() {
  loading.value = true
  try {
    const [cRes, vRes] = await Promise.all([
      getContract(route.params.id),
      getVersions(route.params.id),
    ])
    contract.value = cRes.data
    versions.value = vRes.data
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

onMounted(loadData)
</script>
