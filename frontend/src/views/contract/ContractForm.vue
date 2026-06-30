<template>
  <div>
    <h2>{{ isEdit ? (contractStatus !== '草稿' ? '重新编辑合同' : '编辑合同') : '新建合同' }}</h2>
    <el-card style="margin:16px 0;max-width:1400px">
      <el-form :model="form" label-width="120px" v-loading="loading">
        <el-tabs type="border-card">
          <el-tab-pane label="基本信息">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="客户" required>
                  <el-select v-model="form.customer_id" filterable style="width:100%">
                    <el-option v-for="c in customers" :key="c.id" :label="c.name" :value="c.id" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="合同编号">
                  <el-input v-model="form.contract_no" placeholder="选择客户后自动生成，也可手动输入" @input="(val) => form.contract_no = val.toUpperCase()" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="合同日期">
                  <el-date-picker v-model="form.contract_date" style="width:100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="交货日期">
                  <el-date-picker v-model="form.delivery_date" style="width:100%" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-tab-pane>

          <el-tab-pane label="行项目">
            <el-button type="primary" size="small" @click="addItem" style="margin-bottom:8px">添加行项目</el-button>
            <el-table :data="form.items" stripe style="margin-top:8px" max-height="500">
              <el-table-column label="行号" width="55">
                <template #default="{ $index }">{{ $index + 1 }}</template>
              </el-table-column>
              <el-table-column label="毛毯规格" width="230">
                <template #default="{ row }">
                  <div style="display:flex;gap:2px;align-items:center">
                    <el-select v-model="row.spec_id" filterable style="flex:1;min-width:0" size="small" placeholder="选择规格">
                      <el-option v-for="s in specs" :key="s.id" :label="s.spec_description" :value="s.id" />
                    </el-select>
                    <el-button size="small" type="primary" text @click.stop="openSpecDialog(row)" style="padding:2px 4px;font-size:16px">＋</el-button>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="包装方式" width="130">
                <template #default="{ row }">
                  <el-select v-model="row.packaging_type" size="small" placeholder="选择" style="width:100%" clearable>
                    <el-option v-for="pt in packagingTypes" :key="pt.code" :label="pt.code" :value="pt.code" />
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column label="压花" width="70" align="center">
                <template #default="{ row }">
                  <el-checkbox v-model="row.is_pressed" />
                </template>
              </el-table-column>
              <el-table-column label="交货日期" width="140">
                <template #default="{ row }">
                  <el-date-picker v-model="row.delivery_date" style="width:100%" size="small" />
                </template>
              </el-table-column>
              <el-table-column label="数量(条)" width="85">
                <template #default="{ row }"><el-input v-model="row.qty" size="small" /></template>
              </el-table-column>
              <el-table-column label="重量KG" width="90">
                <template #default="{ row }">{{ calcWeight(row) ? calcWeight(row).toFixed(1) : '' }}</template>
              </el-table-column>
              <el-table-column label="版数" width="80">
                <template #default="{ row }">{{ calcEdition(row) ? Math.ceil(calcEdition(row)) : '' }}</template>
              </el-table-column>
              <el-table-column label="备注" width="200">
                <template #default="{ row }"><el-input v-model="row.remark" size="small" /></template>
              </el-table-column>
              <el-table-column label="" width="50">
                <template #default="{ $index }">
                  <el-button size="small" type="danger" text @click="form.items.splice($index, 1)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <div style="display:flex;justify-content:center;align-items:center;margin-top:8px;gap:16px">
              <el-button @click="router.push('/contracts')">取消</el-button>
              <el-button type="primary" :loading="loading" @click="handleSave">保存</el-button>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-form>
    </el-card>

    <!-- 快速新建毛毯规格 -->
    <el-dialog v-model="showSpecDialog" title="新建毛毯规格" width="520px" style="text-align:left">
      <el-form :model="specForm" label-width="120px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="毛毯尺寸长" required>
              <el-input v-model="specForm.length" placeholder="如 200" @input="validateNumeric('length')" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="毛毯尺寸宽" required>
              <el-input v-model="specForm.width" placeholder="如 240" @input="validateNumeric('width')" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="毛毯总量(KG)" required>
          <el-input v-model="specForm.weight" placeholder="如 4" @input="validateNumeric('weight')" />
        </el-form-item>
        <el-form-item label="层类型" required>
          <el-radio-group v-model="specForm.layer_type">
            <el-radio v-for="lt in layerTypes" :key="lt.code" :value="lt.code">{{ lt.code }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="规格名称">
          <el-input :model-value="previewSpecName" disabled placeholder="自动生成" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSpecDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSpecSave" :loading="specSaving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createContract, updateContract, getContract, getNextContractNo } from '../../api/contract'
import { listCustomers } from '../../api/customer'
import { listSpecs, createSpec } from '../../api/spec'
import { listBasicData } from '../../api/basicData'

const route = useRoute()
const router = useRouter()
const isEdit = !!route.params.id
const contractStatus = ref('')
const loading = ref(false)
const customers = ref([])
const specs = ref([])
const showSpecDialog = ref(false)
const specSaving = ref(false)
const specForm = reactive({ length: '', width: '', weight: '', layer_type: '单层' })
const specTargetRow = ref(null)
const layerTypes = ref([])
const packagingTypes = ref([])
const hoverRowIndex = ref(-1)

const defaultDelivery = new Date()
defaultDelivery.setMonth(defaultDelivery.getMonth() + 1)

const form = reactive({
  contract_no: '', customer_id: null, contract_date: new Date(),
  delivery_date: defaultDelivery,
  items: [],
})

const totalAmount = computed(() =>
  form.items.reduce((s, i) => s + (parseFloat(i.unit_price) * parseFloat(i.qty) || 0), 0)
)

const previewSpecName = computed(() => {
  const f = specForm
  return f.length && f.width && f.weight ? `${f.length}*${f.width}/${f.weight}KG/${f.layer_type}` : ''
})

const specMap = computed(() => {
  const map = {}
  specs.value.forEach(s => { map[s.id] = s })
  return map
})

function parseWeight(spec) {
  if (!spec || !spec.weight) return 0
  return parseFloat(String(spec.weight).replace('KG', '')) || 0
}

function calcWeight(row) {
  const spec = specMap.value[row.spec_id]
  if (!spec || !row.qty) return 0
  return parseWeight(spec) * parseFloat(row.qty)
}

function calcEdition(row) {
  const spec = specMap.value[row.spec_id]
  if (!spec || !row.qty) return 0
  const qty = parseFloat(row.qty)
  const lt = spec.layer_type
  if (lt === '单层' || lt === '床单') return qty
  if (lt === '枕头') return qty * 2 / 9
  return qty * 2
}

function addItem() {
  form.items.push({
    line_no: form.items.length + 1, spec_id: null,
    packaging_type: '',
    is_pressed: false,
    delivery_date: form.delivery_date || null,
    unit_price: null, qty: null, amount: 0,
    remark: '',
  })
}

// Auto-generate contract_no when customer is selected
watch(() => form.customer_id, async (val) => {
  if (!val || isEdit) return
  try {
    const res = await getNextContractNo(val)
    form.contract_no = res.data.contract_no
  } catch {}
})

// Header delivery_date change → auto-update all item delivery_dates
watch(() => form.delivery_date, (val) => {
  if (!val) return
  form.items.forEach(item => { item.delivery_date = val })
})

function openSpecDialog(row) {
  specTargetRow.value = row
  specForm.length = ''; specForm.width = ''; specForm.weight = ''; specForm.layer_type = '单层'
  showSpecDialog.value = true
}

function validateNumeric(field) {
  specForm[field] = specForm[field].replace(/[^\d.]/g, '').replace(/(\..*)\./g, '$1')
}

async function handleSpecSave() {
  specSaving.value = true
  try {
    const res = await createSpec({ ...specForm })
    ElMessage.success('毛毯规格已创建')
    showSpecDialog.value = false
    const listRes = await listSpecs()
    specs.value = listRes.data
    const newSpec = res.data || listRes.data[0]
    if (specTargetRow.value && newSpec) {
      specTargetRow.value.spec_id = newSpec.id
      specTargetRow.value = null
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '创建失败')
  } finally {
    specSaving.value = false
  }
}

function fmtDate(d) {
  if (!d) return null
  const dt = new Date(d)
  return isNaN(dt.getTime()) ? d : dt.toISOString().slice(0, 10)
}

function validateForm() {
  if (!form.customer_id) { ElMessage.warning('请选择客户'); return false }
  if (!form.delivery_date) { ElMessage.warning('请填写合同交货日期'); return false }
  if (form.items.length === 0) { ElMessage.warning('请至少添加一个行项目'); return false }
  for (let i = 0; i < form.items.length; i++) {
    const item = form.items[i]
    if (!item.spec_id) { ElMessage.warning(`第${i + 1}行：请选择毛毯规格`); return false }
    if (!item.qty || parseFloat(item.qty) <= 0) { ElMessage.warning(`第${i + 1}行：请填写数量`); return false }
    if (!item.delivery_date) { ElMessage.warning(`第${i + 1}行：请填写交货日期`); return false }
    if (!item.packaging_type) { ElMessage.warning(`第${i + 1}行：请选择包装方式`); return false }
  }
  return true
}

async function handleSave() {
  if (!validateForm()) return
  loading.value = true
  try {
    const payload = {
      contract_no: form.contract_no,
      customer_id: form.customer_id,
      contract_date: fmtDate(form.contract_date),
      delivery_date: fmtDate(form.delivery_date),
      total_amount: totalAmount.value,
      items: form.items.map((item, idx) => {
        const base = {
          spec_id: item.spec_id,
          line_no: idx + 1,
          packaging_type: item.packaging_type || '',
          is_pressed: !!item.is_pressed,
          delivery_date: fmtDate(item.delivery_date),
          unit_price: parseFloat(item.unit_price) || 0,
          qty: parseFloat(item.qty) || 0,
          amount: (parseFloat(item.unit_price) || 0) * (parseFloat(item.qty) || 0),
          remark: item.remark || '',
        }
        if (item.id) base.id = item.id
        return base
      }),
    }
    let contractId
    if (isEdit) {
      await updateContract(route.params.id, payload)
      ElMessage.success('已更新')
      contractId = route.params.id
    } else {
      const res = await createContract(payload)
      ElMessage.success('已创建')
      contractId = res.data.id
    }
    router.push(`/contracts/${contractId}`)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    const [cRes, sRes, ltRes, ptRes] = await Promise.all([listCustomers(), listSpecs(), listBasicData('layer_type'), listBasicData('packaging_type')])
    customers.value = cRes.data
    specs.value = sRes.data
    layerTypes.value = ltRes.data || []
    packagingTypes.value = ptRes.data || []
  } catch {}
  if (isEdit) {
    try {
      const res = await getContract(route.params.id)
      contractStatus.value = res.data.status
      Object.assign(form, res.data)
    } catch { ElMessage.error('加载合同失败') }
  }
})
</script>
