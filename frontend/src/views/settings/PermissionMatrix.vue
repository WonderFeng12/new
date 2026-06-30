<template>
  <div>
    <h2>角色权限</h2>
    <p style="color:#666;margin:8px 0 16px">
      自由组合每个角色拥有的权限。取消勾选后保存，对应角色的功能入口和操作按钮将自动隐藏。
    </p>

    <el-card v-loading="loading">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>权限矩阵</span>
          <div>
            <el-button @click="selectAllForRole('业务员')">业务员全选</el-button>
            <el-button @click="selectAllForRole('销售经理')">销售经理全选</el-button>
            <el-button @click="selectAllForRole('生产专员')">生产专员全选</el-button>
            <el-button @click="selectAllForRole('外协人员')">外协人员全选</el-button>
            <el-button @click="selectAllForRole('管理员')">管理员全选</el-button>
          </div>
        </div>
      </template>

      <el-table :data="flatRows" stripe size="small" style="width:100%">
        <el-table-column label="权限" min-width="260">
          <template #default="{ row }">
            <div v-if="row._isGroup" style="font-weight:bold;color:#409eff;font-size:14px;padding:6px 0">
              {{ row.module }}
            </div>
            <div v-else style="padding-left:24px">
              {{ row.label }}
            </div>
          </template>
        </el-table-column>
        <el-table-column v-for="role in roles" :key="role" :label="role" width="100" align="center" header-align="center">
          <template #default="{ row }">
            <el-checkbox
              v-if="!row._isGroup"
              :model-value="getPerm(role, row.key)"
              @change="(val) => togglePerm(role, row.key, val)"
            />
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top:16px;display:flex;gap:12px">
        <el-button type="primary" :loading="saving" @click="handleSave">保存权限配置</el-button>
        <el-button @click="loadData">重置</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  getPermissionDefinitions,
  getAllPermissions,
  updatePermissions,
} from '../../api/permissions'
import { ElMessage } from 'element-plus'

const roles = ['业务员', '销售经理', '生产专员', '外协人员', '管理员']
const loading = ref(false)
const saving = ref(false)
const definitions = ref([])
const rolePerms = ref({})

const flatRows = ref([])

function getPerm(role, permKey) {
  const list = rolePerms.value[role] || []
  return list.includes(permKey)
}

function togglePerm(role, permKey, val) {
  if (!rolePerms.value[role]) rolePerms.value[role] = []
  const list = rolePerms.value[role]
  if (val) {
    if (!list.includes(permKey)) list.push(permKey)
  } else {
    rolePerms.value[role] = list.filter((p) => p !== permKey)
  }
}

function selectAllForRole(role) {
  const allKeys = definitions.value.flatMap((m) =>
    m.permissions.map((p) => p.key)
  )
  rolePerms.value[role] = [...allKeys]
}

function buildFlatRows() {
  const rows = []
  for (const mod of definitions.value) {
    rows.push({ _isGroup: true, module: mod.module })
    for (const perm of mod.permissions) {
      rows.push({ key: perm.key, label: perm.label, module: mod.module })
    }
  }
  return rows
}

async function loadData() {
  loading.value = true
  try {
    const [defRes, permRes] = await Promise.all([
      getPermissionDefinitions(),
      getAllPermissions(),
    ])
    definitions.value = defRes.data || []

    const raw = permRes.data?.roles || permRes.data || {}
    // Deep-clone so we can mutate freely
    rolePerms.value = {}
    for (const role of roles) {
      rolePerms.value[role] = [...(raw[role] || [])]
    }
    flatRows.value = buildFlatRows()
  } catch (e) {
    ElMessage.error('加载权限配置失败')
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    await updatePermissions(rolePerms.value)
    ElMessage.success('权限配置已更新')
    // reload so cache is fresh
    await loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(loadData)
</script>
