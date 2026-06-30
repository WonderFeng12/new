<template>
  <div>
    <h2>工艺单详情</h2>
    <el-card v-loading="loading" style="margin:16px 0">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>
            工艺单号: {{ sheet?.sheet_no }}
            <el-tag v-if="formatVersion(sheet?.confirm_version_no)" size="small" type="info" style="margin-left:8px">{{ formatVersion(sheet?.confirm_version_no) }}</el-tag>
            <el-tag v-if="sheet?.version_marked" size="small" type="warning" style="margin-left:8px">沟通中</el-tag>
            <el-tag v-if="sheet?.customer_confirmed && sheet?.status === '草稿'" size="small" type="success" style="margin-left:8px">客户已确认</el-tag>
          </span>
          <span>
            <el-tag :type="statusType(sheet?.status)" size="small">{{ sheet?.status }}</el-tag>
            <template v-if="sheet?.status === '草稿' && !sheet?.customer_confirmed">
              <el-button size="small" type="warning" style="margin-left:8px" @click="showMarkDialog = true" :disabled="sheet?.status!=='草稿'" :plain="!!sheet?.version_marked">客户沟通</el-button>
              <el-button v-if="permStore.hasPermission('sheet:set_confirm_users')" size="small" style="margin-left:8px" @click="handleOpenConfirmUsers">设置确认人</el-button>
              <el-popconfirm v-if="permStore.hasPermission('sheet:force_confirm')" title="确定直接确认？将跳过所有审核直接升级版本" @confirm="handleForceConfirm">
                <template #reference>
                  <el-button size="small" type="danger" style="margin-left:8px">管理员确认</el-button>
                </template>
              </el-popconfirm>
            </template>
            <template v-else-if="sheet?.status === '草稿' && sheet?.customer_confirmed">
              <span style="margin-left:8px;font-size:12px;color:#e6a23c;vertical-align:middle">
                客户已确认，待内部确认 ({{ internalConfirmCount }}/{{ sheet?.internal_confirm_required || 1 }})
              </span>
              <el-button v-if="canInternalConfirm" size="small" type="success" style="margin-left:8px" @click="handleInternalConfirm">内部确认</el-button>
              <el-popconfirm v-if="permStore.hasPermission('sheet:force_confirm')" title="确定强制通过？将跳过内部确认直接升级版本" @confirm="handleForceConfirm">
                <template #reference>
                  <el-button size="small" type="danger" style="margin-left:8px">强制通过</el-button>
                </template>
              </el-popconfirm>
              <el-button v-if="canReopenEdit" size="small" type="danger" plain style="margin-left:8px" @click="handleReopenEdit">重新编辑</el-button>
            </template>
            <template v-else-if="sheet?.status === '保存' || sheet?.status === '已确认'">
              <el-button size="small" type="primary" @click="handleDispatch" :disabled="sheet?.status === '已下发'">下发工艺单</el-button>
              <el-button v-if="canReopenEdit" size="small" type="danger" plain style="margin-left:8px" @click="handleReopenEdit">重新编辑</el-button>
            </template>
            <template v-if="sheet?.status === '已下发'">
              <el-button size="small" style="margin-left:8px" @click="handlePrint">打印</el-button>
              <el-button v-if="canReopenEdit" size="small" type="danger" plain style="margin-left:8px" @click="handleReopenEdit">重新编辑</el-button>
            </template>
          </span>
        </div>
      </template>

      <el-descriptions :column="3" border>
        <el-descriptions-item label="合同号">
          <el-link type="primary" @click="$router.push(`/contracts/${sheet?.contract?.id}`)">{{ sheet?.contract?.contract_no }}</el-link>
        </el-descriptions-item>
        <el-descriptions-item label="客户">{{ sheet?.contract?.customer?.name }}</el-descriptions-item>
        <el-descriptions-item label="合同版本">
          <template v-if="sheet?.contract_snapshot">
            {{ formatVersion(sheet?.contract_snapshot?.latest_confirm_version) || 'V0' }}
            <el-tag v-if="contractVersionMatch" :type="contractVersionMatch.match ? 'success' : 'warning'" size="small" style="margin-left:4px">
              {{ contractVersionMatch.match ? '一致' : '不一致' }}
            </el-tag>
          </template>
          <span v-else>—</span>
        </el-descriptions-item>
        <el-descriptions-item v-if="formatVersion(sheet?.confirm_version_no)" label="工艺单版本">
          {{ formatVersion(sheet?.confirm_version_no) }}
          <el-tag v-if="sheet?.version_note" size="small" type="info" style="margin-left:4px">{{ sheet?.version_note }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item v-else label="工艺单版本">—</el-descriptions-item>
        <el-descriptions-item label="状态">{{ sheet?.status }}</el-descriptions-item>
        <el-descriptions-item label="创建人">{{ sheet?.created_by }}</el-descriptions-item>
        <el-descriptions-item label="合同日期">{{ sheet?.contract?.contract_date }}</el-descriptions-item>
        <el-descriptions-item label="交货日期">{{ sheet?.items?.[0]?.delivery_date || sheet?.contract?.delivery_date || '—' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ sheet?.created_at }}</el-descriptions-item>
      </el-descriptions>

      <el-divider>行项目</el-divider>

      <el-table :data="items" stripe size="small">
        <el-table-column prop="line_no" label="行号" width="60" />
        <el-table-column label="毛毯规格" width="180">
          <template #default="{ row }">
            {{ getSpecName(row.spec_id) }}
          </template>
        </el-table-column>
        <el-table-column label="包装方式" width="90">
          <template #default="{ row }">{{ row.packaging_type || '—' }}</template>
        </el-table-column>
        <el-table-column label="包边材料" width="100">
          <template #default="{ row }">{{ detailData.binding_material || '—' }}</template>
        </el-table-column>
        <el-table-column label="包边宽度" width="90">
          <template #default="{ row }">{{ detailData.binding_width || '—' }}</template>
        </el-table-column>
        <el-table-column label="压花" width="55">
          <template #default="{ row }">{{ row.is_pressed ? '是' : '否' }}</template>
        </el-table-column>
        <el-table-column label="花型数" width="65">
          <template #default="{ row }">{{ row.pattern_count || 0 }}</template>
        </el-table-column>
        <el-table-column label="数量" width="75">
          <template #default="{ row }">{{ row.qty || 0 }}</template>
        </el-table-column>
        <el-table-column label="交货日期" width="100">
          <template #default="{ row }">{{ row.delivery_date || '—' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row, $index }">
            <el-button size="small" type="primary" text :disabled="sheet?.status !== '草稿'" @click="openItemDetail($index)">明细</el-button>
            <el-button size="small" type="danger" text :disabled="sheet?.status !== '草稿'" @click="removeItem($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-divider>版本历史</el-divider>
      <div style="margin-bottom:16px">
        <el-timeline>
          <el-timeline-item timestamp="工艺单创建" :timestamp="sheet?.created_at || '—'" type="primary" size="large">
            <p style="margin:0">创建人: {{ sheet?.created_by || '—' }}</p>
            <p style="margin:0;font-size:12px;color:#999">版本 V0</p>
            <template v-if="sheet?.contract_snapshot">
              <p style="margin:4px 0 0;font-size:12px">
                合同号: <el-link type="primary" style="font-size:12px" @click="$router.push(`/contracts/${sheet?.contract?.id}`)">{{ sheet?.contract_snapshot?.contract_no || '—' }}</el-link>
              </p>
              <p style="margin:2px 0 0;font-size:12px">
                下推时合同版本: {{ formatVersion(sheet?.contract_snapshot?.latest_confirm_version) || 'V0' }}
                <el-tag v-if="contractVersionMatch" :type="contractVersionMatch.match ? 'success' : 'warning'" size="small" style="margin-left:4px">
                  {{ contractVersionMatch.match ? '版本一致' : '版本不一致' }}
                </el-tag>
              </p>
              <p v-if="contractVersionMatch && !contractVersionMatch.match" style="margin:2px 0 0;font-size:12px;color:#e6a23c">
                当前合同最新版本: {{ formatVersion(contractVersionMatch.current) }} — 建议重新下推
              </p>
            </template>
          </el-timeline-item>
          <el-timeline-item v-for="(evt, ei) in reopenEvents" :key="'reopen'+ei" timestamp="重新编辑" :timestamp="evt.created_at || '—'" type="danger" size="large">
            <p style="margin:0;font-size:12px;color:#666">{{ evt.remark }}</p>
            <p style="margin:2px 0 0;font-size:12px;color:#999">{{ evt.operator_name || '—' }}</p>
          </el-timeline-item>
          <el-timeline-item v-for="(evt, ei) in commEvents" :key="'comm'+ei" timestamp="客户沟通标记" :timestamp="evt.created_at || '—'" type="warning" size="large">
            <p style="margin:0;font-size:12px;color:#666">{{ evt.remark }}</p>
          </el-timeline-item>
          <el-timeline-item v-for="(evt, ei) in customerConfirmedFromLog" :key="'cc'+ei" :timestamp="evt.created_at || '—'" type="success" size="large">
            <template #timestamp>客户已确认</template>
            <p style="margin:0;font-size:12px;color:#666">{{ evt.remark }}</p>
            <p v-if="evt.remark && !evt.remark.includes(sheet?.customer_comment || '') && sheet?.customer_comment" style="margin:4px 0 0;font-size:12px;color:#666">客户意见: {{ sheet?.customer_comment }}</p>
          </el-timeline-item>
          <el-timeline-item v-if="sheet?.status === '保存' || sheet?.status === '已确认' || sheet?.status === '已下发'" timestamp="内部确认完成，版本锁定" :timestamp="sheet?.updated_at || '—'" type="success" size="large">
            <p style="margin:0">正式版本: <strong>{{ formatVersion(sheet?.confirm_version_no) }}</strong></p>
          </el-timeline-item>
          <el-timeline-item v-if="sheet?.status === '已下发'" timestamp="工艺单已下发" :timestamp="sheet?.updated_at || '—'" type="primary" size="large">
            <p style="margin:0;font-size:12px;color:#999">工艺单发至车间</p>
          </el-timeline-item>
        </el-timeline>
      </div>

      <el-divider>操作日志</el-divider>
      <StatusLog
        :logs="logs"
        :columns="['时间','操作','备注']"
        :loading="loadingLogs"
      />

      <!-- 保存后在只读模式下显示花型信息 -->
      <div v-if="sheet?.status !== '草稿' && items.length">
        <el-divider>花型详情</el-divider>
        <div v-for="(item, idx) in items" :key="item.id" style="margin-bottom:16px">
          <div style="font-weight:bold;margin-bottom:4px">行{{ item.line_no }}: {{ getSpecName(item.spec_id) }}</div>
          <div v-if="item.pattern_data?.length">
            <div v-for="(p, pi) in item.pattern_data" :key="pi" style="display:flex;gap:8px;align-items:center;margin:4px 0;padding:4px 8px;background:#f5f7fa;border-radius:4px">
              <span style="font-size:12px;font-weight:bold;min-width:85px">{{ getPatternLabel(pi, item) }}</span>
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
        <div v-for="i in 8" :key="'pnr'+i">
          <div v-if="detailData[`pack_note_${i}`]" style="padding:2px 0;font-size:13px">{{ detailData[`pack_note_${i}`] }}</div>
        </div>
        <template v-if="detailData.box_note_1 || detailData.box_note_2 || detailData.box_note_3 || extraBoxNoteCount">
          <el-divider style="margin:8px 0">包装箱要求</el-divider>
          <div v-for="i in 6" :key="'bnr'+i">
            <div v-if="detailData[`box_note_${i}`]" style="padding:2px 0;font-size:13px">{{ detailData[`box_note_${i}`] }}</div>
          </div>
        </template>
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
                    <el-select v-model="activeItem.packaging_type" style="width:100%" placeholder="选择包装方式" disabled>
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
                      <div v-if="activeItem.pressed_image_name" style="font-size:10px;color:#666;text-align:center;max-width:70px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ activeItem.pressed_image_name }}</div>
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
                    <el-col :span="7" style="display:flex;align-items:center;min-height:40px;padding-left:0!important">
                      <el-form-item :label="getPatternLabel(pi, activeItem)" label-width="100px" label-style="padding-left:0" style="margin-bottom:0">
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
                    <el-col :span="4" style="display:flex;align-items:center;min-height:40px">
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
                <el-input v-model="detailData.tech_note_1" type="textarea" :rows="2" @change="onDetailChange" />
              </el-col>
            </el-row>
            <el-row :gutter="20" style="margin-bottom:12px">
              <el-col :span="24">
                <el-input v-model="detailData.tech_note_2" type="textarea" :rows="2" @change="onDetailChange" />
              </el-col>
            </el-row>
            <el-row :gutter="20" style="margin-bottom:12px">
              <el-col :span="24">
                <el-input v-model="detailData.tech_note_3" type="textarea" :rows="2" @change="onDetailChange" />
              </el-col>
            </el-row>
            <el-row :gutter="20" style="margin-bottom:12px">
              <el-col :span="24">
                <el-input v-model="detailData.tech_note_4" type="textarea" :rows="2" @change="onDetailChange" />
              </el-col>
            </el-row>
            <el-row :gutter="20" style="margin-bottom:12px">
              <el-col :span="24">
                <el-input v-model="detailData.tech_note_5" type="textarea" :rows="2" @change="onDetailChange" />
              </el-col>
            </el-row>
            <el-row :gutter="20" v-for="i in extraTechNoteCount" :key="'extra'+(5+i)" style="margin-bottom:12px">
              <el-col :span="24">
                <el-input v-model="detailData[`tech_note_${5+i}`]" type="textarea" :rows="2" @change="onDetailChange" />
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="24">
                <el-button type="primary" text @click="addTechNote">+ 新增技术说明</el-button>
              </el-col>
            </el-row>
          </el-tab-pane>

          <el-tab-pane label="包装箱单">
            <el-divider>包装 (3项)</el-divider>
            <el-row :gutter="20" style="margin-bottom:12px">
              <el-col :span="24">
                <el-input v-model="detailData.pack_note_1" type="textarea" :rows="2" @change="onDetailChange" />
              </el-col>
            </el-row>
            <el-row :gutter="20" style="margin-bottom:12px">
              <el-col :span="24">
                <el-input v-model="detailData.pack_note_2" type="textarea" :rows="2" @change="onDetailChange" />
              </el-col>
            </el-row>
            <el-row :gutter="20" style="margin-bottom:12px">
              <el-col :span="24">
                <el-input v-model="detailData.pack_note_3" type="textarea" :rows="2" @change="onDetailChange" />
              </el-col>
            </el-row>
            <el-row :gutter="20" v-for="i in extraPackNoteCount" :key="'extraPn'+(3+i)" style="margin-bottom:12px">
              <el-col :span="24">
                <el-input v-model="detailData[`pack_note_${3+i}`]" type="textarea" :rows="2" @change="onDetailChange" />
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="24">
                <el-button type="primary" text @click="addPackNote">+ 新增包装说明</el-button>
              </el-col>
            </el-row>

            <el-divider>包装箱要求 (2项)</el-divider>
            <el-row :gutter="20" style="margin-bottom:12px">
              <el-col :span="24">
                <el-input v-model="detailData.box_note_1" type="textarea" :rows="2" @change="onDetailChange" />
              </el-col>
            </el-row>
            <el-row :gutter="20" style="margin-bottom:12px">
              <el-col :span="24">
                <el-input v-model="detailData.box_note_2" type="textarea" :rows="2" @change="onDetailChange" />
              </el-col>
            </el-row>
            <el-row :gutter="20" v-for="i in extraBoxNoteCount" :key="'extraBn'+(2+i)" style="margin-bottom:12px">
              <el-col :span="24">
                <el-input v-model="detailData[`box_note_${2+i}`]" type="textarea" :rows="2" @change="onDetailChange" />
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="24">
                <el-button type="primary" text @click="addBoxNote">+ 新增箱单说明</el-button>
              </el-col>
            </el-row>

          </el-tab-pane>
        </el-tabs>
      </template>
      <template #footer>
        <el-button type="primary" @click="saveItemDetail">保存</el-button>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 客户沟通对话框 -->
    <el-dialog v-model="showMarkDialog" title="客户沟通" width="560px" :close-on-click-modal="!markingVersion">
      <template v-if="!confirmLink">
        <p v-if="formatVersion(sheet?.confirm_version_no)" style="margin-bottom:12px;color:#666">
          当前版本 {{ formatVersion(sheet?.confirm_version_no) }}，将标记用于客户沟通。每次保存版本自动 +0.01。
        </p>
        <p v-else style="margin-bottom:12px;color:#666">
          将生成初始沟通版本 <strong>V0.11</strong>，开始与客户沟通。后续每次保存版本自动 +0.01。
        </p>
        <el-form>
          <el-form-item label="沟通说明">
            <el-input v-model="markNote" type="textarea" :rows="3" placeholder="请描述本次沟通或更改内容..." />
          </el-form-item>
        </el-form>
      </template>
      <template v-else>
        <el-alert type="success" :title="'已生成版本 ' + confirmVersion" show-icon style="margin-bottom:16px" />
        <el-form>
          <el-form-item label="确认链接">
            <el-input :model-value="confirmLink" readonly>
              <template #append>
                <el-button @click="copyLink">复制</el-button>
              </template>
            </el-input>
          </el-form-item>
        </el-form>
        <p style="color:#999;font-size:12px">客户打开此链接可查看工艺单并确认，无需登录。</p>
      </template>
      <template #footer>
        <template v-if="!confirmLink">
          <el-button @click="showMarkDialog = false">取消</el-button>
          <el-button type="primary" @click="confirmMarkVersion" :loading="markingVersion">确认</el-button>
        </template>
        <template v-else>
          <el-button type="primary" @click="showMarkDialog = false">完成</el-button>
        </template>
      </template>
    </el-dialog>

    <!-- 设置确认人对话框 -->
    <el-dialog v-model="showConfirmUsersDialog" title="设置内部确认人" width="560px">
      <p style="color:#666;margin-bottom:12px">选择需要确认本工艺单的用户，客户确认后将自动通知以下人员。</p>
      <el-checkbox-group v-model="selectedConfirmUserIds">
        <el-checkbox v-for="u in allUsers" :key="u.id" :label="u.id" style="display:flex;margin-bottom:8px">
          {{ u.display_name || u.username }}
          <el-tag size="small" style="margin-left:6px">{{ u.role }}</el-tag>
        </el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="showConfirmUsersDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingConfirmUsers" @click="handleSaveConfirmUsers">保存</el-button>
      </template>
    </el-dialog>

    <!-- 更改原因对话框（版本已标记后每次保存需要） -->
    <el-dialog v-model="showChangeNoteDialog" title="更改原因" width="420px" :close-on-click-modal="false" :show-close="false">
      <p style="margin-bottom:12px;color:#666">版本已标记用于客户沟通，请说明本次更改原因：</p>
      <el-input v-model="changeNote" type="textarea" :rows="3" placeholder="请描述更改原因..." />
      <template #footer>
        <el-button type="primary" @click="confirmChangeNote" :disabled="!changeNote.trim()">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getSheet, confirmSheet, dispatchSheet, updateSheetDetail, markVersion, getSheetLogs, generateConfirmLink, internalConfirmSheet, reopenSheetEdit, setConfirmUsers, printSheet, forceConfirmSheet } from '../../api/processSheet'
import { usePermissionStore } from '../../store/permissions'
import { listSpecs } from '../../api/spec'
import { listUsers } from '../../api/user'
import { listBasicData, getColorMapping } from '../../api/basicData'
import { uploadImages } from '../../api/upload'
import StatusLog from '../../components/StatusLog.vue'

const route = useRoute()
const permStore = usePermissionStore()
const sheet = ref(null)
const specs = ref([])
const packagingTypes = ref([])
const colorMapping = ref({})
const loading = ref(false)
const loadingLogs = ref(false)
const customerConfirmedFromLog = computed(() => {
  return logs.value.filter(l => l.remark?.includes('客户确认'))
})
const commEvents = computed(() => {
  return logs.value.filter(l => l.remark?.includes('客户沟通标记'))
})
const reopenEvents = computed(() => {
  return logs.value.filter(l => l.operation_type === '重新编辑')
})

const contractVersionMatch = computed(() => {
  if (!sheet.value?.contract_snapshot?.latest_confirm_version) return null
  const snapshotVer = Number(sheet.value.contract_snapshot.latest_confirm_version)
  const currentVer = Number(sheet.value?.contract?.latest_confirm_version)
  if (currentVer === undefined || isNaN(currentVer)) return null
  return { snapshot: snapshotVer, current: currentVer, match: snapshotVer === currentVer }
})
const logs = ref([])

const internalConfirmCount = computed(() => {
  return sheet.value?.internal_confirmed_users?.length || 0
})

const canInternalConfirm = computed(() => {
  return permStore.hasPermission('sheet:internal_confirm')
})

const canReopenEdit = computed(() => {
  return permStore.hasPermission('sheet:reopen_edit')
})

async function loadLogs() {
  try {
    const res = await getSheetLogs(route.params.id)
    logs.value = res.data
  } catch { logs.value = [] }
}

// Items and detail data (reactive copies for editing)
const items = ref([])
const detailData = reactive({})
const extraTechNoteCount = ref(0)
const extraPackNoteCount = ref(0)
const extraBoxNoteCount = ref(0)

function addTechNote() {
  extraTechNoteCount.value++
  const key = 5 + extraTechNoteCount.value
  if (!detailData[`tech_note_${key}`]) {
    detailData[`tech_note_${key}`] = ''
  }
}

function addPackNote() {
  extraPackNoteCount.value++
  const key = 3 + extraPackNoteCount.value
  if (!detailData[`pack_note_${key}`]) {
    detailData[`pack_note_${key}`] = ''
  }
}

function addBoxNote() {
  extraBoxNoteCount.value++
  const key = 2 + extraBoxNoteCount.value
  if (!detailData[`box_note_${key}`]) {
    detailData[`box_note_${key}`] = ''
  }
}

// Detail dialog state
const showDetailDialog = ref(false)
const activeIdx = ref(0)
const patternUploadRefs = reactive({})
const embossUploadRef = ref(null)
const accRefs = reactive({})
const subRefs = reactive({})

// Version management
const showMarkDialog = ref(false)
const markNote = ref('')
const markingVersion = ref(false)
const confirmLink = ref('')
const confirmVersion = ref('')
const showChangeNoteDialog = ref(false)
const changeNote = ref('')
let changeNoteResolve = null

// Confirm user management
const showConfirmUsersDialog = ref(false)
const allUsers = ref([])
const selectedConfirmUserIds = ref([])
const savingConfirmUsers = ref(false)

function askChangeNote() {
  return new Promise((resolve) => {
    changeNoteResolve = resolve
    changeNote.value = ''
    showChangeNoteDialog.value = true
  })
}

function confirmChangeNote() {
  if (changeNoteResolve) changeNoteResolve(changeNote.value)
  showChangeNoteDialog.value = false
  changeNoteResolve = null
}

function formatVersion(v) {
  if (v === null || v === undefined || Number(v) === 0) return ''
  const num = Number(v)
  if (num % 1 === 0) return `V${num}`
  return `V${parseFloat(num.toFixed(2))}`
}

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

function getSpecName(specId) {
  const spec = specs.value.find(s => s.id === specId)
  return spec ? spec.spec_description || spec.spec_name : `规格#${specId}`
}

function getPatternLabel(index, item) {
  const spec = specs.value.find(s => s.id === item.spec_id)
  const isComposite = spec?.layer_type?.includes('复合')
  if (isComposite) {
    const num = Math.floor(index / 2) + 1
    const suffix = index % 2 === 0 ? 'A' : 'B'
    return `花型代码${num}${suffix}`
  }
  return `花型代码${index + 1}`
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
    detailData.tech_note_1 = `请注意尺寸和重量控制:${spec.length}*${spec.width}cm,重量:${spec.weight}-3%~+1%之间`
  } else {
    detailData.tech_note_1 = '请注意尺寸和重量控制'
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
    if (res.data?.[0]) {
      activeItem.value.pressed_image = res.data[0].url
      activeItem.value.pressed_image_name = res.data[0].original_name || file.name
    }
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
    // Auto-fill qty from contract item qty if empty
    if (!detailData[`accessory_qty_${key}`] && activeItem.value?.qty) {
      detailData[`accessory_qty_${key}`] = activeItem.value.qty
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
      // Auto-fill qty from contract item qty if empty
      if (arr?.[idx] && !arr[idx].qty && activeItem.value?.qty) {
        arr[idx].qty = activeItem.value.qty
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
  if (!detailData.pack_note_1) {
    const pkg = items.value[index]?.packaging_type || '包装'
    detailData.pack_note_1 = `每${pkg}条毛毯+只钢丝插好彩页`
  }
  // Set default binding material and width
  if (!detailData.binding_material) {
    detailData.binding_material = '110gsm针织布'
  }
  if (!detailData.binding_width) {
    const spec = specs.value.find(s => s.id === items.value[index]?.spec_id)
    detailData.binding_width = spec?.layer_type?.includes('复合') ? '8cm' : '5cm'
  }
  showDetailDialog.value = true
}

function removeItem(index) {
  items.value.splice(index, 1)
}

async function saveItemDetail() {
  const item = activeItem.value
  if (!item) return

  // Validate packaging type
  if (!item.packaging_type) {
    ElMessage.warning('请选择包装方式')
    return
  }

  // Validate binding fields (required unless 打卷面料)
  if (item.packaging_type !== '打卷面料') {
    if (!detailData.binding_material?.trim()) {
      ElMessage.warning('请填写包边材料')
      return
    }
    if (!detailData.binding_width?.trim()) {
      ElMessage.warning('请填写包边宽度')
      return
    }
    if (!item.pattern_count || item.pattern_count <= 0) {
      ElMessage.warning('请设置花型个数')
      return
    }
  }

  // Validate pattern rows
  if (item.pattern_data?.length > 0) {
    for (let i = 0; i < item.pattern_data.length; i++) {
      const p = item.pattern_data[i]
      if (!p.code?.trim()) {
        ElMessage.warning(`第 ${i + 1} 个花型代码不能为空`)
        return
      }
      if (!p.color) {
        ElMessage.warning(`第 ${i + 1} 个花型颜色不能为空`)
        return
      }
      if (!p.qty || p.qty <= 0) {
        ElMessage.warning(`第 ${i + 1} 个花型数量必须大于 0`)
        return
      }
    }
  }

  // Fill accessory descriptions from group labels
  for (const grp of accessoryGroups) {
    const key = grp.key
    const hasData = detailData[`accessory_size_${key}`] || detailData[`accessory_qty_${key}`] || detailData[`accessory_images_${key}`]?.length
    if (hasData && !detailData[`accessory_desc_${key}`]) {
      detailData[`accessory_desc_${key}`] = grp.label
    }
  }
  // Persist to backend
  try {
    let change_note = undefined
    if (sheet.value?.version_marked) {
      change_note = await askChangeNote()
    }
    const payload = {
      detail_data: { ...detailData },
      items: items.value.map(i => ({
        id: i.id,
        is_pressed: i.is_pressed,
        packaging_type: i.packaging_type || '',
        delivery_date: i.delivery_date,
        pattern_count: i.pattern_count || 0,
        pattern_data: i.pattern_data || [],
        pattern_code: i.pattern_code || '',
        color_a: i.color_a || '',
        image_a_1: i.image_a_1 || '',
        image_a_2: i.image_a_2 || '',
        image_a_3: i.image_a_3 || '',
        color_b: i.color_b || '',
        image_b_1: i.image_b_1 || '',
        image_b_2: i.image_b_2 || '',
        image_b_3: i.image_b_3 || '',
        pressed_image: i.pressed_image || '',
        pressed_image_name: i.pressed_image_name || '',
        process_remark: i.process_remark || '',
        remark: i.remark || '',
        qty: i.qty,
      })),
      change_note,
    }
    await updateSheetDetail(route.params.id, payload)
    ElMessage.success('保存成功')
    showDetailDialog.value = false
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  }
}

// --- Sheet operations ---
async function confirmMarkVersion() {
  markingVersion.value = true
  try {
    const res = await markVersion(route.params.id, { note: markNote.value })
    confirmVersion.value = formatVersion(res.data.confirm_version_no)

    // Generate confirm link
    const linkRes = await generateConfirmLink(route.params.id)
    const origin = window.location.origin
    confirmLink.value = `${origin}/confirm/${linkRes.data.token}`
    copyLink()

    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
  finally { markingVersion.value = false }
}

function copyLink() {
  navigator.clipboard.writeText(confirmLink.value)
  ElMessage.success('确认链接已复制到剪贴板')
}

async function handleConfirm() {
  // First save the current detail data, then confirm
  try {
    let change_note = undefined
    if (sheet.value?.version_marked) {
      change_note = await askChangeNote()
    }
    // Fill accessory descriptions from group labels
    for (const grp of accessoryGroups) {
      const key = grp.key
      const hasData = detailData[`accessory_size_${key}`] || detailData[`accessory_qty_${key}`] || detailData[`accessory_images_${key}`]?.length
      if (hasData && !detailData[`accessory_desc_${key}`]) {
        detailData[`accessory_desc_${key}`] = grp.label
      }
    }
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
        process_remark: item.process_remark || '',
        remark: item.remark || '',
        qty: item.qty,
      })),
      change_note,
    }
    await updateSheetDetail(route.params.id, payload)

    // Then confirm
    const res = await confirmSheet(route.params.id)
    ElMessage.success(`客户已确认，正式版本 ${formatVersion(res.data.confirm_version_no)}`)
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

async function handleInternalConfirm() {
  try {
    await internalConfirmSheet(route.params.id)
    ElMessage.success('内部确认成功')
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
}

async function handleForceConfirm() {
  try {
    await forceConfirmSheet(route.params.id)
    ElMessage.success('强制通过成功')
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
}

async function handleReopenEdit() {
  try {
    await reopenSheetEdit(route.params.id)
    ElMessage.success('已重新打开编辑')
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
}

async function handleOpenConfirmUsers() {
  try {
    if (!allUsers.value.length) {
      const res = await listUsers()
      allUsers.value = res.data
    }
    selectedConfirmUserIds.value = [...(sheet.value?.confirm_user_ids || [])]
    showConfirmUsersDialog.value = true
  } catch { ElMessage.error('加载用户列表失败') }
}

async function handleSaveConfirmUsers() {
  savingConfirmUsers.value = true
  try {
    await setConfirmUsers(route.params.id, selectedConfirmUserIds.value)
    ElMessage.success('确认人设置已保存')
    showConfirmUsersDialog.value = false
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '保存失败') }
  finally { savingConfirmUsers.value = false }
}

watch(showConfirmUsersDialog, (val) => {
  if (!val) return
  if (!allUsers.value.length) {
    listUsers().then(res => { allUsers.value = res.data }).catch(() => {})
  }
  selectedConfirmUserIds.value = [...(sheet.value?.confirm_user_ids || [])]
})

async function handlePrint() {
  try {
    const res = await printSheet(route.params.id)
    const blob = new Blob([res.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${sheet.value?.sheet_no || 'process-sheet'}.pdf`
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (e) { ElMessage.error('打印失败') }
}

async function loadData() {
  loading.value = true
  try {
    const res = await getSheet(route.params.id)
    sheet.value = res.data
    // Deep-copy items and detail_data for editing
    items.value = JSON.parse(JSON.stringify(res.data.items || []))
    const dd = res.data.detail_data || {}
    // Count existing extra tech notes
    const maxTechNote = Math.max(...Object.keys(dd).filter(k => /^tech_note_\d+$/.test(k)).map(k => parseInt(k.split('_')[2])).filter(n => n > 5), 5)
    extraTechNoteCount.value = Math.max(0, maxTechNote - 5)
    // Copy extra tech note values into detailData directly
    for (let i = 6; i <= maxTechNote; i++) {
      if (dd[`tech_note_${i}`]) {
        detailData[`tech_note_${i}`] = dd[`tech_note_${i}`]
      }
    }

    // Count existing extra pack notes
    const maxPackNote = Math.max(...Object.keys(dd).filter(k => /^pack_note_\d+$/.test(k)).map(k => parseInt(k.split('_')[2])).filter(n => n > 3), 3)
    extraPackNoteCount.value = Math.max(0, maxPackNote - 3)
    for (let i = 4; i <= maxPackNote; i++) {
      if (dd[`pack_note_${i}`]) {
        detailData[`pack_note_${i}`] = dd[`pack_note_${i}`]
      }
    }

    // Count existing extra box notes
    const maxBoxNote = Math.max(...Object.keys(dd).filter(k => /^box_note_\d+$/.test(k)).map(k => parseInt(k.split('_')[2])).filter(n => n > 2), 2)
    extraBoxNoteCount.value = Math.max(0, maxBoxNote - 2)
    for (let i = 3; i <= maxBoxNote; i++) {
      if (dd[`box_note_${i}`]) {
        detailData[`box_note_${i}`] = dd[`box_note_${i}`]
      }
    }

    Object.assign(detailData, {
      binding_material: dd.binding_material || '',
      binding_width: dd.binding_width || '',
      binding_color_no: dd.binding_color_no || '',
      tolerance: dd.tolerance || '1',
      tech_note_1: dd.tech_note_1 || '',
      tech_note_2: dd.tech_note_2 || '质量要求,手感厚实,毛面爽滑光亮,不掉毛.',
      tech_note_3: dd.tech_note_3 || '缝制要求:每条毛毯缝制一个洗标和一个产地标,洗标缝在繁忙长边左下角距边20cm处,产地标重叠缝制在下面',
      tech_note_4: dd.tech_note_4 || '辅料:',
      tech_note_5: dd.tech_note_5 || '贴纸贴在抽真空包装上,拆卡插入钢丝包的内插袋口袋',
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
      pack_note_2: dd.pack_note_2 || '花型分配:',
      pack_note_3: dd.pack_note_3 || '',
      box_note_1: dd.box_note_1 || '？个柜,？包/柜',
      box_note_2: dd.box_note_2 || '',
    })
  } catch { ElMessage.error('加载失败') }
  finally {
    loading.value = false
    loadLogs()
  }
}

watch(showMarkDialog, (val) => {
  if (val) {
    confirmLink.value = ''
    confirmVersion.value = ''
  }
})

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
  await loadData()
  if (!detailData.tech_note_1) updateTechNote1()
  loadLogs()
})
</script>
