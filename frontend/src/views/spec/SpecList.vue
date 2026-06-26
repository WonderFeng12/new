<template>
  <div>
    <h2>规格管理</h2>
    <el-card style="margin:16px 0">
      <el-row :gutter="16">
        <el-col :span="8">
          <el-input v-model="keyword" placeholder="搜索规格名称" clearable @clear="search" @keyup.enter="search" />
        </el-col>
        <el-col :span="16" style="text-align:right">
          <el-button type="primary" @click="search">搜索</el-button>
          <el-button type="success" @click="openCreate">新建规格</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-table :data="list" v-loading="loading" stripe>
      <el-table-column prop="spec_name" label="规格名称" width="150" />
      <el-table-column prop="weight" label="重量" width="100" />
      <el-table-column prop="layer_type" label="层类型" width="100" />
      <el-table-column prop="splice_method" label="拼接方式" width="150" />
      <el-table-column prop="spec_description" label="规格描述" min-width="250" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button size="small" @click="editRow(row)">编辑</el-button>
          <el-popconfirm title="确认删除?" @confirm="handleDelete(row)">
            <template #reference><el-button size="small" type="danger">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showDialog" :title="editingId ? '编辑规格' : '新建规格'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="规格名称" required>
          <el-input v-model="form.spec_name" />
        </el-form-item>
        <el-form-item label="毛毯重量" required>
          <el-input v-model="form.weight" placeholder="如 500g" />
        </el-form-item>
        <el-form-item label="层类型" required>
          <el-radio-group v-model="form.layer_type">
            <el-radio value="单层">单层</el-radio>
            <el-radio value="双层">双层</el-radio>
            <el-radio value="复合">复合</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="拼接方式">
          <el-input v-model="form.splice_method" placeholder="如 对拼接" />
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
import { ElMessage } from 'element-plus'
import { listSpecs, createSpec, updateSpec, deleteSpec } from '../../api/spec'

const list = ref([])
const loading = ref(false)
const keyword = ref('')
const showDialog = ref(false)
const editingId = ref(null)
const saving = ref(false)
const form = ref({ spec_name: '', weight: '', layer_type: '单层', splice_method: '' })

async function fetchData() {
  loading.value = true
  try { const res = await listSpecs({ keyword: keyword.value }); list.value = res.data }
  catch {} finally { loading.value = false }
}
function search() { fetchData() }
function editRow(row) { editingId.value = row.id; form.value = { ...row }; showDialog.value = true }
async function handleSave() {
  saving.value = true
  try {
    if (editingId.value) { await updateSpec(editingId.value, form.value); ElMessage.success('已更新') }
    else { await createSpec(form.value); ElMessage.success('已创建') }
    showDialog.value = false; editingId.value = null; fetchData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '保存失败') }
  finally { saving.value = false }
}
async function handleDelete(row) {
  try { await deleteSpec(row.id); ElMessage.success('已删除'); fetchData() }
  catch (e) { ElMessage.error(e.response?.data?.detail || '删除失败') }
}
onMounted(fetchData)
</script>
