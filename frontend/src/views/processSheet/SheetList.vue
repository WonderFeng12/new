<template>
  <div>
    <h2>工艺单管理</h2>
    <el-card style="margin:16px 0">
      <el-row :gutter="16">
        <el-col :span="8">
          <el-input v-model="keyword" placeholder="搜索工艺单号" clearable @clear="search" @keyup.enter="search" />
        </el-col>
        <el-col :span="16" style="text-align:right">
          <el-button type="primary" @click="search">搜索</el-button>
          <el-button type="success" @click="openCreateDialogFn">新建工艺单</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-table :data="sheets" v-loading="loading" stripe style="width:100%">
      <el-table-column prop="sheet_no" label="工艺单号" width="150" />
      <el-table-column label="合同号" width="150">
        <template #default="{ row }">{{ row.contract?.contract_no }}</template>
      </el-table-column>
      <el-table-column label="合同版本" width="90">
        <template #default="{ row }">V{{ row.confirm_version_no }}</template>
      </el-table-column>
      <el-table-column label="行项目数" width="80">
        <template #default="{ row }">{{ row.items?.length || 0 }}</template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_by" label="创建人" width="100" />
      <el-table-column prop="created_at" label="创建时间" width="160" />
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
          <el-button size="small" type="success" @click="handleConfirm(row)" :disabled="row.status!=='草稿'">确认</el-button>
          <el-button size="small" type="primary" @click="handleDispatch(row)" :disabled="row.status!=='保存'">下发</el-button>
          <el-popconfirm title="确认删除?" @confirm="handleDelete(row)">
            <template #reference>
              <el-button size="small" type="danger" :disabled="row.status==='已下发'">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建工艺单 dialog -->
    <el-dialog v-model="showCreateDialog" title="新建工艺单" width="600px">
      <el-form>
        <el-form-item label="选择合同">
          <el-select v-model="selectedContractId" filterable style="width:100%" placeholder="选择已确认的合同" @change="onContractChange">
            <el-option v-for="c in availableContracts" :key="c.id" :label="`${c.contract_no} - ${c.customer?.name}`" :value="c.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <div v-if="selectedContractItems.length > 0" style="margin-top:12px">
        <div style="font-weight:bold;margin-bottom:8px">选择行项目</div>
        <el-checkbox-group v-model="selectedItemIds">
          <div v-for="item in selectedContractItems" :key="item.id" style="padding:6px 8px;border-bottom:1px solid #eee;display:flex;align-items:center">
            <el-checkbox :value="item.id" :label="item.id" style="margin-right:8px" />
            <span>行{{ item.line_no }} - {{ item.spec_description || `规格#${item.spec_id}` }} - ¥{{ item.unit_price }} × {{ item.qty }}</span>
          </div>
        </el-checkbox-group>
        <div style="margin-top:8px">
          <el-button size="small" @click="selectAllItems">全选</el-button>
          <el-button size="small" @click="selectedItemIds = []">清空</el-button>
        </div>
      </div>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating" :disabled="selectedItemIds.length === 0">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listSheets, confirmSheet, dispatchSheet, deleteSheet, createSheet } from '../../api/processSheet'
import { getAvailableContracts } from '../../api/contract'

const router = useRouter()
const sheets = ref([])
const loading = ref(false)
const keyword = ref('')
const showCreateDialog = ref(false)
const availableContracts = ref([])
const selectedContractId = ref(null)
const selectedContractItems = ref([])
const selectedItemIds = ref([])
const creating = ref(false)

function statusType(s) {
  if (s === '草稿') return 'warning'
  if (s === '保存') return 'success'
  return 'info'
}

async function fetchData() {
  loading.value = true
  try {
    const res = await listSheets({ keyword: keyword.value })
    sheets.value = res.data
  } catch {}
  finally { loading.value = false }
}

function search() { fetchData() }
function viewDetail(row) { router.push(`/process-sheets/${row.id}`) }

async function handleConfirm(row) {
  try {
    await confirmSheet(row.id)
    ElMessage.success('已确认')
    fetchData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
}

async function handleDispatch(row) {
  try {
    await dispatchSheet(row.id)
    ElMessage.success('已下发')
    fetchData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
}

async function handleDelete(row) {
  try {
    await deleteSheet(row.id)
    ElMessage.success('已删除')
    fetchData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '删除失败') }
}

async function openCreateDialogFn() {
  try {
    const res = await getAvailableContracts()
    availableContracts.value = res.data
    selectedContractId.value = null
    selectedContractItems.value = []
    selectedItemIds.value = []
    showCreateDialog.value = true
  } catch { ElMessage.error('获取可用合同失败') }
}

function onContractChange(contractId) {
  const contract = availableContracts.value.find(c => c.id === contractId)
  selectedContractItems.value = contract?.items || []
  selectedItemIds.value = selectedContractItems.value.map(i => i.id)
}

function selectAllItems() {
  selectedItemIds.value = selectedContractItems.value.map(i => i.id)
}

async function handleCreate() {
  if (!selectedContractId.value) { ElMessage.warning('请选择合同'); return }
  if (selectedItemIds.value.length === 0) { ElMessage.warning('请至少选择一个行项目'); return }
  creating.value = true
  try {
    const res = await createSheet({
      contract_id: selectedContractId.value,
      contract_item_ids: selectedItemIds.value,
    })
    ElMessage.success('工艺单已创建')
    showCreateDialog.value = false
    selectedContractId.value = null
    selectedItemIds.value = []
    // Navigate to the new process sheet detail page
    const sheetId = res.data?.id
    if (sheetId) {
      router.push(`/process-sheets/${sheetId}`)
    } else {
      fetchData()
    }
  } catch (e) { ElMessage.error(e.response?.data?.detail || '创建失败') }
  finally { creating.value = false }
}

onMounted(fetchData)
</script>
