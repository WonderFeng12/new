<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2>用户管理</h2>
      <el-button type="primary" @click="openCreate">新增用户</el-button>
    </div>

    <el-card v-loading="loading">
      <el-table :data="users" stripe size="small">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="display_name" label="显示名称" width="120" />
        <el-table-column prop="role" label="角色" width="110">
          <template #default="{ row }">
            <el-tag :type="roleType(row.role)" size="small">{{ row.role }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="企微 UserID" min-width="180">
          <template #default="{ row }">
            {{ row.wecom_userid || '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" @click="openResetPwd(row)">重置密码</el-button>
            <el-popconfirm title="确定删除此用户？" @confirm="handleDelete(row)">
              <template #reference>
                <el-button size="small" type="danger" :disabled="row.id === currentUserId">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Create/Edit dialog -->
    <el-dialog v-model="formVisible" :title="isEditing ? '编辑用户' : '新增用户'" width="480px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="用户名" v-if="!isEditing">
          <el-input v-model="form.username" placeholder="登录名" />
        </el-form-item>
        <el-form-item label="密码" v-if="!isEditing">
          <el-input v-model="form.password" type="password" placeholder="初始密码" show-password />
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="form.display_name" placeholder="显示名称" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role" style="width:100%">
            <el-option label="业务员" value="业务员" />
            <el-option label="销售经理" value="销售经理" />
            <el-option label="生产专员" value="生产专员" />
            <el-option label="外协人员" value="外协人员" />
          </el-select>
        </el-form-item>
        <el-form-item label="企业微信 UserID">
          <el-input v-model="form.wecom_userid" placeholder="企微用户ID（用于@提醒）" />
          <div style="font-size:12px;color:#999;margin-top:4px">
            在企微通讯录中查看自己账号详情，复制 UserID 填入。配置后合同请求确认时会自动 @该用户。
          </div>
        </el-form-item>
        <el-form-item label="启用" v-if="isEditing">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- Reset password dialog -->
    <el-dialog v-model="pwdVisible" title="重置密码" width="400px">
      <el-form>
        <el-form-item label="新密码">
          <el-input v-model="newPassword" type="password" show-password placeholder="输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleResetPwd">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { listUsers, createUser, updateUser, resetPassword, deleteUser } from '../../api/user'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const users = ref([])
const formVisible = ref(false)
const isEditing = ref(false)
const saving = ref(false)
const form = ref({ username: '', password: '', display_name: '', role: '业务员', wecom_userid: '', is_active: true })
const editId = ref(null)

const pwdVisible = ref(false)
const resetUserId = ref(null)
const resetUserName = ref('')
const newPassword = ref('')

const currentUserId = computed(() => {
  try {
    const token = localStorage.getItem('token')
    const payload = JSON.parse(atob(token.split('.')[1]))
    return Number(payload.sub)
  } catch { return null }
})

function roleType(role) {
  if (role === '销售经理') return 'danger'
  if (role === '生产专员') return 'primary'
  if (role === '外协人员') return 'warning'
  return ''
}

function openCreate() {
  isEditing.value = false
  editId.value = null
  form.value = { username: '', password: '', display_name: '', role: '业务员', wecom_userid: '', is_active: true }
  formVisible.value = true
}

function openEdit(row) {
  isEditing.value = true
  editId.value = row.id
  form.value = {
    username: row.username,
    password: '',
    display_name: row.display_name,
    role: row.role,
    wecom_userid: row.wecom_userid || '',
    is_active: row.is_active,
  }
  formVisible.value = true
}

function openResetPwd(row) {
  resetUserId.value = row.id
  resetUserName.value = row.display_name
  newPassword.value = ''
  pwdVisible.value = true
}

async function handleSave() {
  if (!isEditing.value && (!form.value.username || !form.value.password)) {
    ElMessage.warning('用户名和密码不能为空')
    return
  }
  if (!form.value.display_name) {
    ElMessage.warning('显示名称不能为空')
    return
  }
  saving.value = true
  try {
    if (isEditing.value) {
      await updateUser(editId.value, {
        display_name: form.value.display_name,
        role: form.value.role,
        wecom_userid: form.value.wecom_userid || null,
        is_active: form.value.is_active,
      })
      ElMessage.success('用户已更新')
    } else {
      await createUser({
        username: form.value.username,
        password: form.value.password,
        display_name: form.value.display_name,
        role: form.value.role,
      })
      ElMessage.success('用户已创建')
    }
    formVisible.value = false
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '保存失败') }
  finally { saving.value = false }
}

async function handleResetPwd() {
  if (!newPassword.value) {
    ElMessage.warning('请输入新密码')
    return
  }
  saving.value = true
  try {
    await resetPassword(resetUserId.value, { password: newPassword.value })
    ElMessage.success('密码已重置')
    pwdVisible.value = false
  } catch (e) { ElMessage.error(e.response?.data?.detail || '重置失败') }
  finally { saving.value = false }
}

async function handleDelete(row) {
  try {
    await deleteUser(row.id)
    ElMessage.success('已删除')
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '删除失败') }
}

async function loadData() {
  loading.value = true
  try {
    const res = await listUsers()
    users.value = res.data
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

onMounted(loadData)
</script>
