<template>
  <div>
    <h2>基础数据维护</h2>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="工序管理" name="process_steps">
        <div style="margin-bottom:10px">
          <el-button type="primary" size="small" @click="openStepCreate">新建工序</el-button>
        </div>
        <el-table :data="processSteps" stripe v-loading="stepLoading" max-height="600">
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
          <el-table-column label="操作" width="210" fixed="right">
            <template #default="{ row }">
              <div style="display:flex;gap:4px;flex-wrap:nowrap">
                <el-button size="small" text type="primary" @click="openStepEdit(row)">编辑</el-button>
                <el-button size="small" text type="primary" @click="openStepAssign(row)">负责人</el-button>
                <el-button size="small" text type="danger" @click="handleStepDelete(row)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <!-- 工序编辑 dialog -->
        <el-dialog v-model="stepForm.visible" :title="stepForm.isEdit ? '编辑工序' : '新建工序'" width="450px">
          <el-form :model="stepForm.data" label-width="100px">
            <el-form-item label="工序编码">
              <el-input v-model="stepForm.data.step_code" :disabled="stepForm.isEdit" />
            </el-form-item>
            <el-form-item label="工序名称">
              <el-input v-model="stepForm.data.step_name" />
            </el-form-item>
            <el-form-item label="排序号">
              <el-input-number v-model="stepForm.data.sort_order" :min="0" />
            </el-form-item>
            <el-form-item label="状态">
              <el-switch v-model="stepForm.data.is_active" active-text="启用" inactive-text="禁用" />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="stepForm.visible = false">取消</el-button>
            <el-button type="primary" @click="confirmStepSave" :loading="stepForm.loading">保存</el-button>
          </template>
        </el-dialog>

        <!-- 工序负责人 dialog -->
        <el-dialog v-model="stepAssign.visible" title="配置工序负责人" width="500px">
          <div v-if="stepAssign.step">
            <p style="margin-bottom:12px">工序：<el-tag>{{ stepAssign.step.step_name }}</el-tag></p>
            <el-checkbox-group v-model="stepAssign.selectedUserIds">
              <el-checkbox v-for="u in allUsers" :key="u.id" :label="u.id" style="display:flex;margin:6px 0">
                {{ u.display_name }} ({{ u.role }})
              </el-checkbox>
            </el-checkbox-group>
          </div>
          <template #footer>
            <el-button @click="stepAssign.visible = false">取消</el-button>
            <el-button type="primary" @click="confirmStepAssign" :loading="stepAssign.loading">保存</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>

      <el-tab-pane label="颜色映射" name="color">
        <div style="margin-bottom:10px">
          <el-button type="primary" size="small" @click="openAdd">添加颜色</el-button>
        </div>
        <el-table :data="colorMappingData" stripe max-height="600">
          <el-table-column label="颜色名称" width="200" sortable prop="code" />
          <el-table-column label="包边色号" width="200" sortable prop="value" />
          <el-table-column label="操作" width="130">
            <template #default="{ row }">
              <el-button size="small" type="primary" text @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" text @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="包装方式" name="packing">
        <div style="margin-bottom:10px">
          <el-button type="primary" size="small" @click="openAdd">添加包装方式</el-button>
        </div>
        <el-table :data="packagingData" stripe max-height="600">
          <el-table-column label="名称" width="200" sortable prop="code" />
          <el-table-column label="操作" width="130">
            <template #default="{ row }">
              <el-button size="small" type="primary" text @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" text @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="层类型" name="layer_type">
        <div style="margin-bottom:10px">
          <el-button type="primary" size="small" @click="openAdd">添加层类型</el-button>
        </div>
        <el-table :data="layerTypeData" stripe max-height="600">
          <el-table-column label="名称" width="200" sortable prop="code" />
          <el-table-column label="操作" width="130">
            <template #default="{ row }">
              <el-button size="small" type="primary" text @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" text @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="编码规则" name="code_rules">
        <div style="margin-bottom:10px">
          <el-button type="primary" size="small" @click="openAdd">添加编码规则</el-button>
        </div>
        <el-table :data="codeRulesData" stripe max-height="600">
          <el-table-column label="前缀" width="150" sortable prop="code" />
          <el-table-column label="后缀" width="150">
            <template #default="{ row }">{{ parseCodeRuleValue(row.value).suffix }}</template>
          </el-table-column>
          <el-table-column label="客户" width="auto">
            <template #default="{ row }">
              {{ customerList.find(c => c.id === parseCodeRuleValue(row.value).customer_id)?.name || '—' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="130">
            <template #default="{ row }">
              <el-button size="small" type="primary" text @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" text @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="其他" name="other">
        <el-empty description="其他基础数据，待扩展" :image-size="60" />
      </el-tab-pane>
    </el-tabs>

    <!-- Add/Edit Dialog -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="450px">
      <el-form :model="form" label-width="100px">
        <el-form-item :label="editLabel" required>
          <el-input v-model="form.code" />
        </el-form-item>
        <template v-if="activeTab === 'code_rules'">
          <el-form-item label="后缀">
            <el-input v-model="form.suffix" placeholder="可选" />
          </el-form-item>
          <el-form-item label="客户" required>
            <el-select v-model="form.customer_id" filterable style="width:100%" placeholder="选择客户">
              <el-option v-for="c in customerList" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
          </el-form-item>
        </template>
        <el-form-item label="包边色号" v-if="activeTab === 'color'">
          <el-input v-model="form.value" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listBasicData, createBasicData, updateBasicData, deleteBasicData } from '../../api/basicData'
import { listCustomers } from '../../api/customer'
import { listProcessSteps, createProcessStep, updateProcessStep, deleteProcessStep, setStepAssignees } from '../../api/production'
import { listUsers } from '../../api/user'

const activeTab = ref('process_steps')
const colorMappingData = ref([])
const packagingData = ref([])
const layerTypeData = ref([])
const codeRulesData = ref([])
const customerList = ref([])

function parseCodeRuleValue(val) {
  if (!val) return { suffix: '', customer_id: null }
  try { return JSON.parse(val) } catch { return { suffix: val, customer_id: null } }
}

const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref(null)
const form = ref({ code: '', value: '', suffix: '', customer_id: null })

const tabLabel = computed(() => {
  if (activeTab.value === 'color') return '颜色'
  if (activeTab.value === 'packing') return '包装方式'
  if (activeTab.value === 'layer_type') return '层类型'
  if (activeTab.value === 'code_rules') return '编码规则'
  return ''
})
const editLabel = computed(() => {
  if (activeTab.value === 'color') return '颜色名称'
  if (activeTab.value === 'code_rules') return '前缀'
  return '名称'
})
const dialogTitle = computed(() => (editingId.value ? '编辑' : '添加') + tabLabel.value)

// ── Process Steps ──
const processSteps = ref([])
const allUsers = ref([])
const stepLoading = ref(false)
const stepForm = ref({ visible: false, isEdit: false, data: { step_code: '', step_name: '', sort_order: 0, is_active: true }, loading: false })
const stepAssign = ref({ visible: false, step: null, selectedUserIds: [], loading: false })

function openStepCreate() {
  stepForm.value = { visible: true, isEdit: false, data: { step_code: '', step_name: '', sort_order: 0, is_active: true }, loading: false }
}

function openStepEdit(row) {
  stepForm.value = { visible: true, isEdit: true, data: { ...row }, loading: false }
}

async function confirmStepSave() {
  stepForm.value.loading = true
  try {
    if (stepForm.value.isEdit) {
      await updateProcessStep(stepForm.value.data.id, stepForm.value.data)
      ElMessage.success('更新成功')
    } else {
      await createProcessStep(stepForm.value.data)
      ElMessage.success('创建成功')
    }
    stepForm.value.visible = false
    loadStepData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
  finally { stepForm.value.loading = false }
}

function openStepAssign(row) {
  stepAssign.value = {
    visible: true,
    step: row,
    selectedUserIds: row.assignees?.map(a => a.id) || [],
    loading: false,
  }
}

async function confirmStepAssign() {
  stepAssign.value.loading = true
  try {
    await setStepAssignees(stepAssign.value.step.id, { user_ids: stepAssign.value.selectedUserIds })
    ElMessage.success('负责人已配置')
    stepAssign.value.visible = false
    loadStepData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
  finally { stepAssign.value.loading = false }
}

async function handleStepDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除工序「${row.step_name}」？`, '确认')
    await deleteProcessStep(row.id)
    ElMessage.success('已删除')
    loadStepData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

async function loadStepData() {
  stepLoading.value = true
  try {
    const [sRes, uRes] = await Promise.all([
      listProcessSteps({ include_inactive: true }),
      listUsers(),
    ])
    processSteps.value = sRes.data
    allUsers.value = uRes.data
  } catch { ElMessage.error('加载工序数据失败') }
  finally { stepLoading.value = false }
}

async function loadData() {
  try {
    const [cRes, pRes, lRes, crRes, custRes] = await Promise.all([
      listBasicData('color'),
      listBasicData('packing'),
      listBasicData('layer_type'),
      listBasicData('code_rules'),
      listCustomers(),
    ])
    colorMappingData.value = cRes.data || []
    packagingData.value = pRes.data || []
    layerTypeData.value = lRes.data || []
    codeRulesData.value = crRes.data || []
    customerList.value = custRes.data || []
  } catch (e) {
    console.error('loadData error:', e.response?.status, e.response?.data, e.message)
    ElMessage.error('加载基础数据失败')
  }
}

function openAdd() {
  editingId.value = null
  form.value = { code: '', value: '', suffix: '', customer_id: null }
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  const parsed = parseCodeRuleValue(row.value)
  form.value = {
    code: row.code,
    value: row.value || '',
    suffix: parsed.suffix,
    customer_id: parsed.customer_id,
  }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.value.code) { ElMessage.warning('请填写名称'); return }
  saving.value = true
  try {
    let payload
    if (activeTab.value === 'code_rules') {
      if (!form.value.customer_id) { ElMessage.warning('请选择客户'); return }
      payload = {
        code: form.value.code,
        value: JSON.stringify({ suffix: form.value.suffix || '', customer_id: form.value.customer_id }),
      }
    } else {
      payload = { ...form.value }
    }
    if (editingId.value) {
      await updateBasicData(activeTab.value, editingId.value, payload)
      ElMessage.success('已更新')
    } else {
      await createBasicData(activeTab.value, payload)
      ElMessage.success('已添加')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {
    console.error('Save error:', e.response?.status, e.response?.data, e.message)
    const detail = e.response?.data?.detail
    ElMessage.error(typeof detail === 'string' ? detail : JSON.stringify(detail) || '操作失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定删除?', '提示')
    await deleteBasicData(activeTab.value, row.id)
    ElMessage.success('已删除')
    loadData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(() => {
  loadData()
  loadStepData()
})
</script>
