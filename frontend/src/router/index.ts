import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '诊断工作台' },
      },
      {
        path: 'diagnosis/:id',
        name: 'diagnosis-detail',
        component: () => import('@/views/DiagnosisDetail.vue'),
        meta: { title: '诊断详情' },
      },
      {
        path: 'history',
        name: 'history',
        component: () => import('@/views/History.vue'),
        meta: { title: '历史记录' },
      },
      {
        path: 'settings',
        name: 'settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '配置' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.afterEach((to) => {
  const title = (to.meta.title as string | undefined) ?? 'AIOpsGuard'
  document.title = `${title} · AIOpsGuard`
})

export default router
