<template>
  <div>
    <h2>工艺单详情</h2>
    <el-card v-loading="loading" style="margin:16px 0">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>工艺单号: {{ sheet?.sheet_no }}</span>
          <span>
            <el-tag :type="statusType(sheet?.status)" size="small">{{ sheet?.status }}</el-tag>
            <el-button size="small" type="success" style="margin-left:8px" @click="handleConfirm" :disabled="sheet?.status!=='草稿'">确认工艺单</el-button>
            <el-button size="small" type="primary" @click="handleDispatch" :disabled="sheet?.status!=='保存'">下发工艺单</el-button>
          </span>
        </div>
      </template>

      <el-descriptions :column="3" border>
        <el-descriptions-item label="合同号">{{ sheet?.contract?.contract_no }}</el-descriptions-item>
        <el-descriptions-item label="客户">{{ sheet?.contract?.customer?.name }}</el-descriptions-item>
        <el-descriptions-item label="合同版本">V{{ sheet?.confirm_version_no }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ sheet?.status }}</el-descriptions-item>
        <el-descriptions-item label="创建人">{{ sheet?.created_by }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ sheet?.created_at }}</el-descriptions-item>
        <el-descriptions-item label="合同日期">{{ sheet?.contract?.contract_date }}</el-descriptions-item>
        <el-descriptions-item label="总金额">¥{{ sheet?.contract?.total_amount?.toFixed(2) }}</el-descriptions-item>
      </el-descriptions>

      <el-divider>行项目</el-divider>

      <div v-if="sheet?.status === '草稿'" style="margin-bottom:8px;display:flex;gap:8px">
        <el-button type="primary" size="small" :loading="savingDetail" @click="handleSaveDetail">保存工艺详情</el-button>
      </div>

      <el-table :data="items" stripe size="small">
        <el-table-column prop="line_no" label="行号" width="60" />
        <el-table-column label="毛毯规格" min-width="150">
          <template #default="{ row }">
            {{ getSpecName(row.spec_id) }}
          </template>
        </el-table-column>
        <el-table-column label="包装方式" width="100">
          <template #default="{ row }">{{ row.packaging_type || '—' }}</template>
        </el-table-column>
        <el-table-column label="压花" width="60">
          <template #default="{ row }">{{ row.is_pressed ? '是' : '否' }}</template>
        </el-table-column>
        <el-table-column label="花型数" width="70">
          <template #default="{ row }">{{ row.pattern_count || 0 }}</template>
        </el-table-column>
        <el-table-column label="交货日期" width="110">
          <template #default="{ row }">{{ row.delivery_date || '—' }}</template>
        </el-table-column>
        <el-table-column label="价格" min-width="120">
          <template #default="{ row }">
            ¥{{ formatPrice(row.unit_price) }} × {{ row.qty || 0 }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row, $index }">
            <el-button size="small" type="primary" text :disabled="sheet?.status !== '草稿'" @click="openItemDetail($index)">明细</el-button>
            <el-button size="small" type="danger" text :disabled="sheet?.status !== '草稿'" @click="removeItem($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 保存后在只读模式下显示花型信息 -->
      <div v-if="sheet?.status !== '草稿' && items.length">
        <el-divider>花型详情</el-divider>
        <div v-for="(item, idx) in items" :key="item.id" style="margin-bottom:16px">
          <div style="font-weight:bold;margin-bottom:4px">行{{ item.line_no }}: {{ getSpecName(item.spec_id) }}</div>
          <div v-if="item.pattern_data?.length">
            <div v-for="(p, pi) in item.pattern_data" :key="pi" style="display:flex;gap:8px;align-items:center;margin:4px 0;padding:4px 8px;background:#f5f7fa;border-radius:4px">
              <el-tag size="small">{{ p.code }}</el-tag>
              <span style="font-size:12px;color:#666">颜色: {{ p.color || '无色' }}</span>
              <span style="font-size:12px;color:#666">数量: ×{{ p.qty }}</span>
              <span style="font-size:12px;color:#666">色号: {{ p.binding_color_no || '—' }}</span>
              <el-image v-if="p.image" :src="p.image" style="width:100px;height:100px;border-radius:4px;object-fit:cover;border:1px solid #dcdfe6;cursor:pointer" :preview-src-list="[p.image]" preview-teleported />
            </div>
          </div>
        </div>

        <el-divider>技术要求</el-divider>
        <el-descriptions :column="2" border>
          <el-descriptions-item v-for="i in 10" :key="'tn'+i" :label="'说明'+i">
            {{ detailData?.[`tech_note_${i}`] || '—' }}
          </el-descriptions-item>
        </el-descriptions>

        <el-divider>辅料</el-divider>
        <div v-if="accessories.length">
          <div v-for="acc in accessories" :key="acc.label" style="padding:4px 0">
            <strong>{{ acc.label }}:</strong> {{ acc.size }} / {{ acc.qty }}
          </div>
        </div>
        <span v-else style="color:#999">无辅料信息</span>

        <el-divider>包装箱单</el-divider>
        <el-descriptions :column="2" border>
          <el-descriptions-item v-for="i in 5" :key="'pn'+i" :label="'包装'+i">
            {{ detailData?.[`pack_note_${i}`] || '—' }}
          </el-descriptions-item>
        </el-descriptions>
        <el-descriptions :column="3" border style="margin-top:8px">
          <el-descriptions-item v-for="i in 3" :key="'bn'+i" :label="'箱单'+i">
            {{ detailData?.[`box_note_${i}`] || '—' }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>

    <!-- 行项目明细对话框 -->
    <el-dialog v-model="showDetailDialog" :title="'行项目明细 - 第' + (activeIdx + 1) + '行'" width="900px" destroy-on-close>
      <template v-if="activeItem">
        <el-tabs type="border-card">
          <el-tab-pane label="花型颜色">
            <el-form label-width="100px">
              <el-form-item label="工艺说明">
                <el-input :model-value="processDescription" disabled readonly />
              </el-form-item>
              <el-divider />
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-form-item label="包装方式">
                    <el-select v-model="activeItem.packaging_type" style="width:100%" placeholder="选择包装方式">
                      <el-option v-for="pt in packagingTypes" :key="pt.code" :label="pt.code" :value="pt.code" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="包边材料">
                    <el-input v-model="detailData.binding_material" :disabled="isBindingDisabled" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="包边宽度">
                    <el-input v-model="detailData.binding_width" :disabled="isBindingDisabled" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-form-item label="是否压花">
                    <el-switch v-model="activeItem.is_pressed" @change="onItemFieldChange" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <div style="display:flex;align-items:center;flex-wrap:wrap">
                    <el-button size="small" @click="triggerEmbossUpload">上传压花图片</el-button>
                    <div v-if="activeItem.pressed_image" style="position:relative;display:inline-block;margin-left:8px">
                      <img :src="activeItem.pressed_image" style="width:60px;height:60px;object-fit:cover;border:1px solid #ddd;border-radius:4px" />
                      <el-button size="small" circle style="position:absolute;top:-6px;right:-6px;padding:0;width:16px;height:16px;background:#f56c6c;color:#fff;border:none;font-size:10px;line-height:16px;min-height:auto" @click="removeEmbossImage">×</el-button>
                    </div>
                  </div>
                  <input type="file" ref="embossUploadRef" accept=".jpg,.jpeg,.png,.bmp" style="display:none" @change="onEmbossFileSelected" />
                </el-col>
              </el-row>
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-form-item label="花型个数">
                    <el-input-number v-model="activeItem.pattern_count" :min="0" :max="20" size="small" style="width:120px" @change="onPatternCountChange" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-divider />
              <template v-if="activeItem.pattern_count > 0">
                <div v-for="(p, pi) in activeItem.pattern_data" :key="pi" style="border:1px solid #eee;border-radius:6px;padding:12px;margin-bottom:8px">
                  <el-row :gutter="8" type="flex" align="middle">
                    <el-col :span="8" style="display:flex;align-items:center;min-height:40px;padding-left:0">
                      <el-form-item :label="'花型代码' + (pi + 1)" label-width="85px" label-style="padding-left:0" style="margin-bottom:0">
                        <el-input v-model="p.code" />
                      </el-form-item>
                    </el-col>
                    <el-col :span="4" style="display:flex;align-items:center;min-height:40px">
                      <el-form-item label="颜色" label-width="50px" style="margin-bottom:0">
                        <el-select v-model="p.color" filterable clearable style="width:100%" @change="(val) => onPatternColorChange(pi, val)">
                          <el-option v-for="(v, k) in colorMapping" :key="k" :label="k" :value="k" />
                        </el-select>
                      </el-form-item>
                    </el-col>
                    <el-col :span="4" style="display:flex;align-items:center;min-height:40px">
                      <el-form-item label="数量" label-width="50px" style="margin-bottom:0">
                        <el-input-number v-model="p.qty" :min="0" :precision="0" size="small" style="width:100%" :controls="false" />
                      </el-form-item>
                    </el-col>
                    <el-col :span="3" style="display:flex;align-items:center;min-height:40px">
                      <el-form-item label="色号" label-width="50px" style="margin-bottom:0">
                        <el-input v-model="p.binding_color_no" disabled />
                      </el-form-item>
                    </el-col>
                    <el-col :span="5" style="display:flex;align-items:center;min-height:40px">
                      <el-form-item label="用量(m)" label-width="60px" style="margin-bottom:0">
                        <el-input :model-value="p.qty ? (p.qty * 10.56).toFixed(1) : ''" disabled />
                      </el-form-item>
                    </el-col>
                  </el-row>
                  <el-row :gutter="8" style="margin-top:8px">
                    <el-col>
                      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
                        <el-button size="small" @click="triggerPatternUpload(pi)">上传图片</el-button>
                        <div v-if="p.image" style="position:relative;display:inline-block">
                          <img :src="p.image" style="width:80px;height:80px;object-fit:cover;border:1px solid #ddd;border-radius:4px" />
                          <el-button size="small" circle style="position:absolute;top:-8px;right:-8px;padding:0;width:20px;height:20px;background:#f56c6c;color:#fff;border:none;font-size:12px;line-height:20px;min-height:auto" @click="removePatternImage(pi)">×</el-button>
                        </div>
                      </div>
                    </el-col>
                  </el-row>
                  <input type="file" :ref="el => { if (el) patternUploadRefs[pi] = el }" accept=".jpg,.jpeg,.png,.bmp" style="display:none" @change="onPatternFileSelected(pi, $event)" />
                </div>
              </template>
              <template v-else>
                <el-empty description="请设置花型个数" :image-size="60" />
              </template>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="辅料">
            <div style="border:1px solid #eee;border-radius:6px;padding:12px;margin-bottom:12px">
              <div v-for="(sub, sgIdx) in washOriginGroups" :key="sgIdx" :style="sgIdx === 0 ? 'margin-bottom:8px' : ''">
                <el-row :gutter="12" type="flex" align="middle" justify="center">
                  <el-col :span="3" style="text-align:left;line-height:32px;font-weight:bold">
                    {{ washOriginLabels[sub.key] }}
                  </el-col>
                  <el-col :span="9" style="text-align:left">
                    <el-input v-model="subItems(sub.key)[0].size" placeholder="尺寸(cm) 如 10*15" @change="onDetailChange" />
                  </el-col>
                  <el-col :span="8" style="text-align:left">
                    <el-input v-model="subItems(sub.key)[0].qty" placeholder="数量" @change="onDetailChange" />
                  </el-col>
                  <el-col :span="4" style="text-align:left">
                    <el-button size="small" @click="triggerSubUpload(sub.key, 0)">上传图片</el-button>
                    <input type="file" :ref="el => setSubRef(sub.key, 0, el)" accept=".jpg,.jpeg,.png,.bmp" style="display:none" multiple @change="onSubFileSelected(sub.key, 0, $event)" />
                  </el-col>
                </el-row>
                <el-row :gutter="8" style="margin-top:4px" justify="center">
                  <el-col v-for="(img, iidx) in (subItems(sub.key)[0].images || [])" :key="iidx" :xs="8" :sm="8" :md="6" :lg="4" style="margin-bottom:8px">
                    <div style="position:relative;display:inline-block;width:100%">
                      <img :src="img" style="width:100%;height:80px;object-fit:cover;border:1px solid #ddd;border-radius:4px" />
                      <el-button size="small" circle style="position:absolute;top:-8px;right:-8px;padding:0;width:20px;height:20px;background:#f56c6c;color:#fff;border:none;font-size:12px;line-height:20px;min-height:auto" @click="removeSubImg(sub.key, 0, iidx)">×</el-button>
                    </div>
                  </el-col>
                </el-row>
              </div>
            </div>
            <div v-for="grp in accessoryGroups" :key="grp.key" style="border:1px solid #eee;border-radius:6px;padding:12px;margin-bottom:12px">
              <el-row :gutter="12" type="flex" align="middle" justify="center">
                <el-col :span="3" style="text-align:left;line-height:32px;font-weight:bold;white-space:nowrap">{{ grp.label }}</el-col>
                <el-col :span="9" style="text-align:left">
                  <el-input v-model="detailData[`accessory_size_${grp.key}`]" placeholder="尺寸(cm) 如 10*15" @change="onDetailChange" />
                </el-col>
                <el-col :span="8" style="text-align:left">
                  <el-input v-model="detailData[`accessory_qty_${grp.key}`]" placeholder="数量" @change="onDetailChange" />
                </el-col>
                <el-col :span="4" style="text-align:left">
                  <el-button size="small" @click="triggerAccUpload(grp.key)">上传图片</el-button>
                  <input type="file" :ref="el => setAccRef(grp.key, el)" accept=".jpg,.jpeg,.png,.bmp" style="display:none" multiple @change="onAccFileSelected(grp.key, $event)" />
                </el-col>
              </el-row>
              <el-row :gutter="8" style="margin-top:8px" justify="center">
                <el-col v-for="(img, idx) in (detailData[`accessory_images_${grp.key}`] || [])" :key="idx" :xs="8" :sm="8" :md="6" :lg="4" style="margin-bottom:8px">
                  <div style="position:relative;display:inline-block;width:100%">
                    <img :src="img" style="width:100%;height:80px;object-fit:cover;border:1px solid #ddd;border-radius:4px" />
                    <el-button size="small" circle style="position:absolute;top:-8px;right:-8px;padding:0;width:20px;height:20px;background:#f56c6c;color:#fff;border:none;font-size:12px;line-height:20px;min-height:auto" @click="removeAccImg(grp.key, idx)">×</el-button>
                  </div>
                </el-col>
              </el-row>
            </div>
          </el-tab-pane>

          <el-tab-pane label="技术要求">
            <el-row :gutter="20" style="margin-bottom:12px">
              <el-col :span="24">
                <el-form-item label="1">
                  <div style="display:flex;align-items:center;gap:4px;flex-wrap:wrap;width:100%;line-height:32px">
                    <span>请注意尺寸和重量控制:</span>
                    <span style="font-weight:bold">{{ specDimText }}</span>
                    <span>±</span>
                    <el-input v-model="detailData.tolerance" style="width:70px;display:inline-block" size="small" @change="updateTechNote1" />
                    <span>cm, 重量:</span>
                    <span style="font-weight:bold">{{ specWeightText }}</span>
                  </div>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20" style="margin-bottom:12px">
              <el-col :span="24">
                <el-form-item label="2">
                  <el-input v-model="detailData.tech_note_2" type="textarea" :rows="2" placeholder="2.质量要求,手感厚实,毛面爽滑光亮,不掉毛" @change="onDetailChange" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12" v-for="i in [3,4,5,6,7,8,9,10]" :key="'tn'+i">
                <el-form-item :label="''+i">
                  <el-input v-model="detailData[`tech_note_${i}`]" type="textarea" :rows="2" @change="onDetailChange" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-tab-pane>

          <el-tab-pane label="包装箱单">
            <el-divider>包装说明 (5项)</el-divider>
            <el-row :gutter="20">
              <el-col :span="12" v-for="i in 5" :key="'pn'+i">
                <el-form-item :label="'包装'+i">
                  <el-input v-model="detailData[`pack_note_${i}`]" type="textarea" :rows="2" @change="onDetailChange" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-divider>箱单说明 (3项)</el-divider>
            <el-row :gutter="20">
              <el-col :span="8" v-for="i in 3" :key="'bn'+i">
                <el-form-item :label="'箱单'+i">
                  <el-input v-model="detailData[`box_note_${i}`]" type="textarea" :rows="2" @change="onDetailChange" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20" style="margin-top:8px">
              <el-col :span="8">
                <el-form-item label="压花模型">
                  <el-input v-model="detailData.emboss_model" @change="onDetailChange" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-tab-pane>
        </el-tabs>
      </template>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getSheet, confirmSheet, dispatchSheet, updateSheetDetail } from '../../api/processSheet'
import { listSpecs } from '../../api/spec'
import { listBasicData, getColorMapping } from '../../api/basicData'
import { uploadImages } from '../../api/upload'

const route = useRoute()
const sheet = ref(null)
const specs = ref([])
const packagingTypes = ref([])
const colorMapping = ref({})
const loading = ref(false)
const savingDetail = ref(false)

// Items and detail data (reactive copies for editing)
const items = ref([])
const detailData = reactive({})

// Detail dialog state
const showDetailDialog = ref(false)
const activeIdx = ref(0)
const patternUploadRefs = reactive({})
const embossUploadRef = ref(null)
const accRefs = reactive({})
const subRefs = reactive({})

const accessoryGroups = [
  { key: 2, label: '包贴彩卡' },
  { key: 3, label: '钢丝袋' },
  { key: 4, label: '真空包' },
]

const washOriginGroups = [
  { key: 'washing', title: '洗标' },
  { key: 'origin', title: '产地标' },
]

const washOriginLabels = {
  washing: '洗标',
  origin: '产地标',
}

const activeItem = computed(() => items.value[activeIdx.value])

const processDescription = computed(() => {
  const item = activeItem.value
  if (!item) return ''
  const spec = specs.value.find(s => s.id === item.spec_id)
  const specName = spec ? spec.spec_name : ''
  const pressed = item.is_pressed ? '压花' : ''
  return `${specName}经编印花${pressed}毛毯-${item.packaging_type || ''}`
})

const isBindingDisabled = computed(() => {
  return activeItem.value?.packaging_type === '打卷面料'
})

const firstSpec = computed(() => {
  const item = items.value[0]
  if (!item?.spec_id) return null
  return specs.value.find(s => s.id === item.spec_id) || null
})

const specDimText = computed(() => {
  const spec = firstSpec.value
  return spec ? `${spec.length}*${spec.width}mm` : '—'
})

const specWeightText = computed(() => {
  const spec = firstSpec.value
  return spec ? spec.weight : '—'
})

const accessories = computed(() => {
  if (!detailData) return []
  const result = []
  for (let i = 1; i <= 6; i++) {
    if (detailData[`accessory_desc_${i}`]) {
      result.push({ label: accessoryGroups[i - 1]?.label || `辅料${i}`, size: detailData[`accessory_size_${i}`], qty: detailData[`accessory_qty_${i}`] })
    }
  }
  return result
})

function formatPrice(v) {
  return v ? parseFloat(v).toFixed(2) : '0.00'
}

function getSpecName(specId) {
  const spec = specs.value.find(s => s.id === specId)
  return spec ? spec.spec_description || spec.spec_name : `规格#${specId}`
}

function statusType(s) {
  if (s === '草稿') return 'warning'
  if (s === '保存') return 'success'
  return 'info'
}

function makePatternEntry() {
  return { code: '', color: '', binding_color_no: '', image: '', qty: null }
}

function syncPatternData(item) {
  if (!item.pattern_count || item.pattern_count <= 0) return
  const spec = specs.value.find(s => s.id === item.spec_id)
  const isComposite = spec?.layer_type?.includes('复合')
  const totalRows = isComposite ? item.pattern_count * 2 : item.pattern_count
  if (!item.pattern_data) item.pattern_data = []
  while (item.pattern_data.length < totalRows) {
    item.pattern_data.push(makePatternEntry())
  }
  if (item.pattern_data.length > totalRows) {
    item.pattern_data.splice(totalRows)
  }
  distributeQty(item)
}

function distributeQty(item) {
  if (!item?.pattern_data?.length) return
  const total = Math.floor(parseFloat(item.qty) || 0)
  const count = item.pattern_data.length
  if (count === 0) return
  const base = Math.floor(total / count)
  const remainder = total - base * count
  item.pattern_data.forEach((p, i) => {
    p.qty = i === 0 ? base + remainder : base
  })
}

function onPatternCountChange() {
  const item = activeItem.value
  if (item) syncPatternData(item)
}

function onPatternColorChange(index, color) {
  if (!color || !activeItem.value?.pattern_data?.[index]) return
  const bindingNo = colorMapping.value[color]
  if (bindingNo) {
    activeItem.value.pattern_data[index].binding_color_no = bindingNo
  }
}

function onItemFieldChange() {
  // reactivity marker for item-level changes
}

function onDetailChange() {
  // reactivity marker for detail_data changes
}

function updateTechNote1() {
  const spec = firstSpec.value
  if (spec) {
    detailData.tech_note_1 = `1.请注意尺寸和重量控制:${spec.length}*${spec.width}mm,±${detailData.tolerance || '1'}cm,重量:${spec.weight}`
  } else {
    detailData.tech_note_1 = '1.请注意尺寸和重量控制'
  }
}

// --- Image uploads ---
function triggerPatternUpload(index) {
  patternUploadRefs[index]?.click()
}

async function onPatternFileSelected(index, event) {
  const file = event.target.files?.[0]
  if (!file || !activeItem.value?.pattern_data?.[index]) return
  try {
    const res = await uploadImages([file])
    if (res.data?.[0]) {
      activeItem.value.pattern_data[index].image = res.data[0].url
      const name = (res.data[0].original_name || '').replace(/\.[^.]+$/, '')
      if (name && !activeItem.value.pattern_data[index].code) {
        activeItem.value.pattern_data[index].code = name
      }
    }
  } catch { ElMessage.error('图片上传失败') }
  event.target.value = ''
}

function removePatternImage(index) {
  if (activeItem.value?.pattern_data?.[index]) {
    activeItem.value.pattern_data[index].image = ''
  }
}

function triggerEmbossUpload() { embossUploadRef.value?.click() }

async function onEmbossFileSelected(event) {
  const file = event.target.files?.[0]
  if (!file || !activeItem.value) return
  try {
    const res = await uploadImages([file])
    if (res.data?.[0]) activeItem.value.pressed_image = res.data[0].url
  } catch { ElMessage.error('图片上传失败') }
  event.target.value = ''
}

function removeEmbossImage() { if (activeItem.value) activeItem.value.pressed_image = '' }

// Accessory image uploads
function setAccRef(key, el) { if (el) accRefs[key] = el }
function triggerAccUpload(key) { accRefs[key]?.click() }

async function onAccFileSelected(key, event) {
  const files = event.target.files
  if (!files?.length) return
  try {
    const res = await uploadImages(Array.from(files))
    if (res.data?.length) {
      if (!detailData[`accessory_images_${key}`]) detailData[`accessory_images_${key}`] = []
      res.data.forEach(img => detailData[`accessory_images_${key}`].push(img.url))
    }
  } catch { ElMessage.error('图片上传失败') }
  event.target.value = ''
}

function removeAccImg(key, idx) {
  const arr = detailData[`accessory_images_${key}`]
  if (arr) arr.splice(idx, 1)
}

// Sub-label image uploads (washing/origin)
function subItems(key) {
  return key === 'washing' ? detailData.washing_labels : detailData.origin_labels
}

function setSubRef(key, idx, el) { if (el) subRefs[`${key}_${idx}`] = el }
function triggerSubUpload(key, idx) { subRefs[`${key}_${idx}`]?.click() }

async function onSubFileSelected(key, idx, event) {
  const files = event.target.files
  if (!files?.length) return
  try {
    const res = await uploadImages(Array.from(files))
    if (res.data?.length) {
      const arr = subItems(key)
      if (arr?.[idx]) {
        if (!arr[idx].images) arr[idx].images = []
        res.data.forEach(img => arr[idx].images.push(img.url))
      }
    }
  } catch { ElMessage.error('图片上传失败') }
  event.target.value = ''
}

function removeSubImg(key, idx, iidx) {
  const arr = subItems(key)
  if (arr?.[idx]?.images) arr[idx].images.splice(iidx, 1)
}

// --- Item operations ---
function openItemDetail(index) {
  activeIdx.value = index
  syncPatternData(items.value[index])
  showDetailDialog.value = true
}

function removeItem(index) {
  items.value.splice(index, 1)
}

// --- Sheet operations ---
async function handleConfirm() {
  try {
    await confirmSheet(route.params.id)
    ElMessage.success('已确认')
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
}

async function handleDispatch() {
  try {
    await dispatchSheet(route.params.id)
    ElMessage.success('已下发')
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
}

async function handleSaveDetail() {
  savingDetail.value = true
  try {
    const payload = {
      detail_data: { ...detailData },
      items: items.value.map(item => ({
        id: item.id,
        is_pressed: item.is_pressed,
        packaging_type: item.packaging_type || '',
        delivery_date: item.delivery_date,
        pattern_count: item.pattern_count || 0,
        pattern_data: item.pattern_data || [],
        pattern_code: item.pattern_code || '',
        color_a: item.color_a || '',
        image_a_1: item.image_a_1 || '',
        image_a_2: item.image_a_2 || '',
        image_a_3: item.image_a_3 || '',
        color_b: item.color_b || '',
        image_b_1: item.image_b_1 || '',
        image_b_2: item.image_b_2 || '',
        image_b_3: item.image_b_3 || '',
        pressed_image: item.pressed_image || '',
        remark: item.remark || '',
      })),
    }
    await updateSheetDetail(route.params.id, payload)
    ElMessage.success('工艺详情已保存')
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    savingDetail.value = false
  }
}

async function loadData() {
  loading.value = true
  try {
    const res = await getSheet(route.params.id)
    sheet.value = res.data
    // Deep-copy items and detail_data for editing
    items.value = JSON.parse(JSON.stringify(res.data.items || []))
    const dd = res.data.detail_data || {}
    Object.assign(detailData, {
      binding_material: dd.binding_material || '',
      binding_width: dd.binding_width || '',
      binding_color_no: dd.binding_color_no || '',
      tolerance: dd.tolerance || '1',
      tech_note_1: dd.tech_note_1 || '',
      tech_note_2: dd.tech_note_2 || '2.质量要求,手感厚实,毛面爽滑光亮,不掉毛',
      tech_note_3: dd.tech_note_3 || '',
      tech_note_4: dd.tech_note_4 || '',
      tech_note_5: dd.tech_note_5 || '',
      tech_note_6: dd.tech_note_6 || '',
      tech_note_7: dd.tech_note_7 || '',
      tech_note_8: dd.tech_note_8 || '',
      tech_note_9: dd.tech_note_9 || '',
      tech_note_10: dd.tech_note_10 || '',
      accessory_desc_1: dd.accessory_desc_1 || '',
      accessory_size_1: dd.accessory_size_1 || '',
      accessory_qty_1: dd.accessory_qty_1 || null,
      accessory_images_1: dd.accessory_images_1 || [],
      accessory_desc_2: dd.accessory_desc_2 || '',
      accessory_size_2: dd.accessory_size_2 || '',
      accessory_qty_2: dd.accessory_qty_2 || '',
      accessory_images_2: dd.accessory_images_2 || [],
      accessory_desc_3: dd.accessory_desc_3 || '',
      accessory_size_3: dd.accessory_size_3 || '',
      accessory_qty_3: dd.accessory_qty_3 || '',
      accessory_images_3: dd.accessory_images_3 || [],
      accessory_desc_4: dd.accessory_desc_4 || '',
      accessory_size_4: dd.accessory_size_4 || '',
      accessory_qty_4: dd.accessory_qty_4 || '',
      accessory_images_4: dd.accessory_images_4 || [],
      accessory_desc_5: dd.accessory_desc_5 || '',
      accessory_size_5: dd.accessory_size_5 || '',
      accessory_qty_5: dd.accessory_qty_5 || null,
      accessory_desc_6: dd.accessory_desc_6 || '',
      accessory_size_6: dd.accessory_size_6 || '',
      accessory_qty_6: dd.accessory_qty_6 || null,
      washing_labels: dd.washing_labels?.length ? dd.washing_labels : [{ label: '洗标', size: '', qty: '', images: [] }],
      origin_labels: dd.origin_labels?.length ? dd.origin_labels : [{ label: '产地标', size: '', qty: '', images: [] }],
      pack_note_1: dd.pack_note_1 || '',
      pack_note_2: dd.pack_note_2 || '',
      pack_note_3: dd.pack_note_3 || '',
      pack_note_4: dd.pack_note_4 || '',
      pack_note_5: dd.pack_note_5 || '',
      box_note_1: dd.box_note_1 || '',
      box_note_2: dd.box_note_2 || '',
      box_note_3: dd.box_note_3 || '',
      emboss_model: dd.emboss_model || '',
    })
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

onMounted(async () => {
  try {
    const [sRes, ptRes, cmRes] = await Promise.all([
      listSpecs(),
      listBasicData('packing'),
      getColorMapping(),
    ])
    specs.value = sRes.data
    packagingTypes.value = ptRes.data || []
    colorMapping.value = cmRes.data || {}
  } catch {}
  loadData()
})
</script>
