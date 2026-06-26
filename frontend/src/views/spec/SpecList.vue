<template>
  <div style="text-align:left">
    <h2>毛毯规格</h2>
    <el-card style="margin:16px 0">
      <el-row :gutter="16">
        <el-col :span="8">
          <el-input v-model="keyword" placeholder="搜索规格名称" clearable @clear="search" @keyup.enter="search" />
        </el-col>
        <el-col :span="16" style="text-align:right">
          <el-button type="primary" @click="search">搜索</el-button>
          <el-button type="success" @click="openCreate">新建毛毯规格</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-table :data="list" v-loading="loading" stripe @sort-change="onSortChange" ref="tableRef">
      <el-table-column prop="spec_name" label="规格名称" min-width="180" sortable="custom" />
      <el-table-column label="毛毯尺寸" min-width="120" sortable="custom" prop="length">
        <template #default="{ row }">{{ row.length }} × {{ row.width }}</template>
      </el-table-column>
      <el-table-column prop="weight" label="重量" width="100" sortable="custom" />
      <el-table-column prop="layer_type" label="层类型" width="100" sortable="custom" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" :disabled="row.is_in_use" @click="editRow(row)">编辑</el-button>
          <el-button size="small" @click="handleClone(row)">复制</el-button>
          <el-popconfirm title="确认删除?" @confirm="handleDelete(row)">
            <template #reference><el-button size="small" type="danger" :disabled="row.is_in_use">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showDialog" :title="editingId ? '编辑毛毯规格' : '新建毛毯规格'" width="520px" style="text-align:left">
      <el-form :model="form" label-width="120px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="毛毯尺寸长" required>
              <el-input v-model="form.length" placeholder="如 200" @input="validateNumeric('length')" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="毛毯尺寸宽" required>
              <el-input v-model="form.width" placeholder="如 240" @input="validateNumeric('width')" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="毛毯总量(KG)" required>
          <el-input v-model="form.weight" placeholder="如 4" @input="validateNumeric('weight')" />
        </el-form-item>
        <el-form-item label="层类型" required>
          <el-radio-group v-model="form.layer_type">
            <el-radio value="单层">单层</el-radio>
            <el-radio value="双层">双层</el-radio>
            <el-radio value="复合">复合</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="规格名称">
          <el-input :model-value="previewSpecName" disabled placeholder="自动生成" />
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
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listSpecs, createSpec, updateSpec, deleteSpec, cloneSpec } from '../../api/spec'

const list = ref([])
const loading = ref(false)
const keyword = ref('')
const showDialog = ref(false)
const editingId = ref(null)
const saving = ref(false)
const tableRef = ref(null)
const form = ref({ length: '', width: '', weight: '', layer_type: '单层' })

const previewSpecName = computed(() => {
  const f = form.value
  return f.length && f.width && f.weight ? `${f.length}*${f.width}/${f.weight}KG/${f.layer_type}` : ''
})

function validateNumeric(field) {
  form.value[field] = form.value[field].replace(/[^\d.]/g, '').replace(/(\..*)\./g, '$1')
}

async function fetchData() {
  loading.value = true
  try { const res = await listSpecs({ keyword: keyword.value }); list.value = res.data }
  catch {} finally { loading.value = false }
}
function search() { fetchData() }
function openCreate() { editingId.value = null; form.value = { length: '', width: '', weight: '', layer_type: '单层' }; showDialog.value = true }
function editRow(row) {
  editingId.value = row.id
  form.value = { ...row, weight: row.weight.replace(/KG/i, '') }
  showDialog.value = true
}

let sortOrder = {}
function onSortChange({ prop, order }) {
  if (!order || !prop) { sortOrder = {}; return }
  sortOrder = { prop, order }
  const sorted = [...list.value].sort((a, b) => {
    const va = a[prop] || '', vb = b[prop] || ''
    const cmp = va.localeCompare(vb, 'zh-CN')
    return order === 'ascending' ? cmp : -cmp
  })
  list.value = sorted
}

async function handleSave() {
  saving.value = true
  try {
    if (editingId.value) { await updateSpec(editingId.value, form.value); ElMessage.success('已更新') }
    else { await createSpec(form.value); ElMessage.success('已创建') }
    showDialog.value = false; editingId.value = null; fetchData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '保存失败') }
  finally { saving.value = false }
}
async function handleClone(row) {
  try { await cloneSpec(row.id); ElMessage.success('已复制'); fetchData() }
  catch (e) { ElMessage.error(e.response?.data?.detail || '复制失败') }
}
async function handleDelete(row) {
  try { await deleteSpec(row.id); ElMessage.success('已删除'); fetchData() }
  catch (e) { ElMessage.error(e.response?.data?.detail || '删除失败') }
}
onMounted(fetchData)
</script>
