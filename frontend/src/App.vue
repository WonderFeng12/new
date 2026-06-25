<template>
  <router-view v-if="isLogin" />
  <el-container v-else style="height:100vh">
    <el-aside width="220px" style="background:#304156">
      <div class="logo">花织工厂管理系统</div>
      <el-menu
        :default-active="route.path"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item v-if="showContracts" index="/contracts">
          <el-icon><Document /></el-icon>
          <span>合同管理</span>
        </el-menu-item>
        <el-menu-item index="/process-sheets">
          <el-icon><List /></el-icon>
          <span>工艺单管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="background:#fff;border-bottom:1px solid #e6e6e6;display:flex;align-items:center;justify-content:space-between">
        <span></span>
        <el-dropdown @command="handleCommand">
          <span style="cursor:pointer">
            {{ store.user?.display_name || store.username }}
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-main style="background:#f0f2f5;padding:20px">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from './store/user'

const route = useRoute()
const router = useRouter()
const store = useUserStore()

const isLogin = computed(() => route.path === '/login')
const showContracts = computed(() => store.role !== '生产专员')

function handleCommand(cmd) {
  if (cmd === 'logout') {
    store.logout()
    router.push('/login')
  }
}
</script>

<style>
* { margin:0; padding:0; box-sizing:border-box; }
html, body, #app { height:100%; width:100%; font-family:'Helvetica Neue',Helvetica,'PingFang SC','Microsoft YaHei',sans-serif; }
.logo { height:60px; line-height:60px; text-align:center; color:#fff; font-size:14px; font-weight:bold; letter-spacing:1px; border-bottom:1px solid #1f2d3d; }
.el-header { height:60px; padding:0 20px; }
.el-menu { border-right:none; }
</style>
