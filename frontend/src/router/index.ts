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

// 【认证守卫】保护 dashboard 路由，未登录自动跳转登录页
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - TerraiNav`
  } else {
    document.title = 'TerraiNav地形适应无人机巡逻系统'
  }

  // 检查目标路由是否需要认证
  const requiresAuth = to.path.startsWith('/dashboard')
  const isLoginPage = to.path === '/login'

  if (requiresAuth) {
    const token = localStorage.getItem('terrainav_token')
    if (!token) {
      // 未登录 → 重定向到登录页
      console.log('[路由守卫] 未登录，跳转登录页')
      next('/login')
      return
    }
  }

  // 已登录用户访问登录页 → 重定向到仪表板
  if (isLoginPage) {
    const token = localStorage.getItem('terrainav_token')
    if (token) {
      console.log('[路由守卫] 已登录，跳转仪表板')
      next('/dashboard/map-analysis')
      return
    }
  }

  next()
})

export default router
