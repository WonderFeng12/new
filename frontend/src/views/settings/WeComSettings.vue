<template>
  <div>
    <h2>企业微信通知设置</h2>
    <p style="color:#666;margin:8px 0 16px">
      配置企业微信群机器人，用于发送合同确认通知和工艺单生产进度通知。
      可添加多个webhook，分别用于不同类型的通知。
    </p>

    <el-card v-loading="loading" style="max-width:800px">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>Webhook 列表</span>
          <el-button type="primary" size="small" @click="openCreate">新增 Webhook</el-button>
        </div>
      </template>

      <el-table :data="webhooks" stripe empty-text="暂无 webhook 配置">
        <el-table-column prop="name" label="名称" width="140">
          <template #default="{ row }">
            <el-tag size="small">{{ row.name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="webhook_url" label="Webhook URL" min-width="300" show-overflow-tooltip />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_enabled ? 'success' : 'info'" size="small">
              {{ row.is_enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-popconfirm title="确定删除此 webhook？" @confirm="handleDelete(row)">
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top:16px;padding:12px;background:#f5f7fa;border-radius:4px;font-size:13px;color:#666">
        <strong>提示：</strong><br>
        • <strong>合同通知</strong> — 用于发送合同确认请求和每日催办提醒 @销售经理<br>
        • <strong>工艺单通知</strong> — 用于发送坯布计划下达、生产进度推进、取消、完成等通知<br>
        如需其他通知，可添加自定义名称的 webhook（暂未使用）
      </div>
    </el-card>

    <!-- Create/Edit dialog -->
    <el-dialog v-model="formVisible" :title="isEditing ? '编辑 Webhook' : '新增 Webhook'" width="550px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="名称">
          <el-select v-model="form.name" style="width:100%" :disabled="isEditing">
            <el-option label="合同通知" value="合同通知" />
            <el-option label="工艺单通知" value="工艺单通知" />
            <el-option label="自定义" value="__custom__" />
          </el-select>
          <el-input v-if="form.name === '__custom__'" v-model="form.customName" placeholder="输入自定义名称" style="margin-top:8px" />
        </el-form-item>
        <el-form-item label="Webhook URL">
          <el-input v-model="form.webhook_url" type="textarea" :rows="2"
            placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..." />
          <div style="font-size:12px;color:#999;margin-top:4px">
            在企业微信群 → 群设置 → 群机器人 → 添加机器人后获取
          </div>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listWebhooks, createWebhook, updateWebhook, deleteWebhook } from '../../api/webhookConfig'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const webhooks = ref([])
const formVisible = ref(false)
const isEditing = ref(false)
const saving = ref(false)
const editId = ref(null)
const form = ref({ name: '', customName: '', webhook_url: '', is_enabled: true })

function openCreate() {
  isEditing.value = false
  editId.value = null
  form.value = { name: '', customName: '', webhook_url: '', is_enabled: true }
  formVisible.value = true
}

function openEdit(row) {
  isEditing.value = true
  editId.value = row.id
  form.value = {
    name: row.name,
    customName: '',
    webhook_url: row.webhook_url,
    is_enabled: row.is_enabled,
  }
  formVisible.value = true
}

async function handleSave() {
  const name = form.value.name === '__custom__' ? form.value.customName : form.value.name
  if (!name || !name.trim()) {
    ElMessage.warning('请输入名称')
    return
  }
  if (!form.value.webhook_url) {
    ElMessage.warning('请输入 Webhook URL')
    return
  }
  saving.value = true
  try {
    if (isEditing.value) {
      await updateWebhook(editId.value, {
        webhook_url: form.value.webhook_url,
        is_enabled: form.value.is_enabled,
      })
      ElMessage.success('已更新')
    } else {
      await createWebhook({ name, webhook_url: form.value.webhook_url, is_enabled: form.value.is_enabled })
      ElMessage.success('已创建')
    }
    formVisible.value = false
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '保存失败') }
  finally { saving.value = false }
}

async function handleDelete(row) {
  try {
    await deleteWebhook(row.id)
    ElMessage.success('已删除')
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '删除失败') }
}

async function loadData() {
  loading.value = true
  try {
    const res = await listWebhooks()
    webhooks.value = res.data
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

onMounted(loadData)
</script>
