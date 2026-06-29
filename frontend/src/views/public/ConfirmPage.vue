<template>
  <div style="max-width:960px;margin:0 auto;padding:20px">
    <el-card v-loading="loading">
      <template #header>
        <div style="text-align:center">
          <h2 v-if="alreadyConfirmed" style="color:#909399">工艺单已确认</h2>
          <h2 v-else>工艺单确认</h2>
          <div v-if="sheet" style="font-size:14px;color:#666">
            工艺单号: {{ sheet.sheet_no }} | 合同号: {{ sheet.contract_contract_no }}
          </div>
        </div>
      </template>

      <template v-if="alreadyConfirmed">
        <el-result icon="success" title="已确认" :sub-title="`工艺单 ${sheet?.sheet_no} 已被确认`" />
      </template>

      <template v-else-if="sheet">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="客户">{{ sheet.contract_customer_name }}</el-descriptions-item>
          <el-descriptions-item label="合同日期">{{ sheet.contract_date }}</el-descriptions-item>
          <el-descriptions-item label="版本">
            <el-tag size="small" v-if="sheet.confirm_version_no">{{ formatVersion(sheet.confirm_version_no) }}</el-tag>
            <span v-else>—</span>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider>行项目</el-divider>
        <el-table :data="sheet.items" stripe size="small">
          <el-table-column prop="line_no" label="行号" width="60" />
          <el-table-column label="毛毯规格" min-width="140">
            <template #default="{ row }">{{ row.spec_description }}</template>
          </el-table-column>
          <el-table-column label="包装方式" width="90">
            <template #default="{ row }">{{ row.packaging_type || '—' }}</template>
          </el-table-column>
          <el-table-column label="压花" width="55">
            <template #default="{ row }">{{ row.is_pressed ? '是' : '否' }}</template>
          </el-table-column>
          <el-table-column label="交货日期" width="100">
            <template #default="{ row }">{{ row.delivery_date || '—' }}</template>
          </el-table-column>
          <el-table-column prop="qty" label="数量(条)" width="75" />
          <el-table-column label="工艺备注" min-width="120">
            <template #default="{ row }">{{ row.process_remark || '—' }}</template>
          </el-table-column>
        </el-table>

        <template v-if="sheet.detail_data">
          <!-- 花型详情 -->
          <el-divider>花型详情</el-divider>
          <div v-for="item in sheet.items" :key="item.line_no" style="margin-bottom:16px">
            <div style="font-weight:bold;margin-bottom:4px">行{{ item.line_no }}: {{ item.spec_description }}</div>

            <!-- 花型 pattern_data -->
            <div v-if="item.pattern_data?.length">
              <div v-for="(p, pi) in item.pattern_data" :key="pi" style="margin:12px 0;padding:16px;background:#f5f7fa;border-radius:6px">
                <div style="display:flex;flex-wrap:wrap;gap:24px;align-items:center;margin-bottom:12px">
                  <el-tag size="small">{{ p.code }}</el-tag>
                  <span style="font-size:13px;color:#666">颜色: {{ p.color || '无色' }}</span>
                  <span style="font-size:13px;color:#666">数量: ×{{ p.qty }}</span>
                  <span style="font-size:13px;color:#666">色号: {{ p.binding_color_no || '—' }}</span>
                </div>
                <div v-if="p.image" style="margin-top:8px">
                  <el-image :src="p.image" style="width:100px;height:100px;border-radius:4px;object-fit:cover;border:1px solid #dcdfe6;cursor:pointer" :preview-src-list="[p.image]" preview-teleported />
                </div>
              </div>
            </div>

            <!-- A/B 面图片 -->
            <div v-if="item.image_a_1 || item.image_b_1" style="display:flex;flex-wrap:wrap;gap:12px;margin:8px 0">
              <div v-if="item.image_a_1" style="text-align:center">
                <div style="font-size:12px;color:#666;margin-bottom:2px">A面 ({{ item.color_a || '无色' }})</div>
                <el-image :src="item.image_a_1" style="width:100px;height:100px;border-radius:4px;object-fit:cover;border:1px solid #dcdfe6;cursor:pointer" :preview-src-list="[item.image_a_1, item.image_a_2, item.image_a_3].filter(Boolean)" preview-teleported />
              </div>
              <div v-if="item.image_b_1" style="text-align:center">
                <div style="font-size:12px;color:#666;margin-bottom:2px">B面 ({{ item.color_b || '无色' }})</div>
                <el-image :src="item.image_b_1" style="width:100px;height:100px;border-radius:4px;object-fit:cover;border:1px solid #dcdfe6;cursor:pointer" :preview-src-list="[item.image_b_1, item.image_b_2, item.image_b_3].filter(Boolean)" preview-teleported />
              </div>
            </div>

            <!-- 压花图片 -->
            <div v-if="item.pressed_image" style="margin:8px 0">
              <div style="font-size:12px;color:#666;margin-bottom:2px">压花参考图</div>
              <el-image :src="item.pressed_image" style="width:100px;height:100px;border-radius:4px;object-fit:cover;border:1px solid #dcdfe6;cursor:pointer" :preview-src-list="[item.pressed_image]" preview-teleported />
            </div>

            <span v-if="!item.pattern_data?.length && !item.image_a_1 && !item.image_b_1 && !item.pressed_image" style="color:#999;font-size:13px">无花型信息</span>
          </div>

          <!-- 辅料 -->
          <el-divider>辅料</el-divider>
          <div v-if="hasAccessories">
            <div v-for="(acc, idx) in accessoryList" :key="idx" style="border:1px solid #eee;border-radius:6px;padding:12px;margin-bottom:12px">
              <div style="display:flex;flex-wrap:wrap;align-items:center;gap:12px">
                <div style="font-weight:bold;min-width:60px">{{ acc.label }}</div>
                <div style="font-size:13px;color:#666;flex:1">
                  {{ acc.size || '—' }} / {{ acc.qty || '—' }}
                </div>
                <div v-if="acc.images?.length" style="display:flex;flex-wrap:wrap;gap:8px;align-items:center">
                  <el-image v-for="(img, ii) in acc.images" :key="ii" :src="img" style="width:80px;height:80px;border-radius:4px;object-fit:cover;border:1px solid #dcdfe6;cursor:pointer" :preview-src-list="acc.images" preview-teleported />
                </div>
              </div>
            </div>
          </div>
          <span v-else style="color:#999">无辅料信息</span>

          <!-- 技术要求 -->
          <el-divider>技术要求</el-divider>
          <el-descriptions :column="2" border>
            <el-descriptions-item v-for="i in 10" :key="'tn'+i" :label="'说明'+i">
              {{ sheet.detail_data[`tech_note_${i}`] || '—' }}
            </el-descriptions-item>
          </el-descriptions>

          <!-- 包装箱单 -->
          <el-divider>包装箱单</el-divider>
          <el-descriptions :column="2" border>
            <el-descriptions-item v-for="i in 5" :key="'pn'+i" :label="'包装'+i">
              {{ sheet.detail_data[`pack_note_${i}`] || '—' }}
            </el-descriptions-item>
          </el-descriptions>
          <el-descriptions :column="3" border style="margin-top:8px">
            <el-descriptions-item v-for="i in 3" :key="'bn'+i" :label="'箱单'+i">
              {{ sheet.detail_data[`box_note_${i}`] || '—' }}
            </el-descriptions-item>
          </el-descriptions>
        </template>
        <template v-else>
          <el-divider />
          <p style="color:#999;text-align:center">暂无生产工艺详情</p>
        </template>

        <el-divider />
        <h4>客户确认意见</h4>
        <el-input v-model="comment" type="textarea" :rows="4" placeholder="请输入您的确认意见（可选）" style="margin-bottom:16px" />

        <div style="text-align:center;margin:24px 0">
          <el-button type="primary" size="large" @click="handleConfirm" :loading="submitting" style="width:200px">确认工艺单</el-button>
        </div>
      </template>

      <template v-else-if="!loading">
        <el-result icon="error" title="无效链接" sub-title="该确认链接无效或工艺单已被删除" />
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const route = useRoute()
const sheet = ref(null)
const alreadyConfirmed = ref(false)
const loading = ref(true)
const submitting = ref(false)
const comment = ref('')

const accLabels = { 2: '包贴彩卡', 3: '钢丝袋', 4: '真空包' }

const accessoryList = computed(() => {
  const dd = sheet.value?.detail_data
  if (!dd) return []
  const result = []
  // washing_labels
  const wl = dd.washing_labels
  if (wl?.length && wl[0]?.label) {
    result.push({
      label: wl[0].label,
      size: wl[0].size || '',
      qty: wl[0].qty || '',
      images: wl[0].images || [],
    })
  }
  // origin_labels
  const ol = dd.origin_labels
  if (ol?.length && ol[0]?.label) {
    result.push({
      label: ol[0].label,
      size: ol[0].size || '',
      qty: ol[0].qty || '',
      images: ol[0].images || [],
    })
  }
  for (let i = 1; i <= 6; i++) {
    const desc = dd[`accessory_desc_${i}`]
    const size = dd[`accessory_size_${i}`] || ''
    const qty = dd[`accessory_qty_${i}`] || ''
    const images = dd[`accessory_images_${i}`] || []
    if (desc || size || qty || images.length) {
      result.push({
        label: desc || accLabels[i] || `辅料${i}`,
        size,
        qty,
        images,
      })
    }
  }
  return result
})

const hasAccessories = computed(() => accessoryList.value.length > 0)

function formatVersion(v) {
  if (!v || v === 0) return ''
  if (Number.isInteger(v)) return `V${v}`
  return `V${v.toFixed(2)}`
}

async function loadSheet() {
  loading.value = true
  try {
    const res = await axios.get(`/api/public/process-sheet/${route.params.token}`)
    if (res.data.already_confirmed) {
      alreadyConfirmed.value = true
      sheet.value = res.data
    } else {
      sheet.value = res.data
    }
  } catch {
    sheet.value = null
  } finally {
    loading.value = false
  }
}

async function handleConfirm() {
  submitting.value = true
  try {
    await axios.post(`/api/public/process-sheet/${route.params.token}/confirm`, { comment: comment.value })
    ElMessage.success('确认成功')
    await loadSheet()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '确认失败')
  } finally {
    submitting.value = false
  }
}

onMounted(loadSheet)
</script>
