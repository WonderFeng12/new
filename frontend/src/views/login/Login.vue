<template>
  <div style="display:flex;height:100vh;align-items:center;justify-content:center;background:#f0f2f5">
    <el-card style="width:400px">
      <h2 style="text-align:center;margin-bottom:8px;">嘉元瑞通工厂管理系统</h2>
      <p style="text-align:center;color:#999;font-size:14px;margin-bottom:24px;">请登录您的账户</p>
      <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" size="large" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" size="large" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" style="width:100%" size="large" :loading="loading" native-type="submit">登 录</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../../store/user'
import { usePermissionStore } from '../../store/permissions'
import { login } from '../../api/auth'

const router = useRouter()
const store = useUserStore()
const permStore = usePermissionStore()
const formRef = ref(null)
const loading = ref(false)
const submitting = ref(false)
const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const handleLogin = async () => {
  if (submitting.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  loading.value = true
  try {
    const res = await login(form)
    store.setToken(res.data.access_token)
    store.user = res.data.user
    permStore.reset()
    await permStore.fetchMyPermissions()
    await router.push('/dashboard')
    ElMessage.success('登录成功')
  } catch (err) {
    if (err.response?.status === 401) {
      ElMessage.error('用户名或密码错误')
    } else {
      ElMessage.error(err.response?.data?.detail || '登录失败')
    }
  } finally {
    submitting.value = false
    loading.value = false
  }
}
</script>
