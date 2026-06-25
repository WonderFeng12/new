<template>
  <div>
    <h2>欢迎回来，{{ store.user?.display_name || store.username }}</h2>
    <p style="color:#999;margin-bottom:20px">当前角色: {{ roleLabel }}</p>

    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">我的合同</div>
            <div class="stat-num">{{ stats.myContracts }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">待确认合同</div>
            <div class="stat-num warning">{{ stats.pendingConfirm }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">工艺单数</div>
            <div class="stat-num">{{ stats.sheets }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">本月新合同</div>
            <div class="stat-num primary">{{ stats.monthContracts }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top:24px">
      <el-col :span="12">
        <el-card>
          <template #header>快捷操作</template>
          <el-button type="primary" style="width:100%;margin-bottom:8px" @click="$router.push('/contracts/new')">新建合同</el-button>
          <el-button style="width:100%;margin-bottom:8px" @click="$router.push('/contracts')">合同列表</el-button>
          <el-button style="width:100%" @click="$router.push('/process-sheets')">工艺单列表</el-button>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>系统信息</template>
          <el-descriptions :column="1" size="small">
            <el-descriptions-item label="版本">v1.0.0</el-descriptions-item>
            <el-descriptions-item label="当前用户">{{ store.user?.display_name || store.username }}</el-descriptions-item>
            <el-descriptions-item label="角色">{{ roleLabel }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../../store/user'
import { listContracts } from '../../api/contract'
import { listSheets } from '../../api/processSheet'

const store = useUserStore()

const roleLabel = computed(() => {
  const map = { '业务员': '业务员', '销售经理': '销售经理', '生产专员': '生产专员' }
  return map[store.role] || store.role
})

const stats = ref({ myContracts: 0, pendingConfirm: 0, sheets: 0, monthContracts: 0 })

onMounted(async () => {
  try {
    const [cRes, sRes] = await Promise.all([
      listContracts({ keyword: '' }),
      listSheets({ keyword: '' }),
    ])
    const allContracts = cRes.data
    const now = new Date()
    const thisMonth = now.getMonth()
    const thisYear = now.getFullYear()
    stats.value = {
      myContracts: allContracts.length,
      pendingConfirm: allContracts.filter(c => c.status === '草稿').length,
      sheets: sRes.data.length,
      monthContracts: allContracts.filter(c => {
        const d = new Date(c.created_at)
        return d.getMonth() === thisMonth && d.getFullYear() === thisYear
      }).length,
    }
  } catch {}
})
</script>

<style scoped>
.stat-item { text-align: center; }
.stat-label { font-size: 14px; color: #666; margin-bottom: 8px; }
.stat-num { font-size: 32px; font-weight: bold; color: #333; }
.stat-num.warning { color: #e6a23c; }
.stat-num.primary { color: #409eff; }
</style>
