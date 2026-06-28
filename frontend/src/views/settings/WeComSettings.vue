<template>
  <div>
    <h2>企业微信通知设置</h2>
    <el-card style="margin:16px 0;max-width:600px">
      <el-form label-width="160px">
        <el-form-item label="群机器人 Webhook URL">
          <el-input v-model="form.webhook_url" placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..." />
        </el-form-item>
        <el-form-item label="启用生产通知">
          <el-switch v-model="form.notify_enabled" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <h3 style="margin-top:24px">用户企业微信绑定</h3>
    <el-table :data="users" stripe size="small" style="max-width:600px">
      <el-table-column prop="display_name" label="用户" width="120" />
      <el-table-column prop="role" label="角色" width="100" />
      <el-table-column label="企业微信 UserID" min-width="200">
        <template #default="{ row }">
          <el-input v-model="row.wecom_userid" size="small" placeholder="未绑定" @change="handleUpdateWecom(row)" />
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getWecomSettings, updateWecomSettings } from '../../api/production'
import { listUsers } from '../../api/user'
import { ElMessage } from 'element-plus'

const form = ref({ webhook_url: '', notify_enabled: false })
const users = ref([])
const saving = ref(false)

async function handleSave() {
  saving.value = true
  try {
    await updateWecomSettings({
      wecom_webhook_url: form.value.webhook_url,
      production_notify_enabled: form.value.notify_enabled ? 'true' : 'false',
    })
    ElMessage.success('保存成功')
  } catch (e) { ElMessage.error(e.response?.data?.detail || '保存失败') }
  finally { saving.value = false }
}

async function handleUpdateWecom(user) {
  // WeCom binding is done by each user via the /users/me/wecom endpoint
  // This shows current binding status for reference
}

async function loadData() {
  try {
    const [sRes, uRes] = await Promise.all([
      getWecomSettings(),
      listUsers(),
    ])
    form.value.webhook_url = sRes.data.wecom_webhook_url || ''
    form.value.notify_enabled = sRes.data.production_notify_enabled === 'true'
    users.value = uRes.data
  } catch { ElMessage.error('加载失败') }
}

onMounted(loadData)
</script>
