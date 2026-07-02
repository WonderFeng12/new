<template>
  <div>
    <h2>合同管理</h2>
    <el-card style="margin:16px 0">
      <el-row :gutter="16">
        <el-col :span="8">
          <el-input v-model="keyword" placeholder="搜索: 合同号/客户/规格/包装方式/工艺单号/坯布计划单号" clearable @clear="search" @keyup.enter="search" />
        </el-col>
        <el-col :span="16" style="text-align:right">
          <el-button type="primary" @click="search">搜索</el-button>
          <el-button type="success" @click="openCreate">新建合同</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-table :data="sortedItems" v-loading="loading" stripe style="width:100%" @row-click="viewDetail" @sort-change="onSortChange">
      <el-table-column prop="contract_no" label="合同号" width="140" sortable="custom" />
      <el-table-column prop="line_no" label="行号" width="50" sortable="custom" />
      <el-table-column label="客户" width="110" sortable="custom" prop="_customer">
        <template #default="{ row }">{{ row._contract?.customer?.name }}</template>
      </el-table-column>
      <el-table-column prop="contract_date" label="日期" width="100" sortable="custom" />
      <el-table-column label="规格" min-width="180" sortable="custom" prop="_spec">
        <template #default="{ row }">{{ row.spec_description || '—' }}</template>
      </el-table-column>
      <el-table-column label="包装方式" width="90" sortable="custom" prop="packaging_type">
        <template #default="{ row }">{{ row.packaging_type || '—' }}</template>
      </el-table-column>
      <el-table-column prop="qty" label="数量" width="65" sortable="custom" />
      <el-table-column label="生产进度" width="130" sortable="custom" prop="production_status">
        <template #default="{ row }">
          <el-tag v-if="!row.production_status" size="small" type="info">待坯布计划</el-tag>
          <el-tag v-else-if="row.production_status==='cancelled'" size="small" type="danger">已取消</el-tag>
          <el-tag v-else size="small" :type="progressTagType(row)">{{ stepLabel(row.production_status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="合同状态" width="90" sortable="custom" prop="_contract_status">
        <template #default="{ row }">
          <el-tag :type="statusType(row._contract?.computed_status || row._contract?.status)" size="small">{{ row._contract?.computed_status || row._contract?.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click.stop="viewDetail(row._contract)">详情</el-button>
          <el-button size="small" type="primary" @click.stop="openEdit(row._contract)" :disabled="row._contract?.status!=='草稿' && row._contract?.status!=='确认'">编辑</el-button>
          <el-popconfirm title="确认删除?" @confirm.stop="handleDelete(row._contract)">
            <template #reference>
              <el-button size="small" type="danger" :disabled="row._contract?.status!=='草稿'" @click.stop>删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="total > 0"
      v-model:current-page="page"
      :page-size="pageSize"
      :total="total"
      layout="prev, pager, next, total"
      style="margin-top:16px;text-align:right"
      @current-change="fetchData"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listContracts, deleteContract } from '../../api/contract'
import { listProcessSteps } from '../../api/production'
import { ElMessage } from 'element-plus'

const router = useRouter()
const contracts = ref([])
const loading = ref(false)
const keyword = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const processSteps = ref([])

const sortState = ref({ prop: '', order: '' })

function onSortChange({ prop, order }) {
  sortState.value = { prop: prop || '', order: order || '' }
}

const sortedItems = computed(() => {
  const data = flatItems.value
  const { prop, order } = sortState.value
  if (!prop || !order) return data
  return [...data].sort((a, b) => {
    let va, vb
    if (prop === '_customer') {
      va = (a._contract?.customer?.name || '').toLowerCase()
      vb = (b._contract?.customer?.name || '').toLowerCase()
    } else if (prop === '_spec') {
      va = (a.spec_description || '').toLowerCase()
      vb = (b.spec_description || '').toLowerCase()
    } else if (prop === '_contract_status') {
      va = (a._contract?.computed_status || a._contract?.status || '').toLowerCase()
      vb = (b._contract?.computed_status || b._contract?.status || '').toLowerCase()
    } else if (prop === 'contract_date') {
      va = a.contract_date || ''
      vb = b.contract_date || ''
    } else {
      va = a[prop]
      vb = b[prop]
    }
    if (va === vb) return 0
    if (va == null) return 1
    if (vb == null) return -1
    const cmp = typeof va === 'number' ? va - vb : String(va).localeCompare(String(vb))
    return order === 'ascending' ? cmp : -cmp
  })
})

const stepNameMap = computed(() => {
  const map = {}
  for (const s of processSteps.value) {
    map[s.step_code] = s.step_name
  }
  return map
})

const flatItems = computed(() => {
  const result = []
  for (const c of contracts.value) {
    const items = c.items || []
    if (items.length === 0) {
      result.push({ _contract: c, contract_no: c.contract_no, contract_date: c.contract_date, line_no: null, spec_description: null, packaging_type: null, qty: null, production_status: null })
    } else {
      for (const item of items) {
        result.push({ ...item, _contract: c, contract_no: c.contract_no, contract_date: c.contract_date })
      }
    }
  }
  return result
})

function stepLabel(code) {
  return stepNameMap.value[code] || code
}

function progressTagType(row) {
  if (row.production_status === 'completed') return 'success'
  return 'primary'
}

function statusType(s) {
  if (s === '草稿') return 'warning'
  if (s === '确认') return 'success'
  if (s === '已下发') return 'primary'
  if (s === '已取消') return 'danger'
  if (s === '已完成') return 'success'
  return 'info'
}

async function fetchData() {
  loading.value = true
  try {
    const res = await listContracts({ keyword: keyword.value, skip: (page.value - 1) * pageSize.value, limit: pageSize.value })
    contracts.value = res.data
    total.value = res.data.length
    // also fetch process steps for status labels
    if (processSteps.value.length === 0) {
      const sRes = await listProcessSteps()
      processSteps.value = sRes.data
    }
  } catch { /* 403 handled by interceptor */ }
  finally { loading.value = false }
}

function search() { page.value = 1; fetchData() }
function openCreate() { router.push('/contracts/new') }
function openEdit(row) { router.push(`/contracts/${row.id}/edit`) }
function viewDetail(row) { router.push(`/contracts/${row._contract?.id ?? row.id}`) }
async function handleDelete(row) {
  try {
    await deleteContract(row.id)
    ElMessage.success('已删除')
    fetchData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '删除失败') }
}

onMounted(fetchData)
</script>
