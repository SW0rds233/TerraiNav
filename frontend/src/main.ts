// src/main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

// 导入全局样式
import './assets/styles/main.css'

// 获取环境变量（使用 Vite 的方式）
const isDevelopment = import.meta.env.DEV
const isProduction = import.meta.env.PROD
const appVersion = import.meta.env.VITE_APP_VERSION || '1.0.0'

// 创建应用实例
const app = createApp(App)

// 创建 Pinia 实例
const pinia = createPinia()

// 在安装 Pinia 之前注册全局错误处理器
app.config.errorHandler = (err, instance, info) => {
  console.error('Vue 错误:', err)
  console.error('发生在组件:', instance?.$.type?.name)
  console.error('错误信息:', info)

  // 可以在这里添加错误报告逻辑
  if (isProduction) {
    // 生产环境错误上报
    console.error('生产环境错误，应上报:', err) // 修复：移除 reportError 调用
  }
}

// 全局性能监控
if (isDevelopment) {
  // 开发环境性能监控
  const { performance } = window
  if (performance) {
    const startTime = performance.now()
    window.addEventListener('load', () => {
      const loadTime = performance.now() - startTime
      console.log(`应用加载时间: ${loadTime.toFixed(2)}ms`)
    })
  }
}

// 安装 Pinia
app.use(pinia)

// 在安装路由之前初始化用户状态
import { useUserStore } from './stores/userStore'

// 创建用户存储实例
let userStore: ReturnType<typeof useUserStore> | null = null

try {
  userStore = useUserStore()

  // 初始化用户状态
  userStore.initializeUser()

  // 应用主题
  userStore.applyTheme()

  console.log('用户状态初始化完成', {
    isAuthenticated: userStore.isAuthenticated,
    user: userStore.user,
    theme: userStore.preferences.theme
  })
} catch (error) {
  console.error('用户状态初始化失败:', error)
}

// 全局路由守卫
router.beforeEach((to, from, next) => {
  console.log('路由跳转:', {
    from: from.path,
    to: to.path,
    requiresAuth: to.meta?.requiresAuth
  })

  // 重新获取用户存储实例
  if (!userStore) {
    userStore = useUserStore()
  }

  // 检查需要认证的路由
  const requiresAuth = to.path.startsWith('/dashboard') || to.meta?.requiresAuth

  if (requiresAuth && !userStore.isAuthenticated) {
    console.log('需要认证，但未登录，重定向到登录页')
    next('/login')
    return
  }

  // 如果已登录但访问登录页，重定向到仪表板
  if (to.path === '/login' && userStore.isAuthenticated) {
    console.log('已登录，重定向到仪表板')
    next('/dashboard/map-analysis')
    return
  }

  // 检查API密钥（针对需要API密钥的页面）
  if (to.meta?.requiresApiKey && !userStore.hasApiKey) {
    // 可以在这里显示提示或跳转到设置页面
    console.warn('此页面需要API密钥，但当前未配置')
  }

  next()
})

// 安装路由
app.use(router)

// 全局组件注册
// 可以在这里注册全局组件
// app.component('GlobalComponent', GlobalComponent)

// 全局指令
app.directive('focus', {
  mounted(el) {
    el.focus()
  }
})

// 全局属性
app.config.globalProperties.$filters = {
  formatDate(date: Date) {
    return new Intl.DateTimeFormat('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date(date))
  },
  truncate(text: string, length: number = 50) {
    if (text.length <= length) return text
    return text.substring(0, length) + '...'
  }
}

// 开发环境工具
if (isDevelopment) {
  // 在开发环境下暴露一些全局变量以便调试
  ;(window as Window & { __VUE_APP__?: unknown }).__VUE_APP__ = app

  // 添加一个全局的重新加载函数
  ;(window as Window & { reloadApp: () => void }).reloadApp = () => {
    window.location.reload()
  }

  console.log(`
  🚀 TerraiNav 地形适应无人机巡逻系统
  ===================================
  环境: ${isDevelopment ? 'development' : 'production'}
  版本: ${appVersion}
  构建时间: ${new Date().toLocaleString()}
  ===================================
  `)
}

// 挂载应用
app.mount('#app')

// 挂载完成后的处理
app.config.globalProperties.$app = {
  version: appVersion,
  env: isDevelopment ? 'development' : 'production',
  isProduction,
  reload: () => window.location.reload()
}

// 窗口关闭前的处理
window.addEventListener('beforeunload', () => {
  if (userStore && userStore.preferences.autoSave) {
    console.log('自动保存应用状态...')
    // 可以在这里添加状态保存逻辑
  }
})

// 扩展 Window 类型
declare global {
  interface Window {
    __VUE_APP__?: unknown
    reloadApp: () => void
  }
}
