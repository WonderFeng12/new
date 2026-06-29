<template>
  <div>
    <h2>合同详情</h2>
    <el-card v-loading="loading" style="margin:16px 0">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>合同号: {{ contract?.contract_no }}</span>
          <span>
            <el-tag :type="statusType(contract?.status)" size="small">{{ contract?.status }}</el-tag>
            <el-tag v-if="contract?.latest_confirm_version" size="small" type="info" style="margin-left:4px">V{{ contract?.latest_confirm_version }}</el-tag>
            <el-button size="small" style="margin-left:8px" @click="$router.push(`/contracts/${contract?.id}/edit`)" :disabled="contract?.status!=='草稿'">编辑</el-button>
            <el-button size="small" type="warning" @click="handleReopenEdit" :disabled="contract?.status=='草稿'" v-if="userRole === '销售经理' || userRole === '业务员'">重新编辑</el-button>
            <el-button size="small" type="warning" @click="handleRequestConfirm" :disabled="contract?.status!=='草稿'" v-if="userRole === '业务员' || userRole === '销售经理'">请求确认</el-button>
            <el-button size="small" type="danger" @click="manualConfirmDialogVisible = true" :disabled="contract?.status!=='草稿'" v-if="userRole === '销售经理'">确认</el-button>
          </span>
        </div>
      </template>

      <el-descriptions :column="3" border>
        <el-descriptions-item label="客户">{{ contract?.customer?.name }}</el-descriptions-item>
        <el-descriptions-item label="合同日期">{{ contract?.contract_date }}</el-descriptions-item>
        <el-descriptions-item label="交货日期">{{ contract?.delivery_date }}</el-descriptions-item>
      </el-descriptions>

      <el-divider>行项目</el-divider>
      <el-table :data="contract?.items || []" stripe size="small">
        <el-table-column type="expand" width="30">
          <template #default="{ row }">
            <div style="padding:8px 16px;font-size:13px">
              <div v-if="row.process_sheet_no" style="margin-bottom:4px">
                <strong>工艺单号：</strong>
                <el-link type="primary" @click="$router.push(`/process-sheets/${row.process_sheet_id}`)">{{ row.process_sheet_no }}</el-link>
                <el-tag :type="row.process_sheet_status==='已下发'?'success':'info'" size="small" style="margin-left:8px">{{ row.process_sheet_status }}</el-tag>
                <el-tag v-if="row.process_sheet_version > 0" size="small" style="margin-left:4px">V{{ row.process_sheet_version }}</el-tag>
                <el-tag v-if="(contract?.latest_confirm_version || 0) > (row.process_sheet_version || 0)" type="warning" size="small" style="margin-left:4px">合同已更新至V{{ contract?.latest_confirm_version }}，建议重新生成</el-tag>
              </div>
              <div v-if="row.yarn_plan_no" style="margin-bottom:4px">
                <strong>坯布计划单号：</strong>{{ row.yarn_plan_no }}
                <span v-if="row.yarn_plan_user_name" style="margin-left:12px;color:#666">负责人：{{ row.yarn_plan_user_name }}</span>
              </div>
              <div v-if="!row.yarn_plan_no && !row.process_sheet_no" style="color:#999">暂无关联单据</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="line_no" label="行号" width="60" fixed="left" />
        <el-table-column label="毛毯规格" min-width="160" fixed="left">
          <template #default="{ row }">
            {{ row.spec_description || `规格#${row.spec_id}` }}
          </template>
        </el-table-column>
        <el-table-column label="包装方式" width="100">
          <template #default="{ row }">{{ row.packaging_type || '—' }}</template>
        </el-table-column>
        <el-table-column label="压花" width="55">
          <template #default="{ row }">{{ row.is_pressed ? '是' : '否' }}</template>
        </el-table-column>
        <el-table-column label="交货日期" width="110">
          <template #default="{ row }">{{ row.delivery_date || '—' }}</template>
        </el-table-column>
        <el-table-column prop="qty" label="数量(条)" width="75" />
        <el-table-column prop="remark" label="备注" min-width="120" />
        <el-table-column label="生产进度" min-width="160">
          <template #default="{ row }">
            <template v-if="row.production_status">
              <div v-if="row.production_status === 'cancelled'" style="display:flex;align-items:center">
                <el-progress :percentage="100" :stroke-width="16" status="exception" style="flex:1" />
                <span style="margin-left:6px;color:#f56c6c;white-space:nowrap">已取消</span>
              </div>
              <div v-else style="display:flex;align-items:center">
                <el-progress :percentage="progressPercent(row)" :stroke-width="16" style="flex:1" />
                <span style="margin-left:6px;white-space:nowrap">{{ statusLabel(row.production_status) }}</span>
              </div>
            </template>
            <span v-else style="color:#999">待坯布计划</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="440">
          <template #default="{ row }">
            <el-button size="small" v-if="canReleaseYarn(row)" @click="openYarnDialog(row)">下达坯布</el-button>
            <el-button size="small" type="primary" v-if="canAdvance(row)" @click="openAdvanceDialog(row)">推进</el-button>
            <el-button size="small" v-if="canRollback(row)" @click="openRollbackDialog(row)">回退</el-button>
            <el-button size="small" @click="openLogDialog(row)">日志</el-button>
            <el-button size="small" type="primary" v-if="canPushDown(row)" @click="handlePushDownItem(row)">下推工艺单</el-button>
            <el-button size="small" type="danger" v-if="canCancel(row)" @click="openCancelDialog(row)">取消</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-divider>状态日志</el-divider>
      <el-table :data="contractLogs" stripe size="small" v-if="contractLogs.length">
        <el-table-column prop="created_at" label="时间" width="160" />
        <el-table-column prop="operation_type" label="操作" width="100" />
        <el-table-column prop="contract_item_id" label="行号" width="60" />
        <el-table-column prop="from_status" label="从" width="100" />
        <el-table-column prop="to_status" label="到" width="100" />
        <el-table-column prop="operator_name" label="操作人" width="100" />
        <el-table-column prop="remark" label="备注" min-width="150" />
      </el-table>
      <div v-else style="color:#999;text-align:center;padding:16px">暂无日志</div>
    </el-card>

    <!-- 推进 dialog -->
    <el-dialog v-model="advanceDialogVisible" title="推进生产" width="400px">
      <span>确认将当前行项目推进到下一步？</span>
      <template #footer>
        <el-button @click="advanceDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogLoading" @click="confirmAdvance">确认</el-button>
      </template>
    </el-dialog>

    <!-- 回退 dialog -->
    <el-dialog v-model="rollbackDialogVisible" title="回退生产" width="400px">
      <span>确认将当前行项目回退到上一步？</span>
      <template #footer>
        <el-button @click="rollbackDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogLoading" @click="confirmRollback">确认</el-button>
      </template>
    </el-dialog>

    <!-- 确认 dialog -->
    <el-dialog v-model="manualConfirmDialogVisible" title="确认合同" width="420px">
      <el-form>
        <el-form-item label="合同号">{{ contract?.contract_no }}</el-form-item>
        <el-form-item label="确认意见" required>
          <el-input v-model="manualConfirmRemark" type="textarea" :rows="3" placeholder="请填写确认意见（必填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="manualConfirmDialogVisible = false; manualConfirmRemark = ''">取消</el-button>
        <el-button type="danger" :loading="dialogLoading" @click="handleManualConfirm">确认</el-button>
      </template>
    </el-dialog>

    <!-- 取消 dialog -->
    <el-dialog v-model="cancelDialogVisible" title="取消行项目" width="420px">
      <el-form>
        <el-form-item label="取消原因">
          <el-input v-model="cancelReason" type="textarea" :rows="2" placeholder="请输入取消原因" />
        </el-form-item>
        <el-form-item label="取消数量">
          <el-input-number v-model="cancelQty" :min="1" :max="currentItem?.qty || 1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cancelDialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="dialogLoading" @click="confirmCancel">确认取消</el-button>
      </template>
    </el-dialog>

    <!-- 坯布下达 dialog -->
    <el-dialog v-model="yarnDialogVisible" title="下达坯布计划" width="400px">
      <el-form>
        <el-form-item label="计划员">
          <el-select v-model="selectedUserId" placeholder="选择计划员" filterable style="width:100%">
            <el-option v-for="u in users" :key="u.id" :label="u.display_name" :value="u.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="yarnDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogLoading" @click="confirmYarn">确认下达</el-button>
      </template>
    </el-dialog>

    <!-- 下推工艺单 dialog -->
    <el-dialog v-model="pushDownDialogVisible" title="下推工艺单" width="500px">
      <el-form label-width="90px">
        <el-form-item label="毛毯规格">
          <span>{{ pushDownTarget?.spec_description || `规格#${pushDownTarget?.spec_id}` }}</span>
        </el-form-item>
        <el-form-item label="工艺备注">
          <el-input v-model="pushDownProcessRemark" type="textarea" :rows="4" placeholder="请填写工艺要求、注意事项等" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pushDownDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogLoading" @click="confirmPushDown">确认下推</el-button>
      </template>
    </el-dialog>

    <!-- 日志 dialog -->
    <el-dialog v-model="logDialogVisible" title="状态日志" width="700px">
      <el-table :data="dialogLogs" stripe size="small" v-loading="dialogLoading">
        <el-table-column prop="created_at" label="时间" width="160" />
        <el-table-column prop="operation_type" label="操作" width="100" />
        <el-table-column prop="from_status" label="从" width="100" />
        <el-table-column prop="to_status" label="到" width="100" />
        <el-table-column prop="operator_name" label="操作人" width="100" />
        <el-table-column prop="remark" label="备注" min-width="150" />
      </el-table>
      <template #footer>
        <el-button @click="logDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getContract, manualConfirm, requestConfirm, reopenEdit } from '../../api/contract'
import { listProcessSteps, advanceItem, rollbackItem, cancelItem, releaseYarnPlan, getItemLogs, getContractLogs, pushDownItem } from '../../api/production'
import { listUsers } from '../../api/user'

const route = useRoute()
const router = useRouter()

const contract = ref(null)
const loading = ref(false)
const processSteps = ref([])
const users = ref([])
const contractLogs = ref([])

// Dialog state
const advanceDialogVisible = ref(false)
const rollbackDialogVisible = ref(false)
const cancelDialogVisible = ref(false)
const yarnDialogVisible = ref(false)
const logDialogVisible = ref(false)
const currentItem = ref(null)
const cancelQty = ref(0)
const cancelReason = ref('')
const selectedUserId = ref(null)
const dialogLogs = ref([])
const dialogLoading = ref(false)

const manualConfirmDialogVisible = ref(false)
const manualConfirmRemark = ref('')

const pushDownDialogVisible = ref(false)
const pushDownTarget = ref(null)
const pushDownProcessRemark = ref('')

const userRole = computed(() => {
  try {
    const token = localStorage.getItem('token')
    if (!token) return ''
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.role
  } catch { return '' }
})

const currentUserId = computed(() => {
  try {
    const token = localStorage.getItem('token')
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.sub
  } catch { return null }
})

const progressSummary = computed(() => {
  const items = contract.value?.items || []
  const total = items.length
  const released = items.filter(i => i.production_status).length
  const completed = items.filter(i => i.production_status === 'completed').length
  const cancelled = items.filter(i => i.production_status === 'cancelled').length
  return `已下${released}/${total}行 | 完成${completed}行 | 取消${cancelled}行`
})

const stepNameMap = computed(() => {
  const map = {}
  for (const step of processSteps.value) {
    map[step.step_code] = step.step_name
  }
  return map
})

function statusType(s) {
  if (s === '草稿') return 'warning'
  if (s === '确认') return 'success'
  if (s === '已下发') return 'primary'
  return 'info'
}

function progressPercent(row) {
  if (!row.production_status || row.production_status === 'cancelled') return 100
  const steps = processSteps.value
  if (!steps.length) return 0
  const idx = steps.findIndex(s => s.step_code === row.production_status)
  if (idx === -1) return 0
  return Math.round(((idx + 1) / steps.length) * 100)
}

function statusLabel(code) {
  return stepNameMap.value[code] || code
}

function canReleaseYarn(row) {
  const role = userRole.value
  if (contract.value?.status === '草稿') return false
  return (role === '销售经理' || role === '生产专员') && !row.production_status
}

function canAdvance(row) {
  if (!row.production_status) return false
  if (row.production_status === 'cancelled' || row.production_status === 'completed') return false
  const role = userRole.value
  if (role === '销售经理' || role === '生产专员') return true
  // 外协人员只能推进织造工序
  if (role === '外协人员' && row.production_status === 'weaving') return true
  return false
}

function canRollback(row) {
  const role = userRole.value
  return (role === '销售经理' || role === '生产专员') && row.production_status && row.production_status !== 'cancelled'
}

function canCancel(row) {
  const role = userRole.value
  return (role === '销售经理' || role === '生产专员' || role === '业务员') && row.production_status !== 'cancelled'
}

function canPushDown(row) {
  const role = userRole.value
  if (role !== '销售经理' && role !== '生产专员') return false
  if (contract.value?.status !== '确认' && contract.value?.status !== '已下发') return false
  return !row.has_process_sheet
}

async function handleRequestConfirm() {
  try {
    await requestConfirm(route.params.id)
    ElMessage.success('已发送确认请求到企业微信群')
  } catch (e) { ElMessage.error(e.response?.data?.detail || '发送失败') }
}

async function handleReopenEdit() {
  try {
    await reopenEdit(route.params.id)
    ElMessage.success('已记录重新编辑操作，即将跳转编辑页面')
    router.push(`/contracts/${contract.value?.id}/edit`)
  } catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
}

function handlePushDownItem(row) {
  pushDownTarget.value = row
  pushDownProcessRemark.value = ''
  pushDownDialogVisible.value = true
}

async function confirmPushDown() {
  dialogLoading.value = true
  try {
    const res = await pushDownItem(pushDownTarget.value.id, { process_remark: pushDownProcessRemark.value })
    ElMessage.success('工艺单已下推')
    pushDownDialogVisible.value = false
    const sheetId = res.data?.sheet_id
    if (sheetId) {
      router.push(`/process-sheets/${sheetId}`)
    } else {
      loadData()
    }
  } catch (e) { ElMessage.error(e.response?.data?.detail || '下推失败') }
  finally { dialogLoading.value = false }
}

// --- Dialogs ---

function openAdvanceDialog(row) {
  currentItem.value = row
  advanceDialogVisible.value = true
}

async function confirmAdvance() {
  dialogLoading.value = true
  try {
    await advanceItem(currentItem.value.id, {})
    ElMessage.success('推进成功')
    advanceDialogVisible.value = false
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '推进失败') }
  finally { dialogLoading.value = false }
}

function openRollbackDialog(row) {
  currentItem.value = row
  rollbackDialogVisible.value = true
}

async function confirmRollback() {
  dialogLoading.value = true
  try {
    await rollbackItem(currentItem.value.id, {})
    ElMessage.success('回退成功')
    rollbackDialogVisible.value = false
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '回退失败') }
  finally { dialogLoading.value = false }
}

function openCancelDialog(row) {
  currentItem.value = row
  cancelReason.value = ''
  cancelQty.value = row.qty || 0
  cancelDialogVisible.value = true
}

async function confirmCancel() {
  dialogLoading.value = true
  try {
    await cancelItem(currentItem.value.id, { reason: cancelReason.value || '无', quantities: { total: cancelQty.value } })
    ElMessage.success('已取消')
    cancelDialogVisible.value = false
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '取消失败') }
  finally { dialogLoading.value = false }
}

function openYarnDialog(row) {
  currentItem.value = row
  selectedUserId.value = null
  yarnDialogVisible.value = true
}

async function confirmYarn() {
  if (!selectedUserId.value) {
    ElMessage.warning('请选择计划员')
    return
  }
  dialogLoading.value = true
  try {
    await releaseYarnPlan(currentItem.value.id, { yarn_plan_user_id: selectedUserId.value })
    ElMessage.success('坯布计划已下达')
    yarnDialogVisible.value = false
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '下达失败') }
  finally { dialogLoading.value = false }
}

async function openLogDialog(row) {
  currentItem.value = row
  logDialogVisible.value = true
  dialogLoading.value = true
  dialogLogs.value = []
  try {
    const res = await getItemLogs(row.id)
    dialogLogs.value = res.data
  } catch (e) { ElMessage.error(e.response?.data?.detail || '加载日志失败') }
  finally { dialogLoading.value = false }
}

async function handleManualConfirm() {
  if (!manualConfirmRemark.value?.trim()) {
    ElMessage.warning('请填写确认意见')
    return
  }
  dialogLoading.value = true
  try {
    await manualConfirm(route.params.id, { remark: manualConfirmRemark.value.trim() })
    ElMessage.success('合同已手动确认')
    manualConfirmDialogVisible.value = false
    manualConfirmRemark.value = ''
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
  finally { dialogLoading.value = false }
}


async function loadData() {
  loading.value = true
  try {
    const [cRes, sRes, uRes, lRes] = await Promise.all([
      getContract(route.params.id),
      listProcessSteps(),
      listUsers(),
      getContractLogs(route.params.id),
    ])
    contract.value = cRes.data
    processSteps.value = sRes.data
    users.value = uRes.data
    contractLogs.value = lRes.data
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

onMounted(loadData)
</script>
