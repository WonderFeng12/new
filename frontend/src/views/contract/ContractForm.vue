<template>
  <div>
    <h2>{{ isEdit ? '编辑合同' : '新建合同' }}</h2>
    <el-card style="margin:16px 0">
      <el-form :model="form" label-width="120px" v-loading="loading">
        <el-tabs type="border-card">
          <el-tab-pane label="基本信息">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="合同编号">
                  <el-input v-model="form.contract_no" placeholder="自动生成" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="客户" required>
                  <el-select v-model="form.customer_id" filterable style="width:100%">
                    <el-option v-for="c in customers" :key="c.id" :label="c.name" :value="c.id" />
                  </el-select>
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
                <el-form-item label="规格" required>
                  <el-select v-model="form.spec_id" filterable style="width:100%" @change="onSpecChange">
                    <el-option v-for="s in specs" :key="s.id" :label="s.spec_description" :value="s.id" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="是否压花">
                  <el-switch v-model="form.is_pressed" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="包装方式">
                  <el-input v-model="form.packaging_type" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="交货日期">
                  <el-date-picker v-model="form.delivery_date" style="width:100%" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="规格描述">
                  <el-input v-model="form.spec_description" :disabled="!form.spec_description" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-divider>包边信息</el-divider>
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="包边材料">
                  <el-input v-model="form.binding_material" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="包边宽度">
                  <el-input v-model="form.binding_width" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="包边色号">
                  <el-input v-model="form.binding_color_no" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-tab-pane>

          <el-tab-pane label="工艺备注">
            <el-divider>工艺说明 (10项)</el-divider>
            <el-row :gutter="20">
              <el-col :span="12" v-for="i in 10" :key="'tn'+i">
                <el-form-item :label="'说明'+i">
                  <el-input v-model="form[`tech_note_${i}`]" type="textarea" :rows="2" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-tab-pane>

          <el-tab-pane label="辅料信息">
            <el-divider>辅料 (6组)</el-divider>
            <el-row :gutter="20" v-for="i in 6" :key="'acc'+i" style="margin-bottom:8px">
              <el-col :span="8">
                <el-form-item :label="'辅料'+i+'名称'">
                  <el-input v-model="form[`accessory_desc_${i}`]" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item :label="'辅料'+i+'规格'">
                  <el-input v-model="form[`accessory_size_${i}`]" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item :label="'辅料'+i+'数量'">
                  <el-input-number v-model="form[`accessory_qty_${i}`]" :min="0" style="width:100%" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-tab-pane>

          <el-tab-pane label="包装箱单">
            <el-divider>包装说明 (5项)</el-divider>
            <el-row :gutter="20">
              <el-col :span="12" v-for="i in 5" :key="'pn'+i">
                <el-form-item :label="'包装'+i">
                  <el-input v-model="form[`pack_note_${i}`]" type="textarea" :rows="2" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-divider>箱单说明 (3项)</el-divider>
            <el-row :gutter="20">
              <el-col :span="8" v-for="i in 3" :key="'bn'+i">
                <el-form-item :label="'箱单'+i">
                  <el-input v-model="form[`box_note_${i}`]" type="textarea" :rows="2" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20" style="margin-top:8px">
              <el-col :span="8">
                <el-form-item label="压花模型">
                  <el-input v-model="form.emboss_model" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-tab-pane>

          <el-tab-pane label="行项目">
            <el-button type="primary" size="small" @click="addItem">添加行项目</el-button>
            <el-table :data="form.items" stripe style="margin-top:8px" max-height="500">
              <el-table-column label="行号" width="60">
                <template #default="{ $index }">{{ $index + 1 }}</template>
              </el-table-column>
              <el-table-column label="花型代码" width="120">
                <template #default="{ row }"><el-input v-model="row.pattern_code" size="small" /></template>
              </el-table-column>
              <el-table-column label="颜色A" width="100">
                <template #default="{ row }"><el-input v-model="row.color_a" size="small" /></template>
              </el-table-column>
              <el-table-column label="颜色A图片" min-width="180">
                <template #default="{ row }">
                  <el-input v-model="row.image_a_1" placeholder="图片URL" size="small" style="margin-bottom:2px" />
                  <el-input v-model="row.image_a_2" placeholder="图片URL" size="small" style="margin-bottom:2px" />
                  <el-input v-model="row.image_a_3" placeholder="图片URL" size="small" />
                </template>
              </el-table-column>
              <el-table-column label="颜色B" width="100">
                <template #default="{ row }"><el-input v-model="row.color_b" size="small" /></template>
              </el-table-column>
              <el-table-column label="颜色B图片" min-width="180">
                <template #default="{ row }">
                  <el-input v-model="row.image_b_1" placeholder="图片URL" size="small" style="margin-bottom:2px" />
                  <el-input v-model="row.image_b_2" placeholder="图片URL" size="small" style="margin-bottom:2px" />
                  <el-input v-model="row.image_b_3" placeholder="图片URL" size="small" />
                </template>
              </el-table-column>
              <el-table-column label="单价" width="100">
                <template #default="{ row }"><el-input-number v-model="row.unit_price" :min="0" size="small" style="width:90px" @change="calcItem(row)" /></template>
              </el-table-column>
              <el-table-column label="数量" width="100">
                <template #default="{ row }"><el-input-number v-model="row.qty" :min="0" size="small" style="width:90px" @change="calcItem(row)" /></template>
              </el-table-column>
              <el-table-column label="金额" width="100">
                <template #default="{ row }">{{ (row.unit_price * row.qty || 0).toFixed(2) }}</template>
              </el-table-column>
              <el-table-column label="备注" min-width="120">
                <template #default="{ row }"><el-input v-model="row.remark" size="small" /></template>
              </el-table-column>
              <el-table-column width="50">
                <template #default="{ $index }">
                  <el-button type="danger" size="small" text @click="form.items.splice($index, 1)">×</el-button>
                </template>
              </el-table-column>
            </el-table>
            <div style="text-align:right;margin-top:8px;font-weight:bold;font-size:16px">
              总金额: ¥{{ totalAmount.toFixed(2) }}
            </div>
          </el-tab-pane>
        </el-tabs>

        <div style="text-align:center;margin-top:20px">
          <el-button @click="$router.back()">取消</el-button>
          <el-button type="primary" @click="handleSave">保存</el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createContract, updateContract, getContract } from '../../api/contract'
import { listCustomers } from '../../api/customer'
import { listSpecs } from '../../api/spec'

const route = useRoute()
const router = useRouter()
const isEdit = !!route.params.id
const loading = ref(false)
const customers = ref([])
const specs = ref([])

const form = reactive({
  contract_no: '', customer_id: null, contract_date: '', spec_id: null,
  spec_description: '', is_pressed: false, packaging_type: '', delivery_date: null,
  binding_material: '', binding_width: '', binding_color_no: '',
  tech_note_1: '', tech_note_2: '', tech_note_3: '', tech_note_4: '', tech_note_5: '',
  tech_note_6: '', tech_note_7: '', tech_note_8: '', tech_note_9: '', tech_note_10: '',
  accessory_desc_1: '', accessory_size_1: '', accessory_qty_1: null,
  accessory_desc_2: '', accessory_size_2: '', accessory_qty_2: null,
  accessory_desc_3: '', accessory_size_3: '', accessory_qty_3: null,
  accessory_desc_4: '', accessory_size_4: '', accessory_qty_4: null,
  accessory_desc_5: '', accessory_size_5: '', accessory_qty_5: null,
  accessory_desc_6: '', accessory_size_6: '', accessory_qty_6: null,
  pack_note_1: '', pack_note_2: '', pack_note_3: '', pack_note_4: '', pack_note_5: '',
  box_note_1: '', box_note_2: '', box_note_3: '',
  emboss_model: '',
  items: [],
})

const totalAmount = computed(() =>
  form.items.reduce((s, i) => s + (i.unit_price * i.qty || 0), 0)
)

function calcItem(row) {
  row.amount = (row.unit_price || 0) * (row.qty || 0)
}

function addItem() {
  form.items.push({
    line_no: form.items.length + 1, unit_price: null, qty: null, amount: 0,
    pattern_code: '', color_a: '', image_a_1: '', image_a_2: '', image_a_3: '',
    color_b: '', image_b_1: '', image_b_2: '', image_b_3: '', remark: '',
  })
}

function onSpecChange(id) {
  const spec = specs.value.find(s => s.id === id)
  if (spec) form.spec_description = spec.spec_description
}

async function handleSave() {
  loading.value = true
  try {
    const payload = { ...form, total_amount: totalAmount.value }
    payload.items = payload.items.map((item, idx) => ({
      ...item, line_no: idx + 1, amount: (item.unit_price || 0) * (item.qty || 0),
    }))
    if (isEdit) {
      await updateContract(route.params.id, payload)
      ElMessage.success('已更新')
    } else {
      await createContract(payload)
      ElMessage.success('已创建')
    }
    router.push('/contracts')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    const [cRes, sRes] = await Promise.all([listCustomers(), listSpecs()])
    customers.value = cRes.data
    specs.value = sRes.data
  } catch {}
  if (isEdit) {
    try {
      const res = await getContract(route.params.id)
      Object.assign(form, res.data)
    } catch { ElMessage.error('加载合同失败') }
  }
})
</script>
