<template>
  <div>
    <h2>客户管理</h2>
    <el-card style="margin:16px 0">
      <el-row :gutter="16">
        <el-col :span="8">
          <el-input v-model="keyword" placeholder="搜索客户名称" clearable @clear="search" @keyup.enter="search" />
        </el-col>
        <el-col :span="16" style="text-align:right">
          <el-button type="primary" @click="search">搜索</el-button>
          <el-button type="success" @click="showDialog = true; form={}">新建客户</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-table :data="list" v-loading="loading" stripe>
      <el-table-column prop="customer_no" label="客户编号" width="120" />
      <el-table-column prop="name" label="客户名称" min-width="160" />
      <el-table-column prop="contact" label="联系人" width="120" />
      <el-table-column prop="phone" label="电话" width="130" />
      <el-table-column prop="address" label="地址" min-width="200" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button size="small" @click="editRow(row)">编辑</el-button>
          <el-popconfirm title="确认删除?" @confirm="handleDelete(row)">
            <template #reference><el-button size="small" type="danger">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showDialog" :title="editingId ? '编辑客户' : '新建客户'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="form.address" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listCustomers, createCustomer, updateCustomer, deleteCustomer } from '../../api/customer'

const list = ref([])
const loading = ref(false)
const keyword = ref('')
const showDialog = ref(false)
const editingId = ref(null)
const saving = ref(false)
const form = ref({ name: '', contact: '', phone: '', address: '' })

async function fetchData() {
  loading.value = true
  try { const res = await listCustomers({ keyword: keyword.value }); list.value = res.data }
  catch {} finally { loading.value = false }
}
function search() { fetchData() }
function editRow(row) { editingId.value = row.id; form.value = { ...row }; showDialog.value = true }
async function handleSave() {
  saving.value = true
  try {
    if (editingId.value) { await updateCustomer(editingId.value, form.value); ElMessage.success('已更新') }
    else { await createCustomer(form.value); ElMessage.success('已创建') }
    showDialog.value = false; editingId.value = null; fetchData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '保存失败') }
  finally { saving.value = false }
}
async function handleDelete(row) {
  try { await deleteCustomer(row.id); ElMessage.success('已删除'); fetchData() }
  catch (e) { ElMessage.error(e.response?.data?.detail || '删除失败') }
}
onMounted(fetchData)
</script>
