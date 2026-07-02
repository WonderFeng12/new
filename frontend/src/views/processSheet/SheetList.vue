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
        </el-col>
      </el-row>
    </el-card>

    <el-table :data="sortedSheets" v-loading="loading" stripe style="width:100%" @row-click="viewDetail" @sort-change="onSortChange">
      <el-table-column prop="sheet_no" label="工艺单号" width="150" sortable="custom" />
      <el-table-column label="合同号" width="150" sortable="custom" prop="_contract_no">
        <template #default="{ row }">{{ row.contract?.contract_no }}</template>
      </el-table-column>
      <el-table-column label="毛毯规格" min-width="200" sortable="custom" prop="_spec">
        <template #default="{ row }">
          {{ specSummary(row) }}
        </template>
      </el-table-column>
      <el-table-column label="数量" width="80" sortable="custom" prop="_qty">
        <template #default="{ row }">
          {{ totalQty(row) }}
        </template>
      </el-table-column>
      <el-table-column label="交期" width="100" sortable="custom" prop="_delivery">
        <template #default="{ row }">
          {{ firstDelivery(row) }}
        </template>
      </el-table-column>
      <el-table-column label="版本" width="70" sortable="custom" prop="confirm_version_no">
        <template #default="{ row }">V{{ row.confirm_version_no }}</template>
      </el-table-column>
      <el-table-column label="状态" width="70" sortable="custom" prop="status">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_by" label="创建人" width="80" sortable="custom" />
      <el-table-column prop="created_at" label="创建时间" width="155" sortable="custom" />
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listSheets, confirmSheet, dispatchSheet, deleteSheet } from '../../api/processSheet'

const router = useRouter()
const sheets = ref([])
const loading = ref(false)
const keyword = ref('')
const sortState = ref({ prop: '', order: '' })

function onSortChange({ prop, order }) {
  sortState.value = { prop: prop || '', order: order || '' }
}

const sortedSheets = computed(() => {
  const data = sheets.value
  const { prop, order } = sortState.value
  if (!prop || !order) return data
  return [...data].sort((a, b) => {
    let va, vb
    if (prop === '_contract_no') {
      va = (a.contract?.contract_no || '').toLowerCase()
      vb = (b.contract?.contract_no || '').toLowerCase()
    } else if (prop === '_spec') {
      va = specSummary(a).toLowerCase()
      vb = specSummary(b).toLowerCase()
    } else if (prop === '_qty') {
      va = totalQty(a); vb = totalQty(b)
    } else if (prop === '_delivery') {
      va = firstDelivery(a) || ''; vb = firstDelivery(b) || ''
    } else {
      va = a[prop]; vb = b[prop]
    }
    if (va === vb) return 0
    if (va == null) return 1
    if (vb == null) return -1
    const cmp = typeof va === 'number' ? va - vb : String(va).localeCompare(String(vb))
    return order === 'ascending' ? cmp : -cmp
  })
})

function specSummary(row) {
  const items = row.items || []
  if (!items.length) return ''
  const names = items.map(i => i.spec?.spec_description || i.spec?.spec_name || '').filter(Boolean)
  return names.join('; ')
}

function totalQty(row) {
  const items = row.items || []
  return items.reduce((s, i) => s + parseFloat(i.qty || 0), 0)
}

function firstDelivery(row) {
  const items = row.items || []
  return items[0]?.delivery_date || ''
}

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

onMounted(fetchData)
</script>
