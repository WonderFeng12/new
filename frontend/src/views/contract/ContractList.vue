<template>
  <div>
    <h2>合同管理</h2>
    <el-card style="margin:16px 0">
      <el-row :gutter="16">
        <el-col :span="8">
          <el-input v-model="keyword" placeholder="搜索合同号" clearable @clear="search" @keyup.enter="search" />
        </el-col>
        <el-col :span="16" style="text-align:right">
          <el-button type="primary" @click="search">搜索</el-button>
          <el-button type="success" @click="openCreate">新建合同</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-table :data="contracts" v-loading="loading" stripe style="width:100%">
      <el-table-column prop="contract_no" label="合同号" width="150" />
      <el-table-column label="客户" width="120">
        <template #default="{ row }">{{ row.customer?.name }}</template>
      </el-table-column>
      <el-table-column prop="contract_date" label="日期" width="110" />
      <el-table-column label="规格" min-width="160">
        <template #default="{ row }">{{ row.spec_description || row.spec?.spec_description }}</template>
      </el-table-column>
      <el-table-column prop="total_amount" label="总金额" width="120" align="right">
        <template #default="{ row }">{{ row.total_amount?.toFixed(2) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
          <el-button size="small" type="primary" @click="openEdit(row)" :disabled="row.status==='已下发'">编辑</el-button>
          <el-popconfirm title="确认删除?" @confirm="handleDelete(row)">
            <template #reference>
              <el-button size="small" type="danger" :disabled="row.status==='已下发'">删除</el-button>
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listContracts, deleteContract } from '../../api/contract'

const router = useRouter()
const contracts = ref([])
const loading = ref(false)
const keyword = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

function statusType(s) {
  if (s === '草稿') return 'warning'
  if (s === '保存') return 'success'
  return 'info'
}

async function fetchData() {
  loading.value = true
  try {
    const res = await listContracts({ keyword: keyword.value, skip: (page.value - 1) * pageSize.value, limit: pageSize.value })
    contracts.value = res.data
    total.value = res.data.length
  } catch { /* 403 handled by interceptor */ }
  finally { loading.value = false }
}

function search() { page.value = 1; fetchData() }
function openCreate() { router.push('/contracts/new') }
function openEdit(row) { router.push(`/contracts/${row.id}/edit`) }
function viewDetail(row) { router.push(`/contracts/${row.id}`) }
async function handleDelete(row) {
  try {
    await deleteContract(row.id)
    ElMessage.success('已删除')
    fetchData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '删除失败') }
}

onMounted(fetchData)
</script>
