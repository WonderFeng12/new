import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', component: () => import('../views/login/Login.vue') },
  { path: '/', redirect: '/dashboard' },
  {
    path: '/dashboard',
    component: () => import('../views/dashboard/Dashboard.vue'),
    meta: { roles: ['业务员', '销售经理', '生产专员'] },
  },
  {
    path: '/contracts',
    component: () => import('../views/contract/ContractList.vue'),
    meta: { roles: ['业务员', '销售经理'] },
  },
  {
    path: '/contracts/new',
    component: () => import('../views/contract/ContractForm.vue'),
    meta: { roles: ['业务员', '销售经理'] },
  },
  {
    path: '/contracts/:id',
    component: () => import('../views/contract/ContractDetail.vue'),
    meta: { roles: ['业务员', '销售经理'] },
  },
  {
    path: '/contracts/:id/edit',
    component: () => import('../views/contract/ContractForm.vue'),
    meta: { roles: ['业务员', '销售经理'] },
  },
  {
    path: '/customers',
    component: () => import('../views/customer/CustomerList.vue'),
    meta: { roles: ['业务员', '销售经理'] },
  },
  {
    path: '/specs',
    component: () => import('../views/spec/SpecList.vue'),
    meta: { roles: ['业务员', '销售经理'] },
  },
  {
    path: '/process-sheets',
    component: () => import('../views/processSheet/SheetList.vue'),
    meta: { roles: ['业务员', '销售经理', '生产专员'] },
  },
  {
    path: '/process-sheets/:id',
    component: () => import('../views/processSheet/SheetDetail.vue'),
    meta: { roles: ['业务员', '销售经理', '生产专员'] },
  },
  {
    path: '/confirm/:token',
    component: () => import('../views/public/ConfirmPage.vue'),
  },
  {
    path: '/basic-data',
    component: () => import('../views/basicData/BasicDataList.vue'),
    meta: { roles: ['业务员', '销售经理'] },
  },
  {
    path: '/process-steps',
    redirect: '/basic-data',
  },
  {
    path: '/my-tasks',
    component: () => import('../views/task/MyTasks.vue'),
    meta: { roles: ['外协人员'] },
  },
  {
    path: '/settings/wecom',
    component: () => import('../views/settings/WeComSettings.vue'),
    meta: { roles: ['销售经理'] },
  },
  {
    path: '/settings/users',
    component: () => import('../views/settings/UserList.vue'),
    meta: { roles: ['销售经理'] },
  },
]

const router = createRouter({ history: createWebHistory(), routes })
router.beforeEach((to, from, next) => {
  if (to.path.startsWith('/confirm/')) return next()
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) return next('/login')
  if (token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      const role = payload.role
      if (to.meta.roles && !to.meta.roles.includes(role)) {
        return next('/dashboard')
      }
    } catch {}
  }
  next()
})
export default router
