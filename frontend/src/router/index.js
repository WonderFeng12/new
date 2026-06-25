import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', component: () => import('../views/login/Login.vue') },
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: () => import('../views/dashboard/Dashboard.vue') },
  { path: '/contracts', component: () => import('../views/contract/ContractList.vue') },
  { path: '/contracts/new', component: () => import('../views/contract/ContractForm.vue') },
  { path: '/contracts/:id', component: () => import('../views/contract/ContractDetail.vue') },
  { path: '/contracts/:id/edit', component: () => import('../views/contract/ContractForm.vue') },
  { path: '/process-sheets', component: () => import('../views/processSheet/SheetList.vue') },
  { path: '/process-sheets/:id', component: () => import('../views/processSheet/SheetDetail.vue') },
]

const router = createRouter({ history: createWebHistory(), routes })
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) next('/login')
  else next()
})
export default router
