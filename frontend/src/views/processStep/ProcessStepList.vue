<template>
  <div>
    <h2>工序管理</h2>
    <div style="margin:16px 0">
      <el-button type="primary" @click="openCreate">新建工序</el-button>
    </div>
    <el-table :data="steps" stripe size="small" v-loading="loading">
      <el-table-column prop="step_code" label="工序编码" width="120" />
      <el-table-column prop="step_name" label="工序名称" width="150" />
      <el-table-column prop="sort_order" label="排序" width="70" />
      <el-table-column label="负责人" min-width="200">
        <template #default="{ row }">
          <el-tag v-for="a in row.assignees" :key="a.id" size="small" style="margin:2px">{{ a.display_name }} ({{ a.role }})</el-tag>
          <span v-if="!row.assignees?.length" style="color:#999">未配置</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" @click="openAssign(row)">负责人</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="form.visible" :title="form.isEdit ? '编辑工序' : '新建工序'" width="450px">
      <el-form :model="form.data" label-width="100px">
        <el-form-item label="工序编码">
          <el-input v-model="form.data.step_code" :disabled="form.isEdit" />
        </el-form-item>
        <el-form-item label="工序名称">
          <el-input v-model="form.data.step_name" />
        </el-form-item>
        <el-form-item label="排序号">
          <el-input-number v-model="form.data.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.data.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="form.visible = false">取消</el-button>
        <el-button type="primary" @click="confirmSave" :loading="form.loading">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="assign.visible" title="配置工序负责人" width="500px">
      <div v-if="assign.step">
        <p style="margin-bottom:12px">工序：<el-tag>{{ assign.step.step_name }}</el-tag></p>
        <el-checkbox-group v-model="assign.selectedUserIds">
          <el-checkbox v-for="u in allUsers" :key="u.id" :label="u.id" style="display:flex;margin:6px 0">
            {{ u.display_name }} ({{ u.role }})
          </el-checkbox>
        </el-checkbox-group>
      </div>
      <template #footer>
        <el-button @click="assign.visible = false">取消</el-button>
        <el-button type="primary" @click="confirmAssign" :loading="assign.loading">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listProcessSteps, createProcessStep, updateProcessStep, deleteProcessStep, setStepAssignees } from '../../api/production'
import { listUsers } from '../../api/user'
import { ElMessage, ElMessageBox } from 'element-plus'

const steps = ref([])
const allUsers = ref([])
const loading = ref(false)

const form = ref({ visible: false, isEdit: false, data: { step_code: '', step_name: '', sort_order: 0, is_active: true }, loading: false })
const assign = ref({ visible: false, step: null, selectedUserIds: [], loading: false })

function openCreate() {
  form.value = { visible: true, isEdit: false, data: { step_code: '', step_name: '', sort_order: 0, is_active: true }, loading: false }
}

function openEdit(row) {
  form.value = { visible: true, isEdit: true, data: { ...row }, loading: false }
}

async function confirmSave() {
  form.value.loading = true
  try {
    if (form.value.isEdit) {
      await updateProcessStep(form.value.data.id, form.value.data)
      ElMessage.success('更新成功')
    } else {
      await createProcessStep(form.value.data)
      ElMessage.success('创建成功')
    }
    form.value.visible = false
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
  finally { form.value.loading = false }
}

function openAssign(row) {
  assign.value = {
    visible: true,
    step: row,
    selectedUserIds: row.assignees?.map(a => a.id) || [],
    loading: false,
  }
}

async function confirmAssign() {
  assign.value.loading = true
  try {
    await setStepAssignees(assign.value.step.id, { user_ids: assign.value.selectedUserIds })
    ElMessage.success('负责人已配置')
    assign.value.visible = false
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
  finally { assign.value.loading = false }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除工序「${row.step_name}」？`, '确认')
    await deleteProcessStep(row.id)
    ElMessage.success('已删除')
    loadData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

async function loadData() {
  loading.value = true
  try {
    const [sRes, uRes] = await Promise.all([
      listProcessSteps({ include_inactive: true }),
      listUsers(),
    ])
    steps.value = sRes.data
    allUsers.value = uRes.data
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

onMounted(loadData)
</script>
