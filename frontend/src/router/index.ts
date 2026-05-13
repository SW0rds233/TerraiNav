import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/dashboard/map-analysis'
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue')
  },
  {
    path: '/about',
    name: 'about',
    component: () => import('../views/AboutView.vue')
  },
  {
    path: '/help',
    name: 'help',
    component: () => import('../views/HelpView.vue')
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('../views/DashboardView.vue'),
    children: [
      {
      path: '',
      redirect: '/dashboard/map-analysis'  // 添加默认重定向
      },
      {
        path: 'map-analysis',
        name: 'map-analysis',
        component: () => import('../components/dashboard/MapAnalysis.vue'),
        meta: { title: '地图分析' }
      },
      {
        path: 'history',
        name: 'history',
        component: () => import('../components/dashboard/History.vue'),
        meta: { title: '历史记录' }
      },
      {
        path: 'settings',
        name: 'settings',
        component: () => import('../components/dashboard/Settings.vue'),
        meta: { title: '系统设置' }
      },
      {
        path: 'tutorial',
        name: 'tutorial',
        component: () => import('../components/dashboard/Tutorial.vue'),
        meta: { title: '使用教程' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：设置页面标题
router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} - TerraiNav`
  } else {
    document.title = 'TerraiNav地形适应无人机巡逻系统'
  }
  next()
})

export default router
