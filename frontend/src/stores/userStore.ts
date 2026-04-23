import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  // 用户认证状态
  const isAuthenticated = ref(false)
  
  // 用户信息
  const user = ref({
    id: '',
    name: '管理员',
    email: '',
    role: 'admin', // admin, user, guest
    avatar: '',
    loginTime: null as string | null
  })
  
  // API配置
  const apiConfig = ref({
    baiduQianfanApiKey: '',
    lastUsed: ''
  })
  
  // 系统偏好设置
  const preferences = ref({
    theme: 'light', // light, dark, auto
    language: 'zh-CN',
    notifications: true,
    autoSave: true,
    gridDisplay: true,
    showHeatmapLegend: true
  })
  
  // 计算属性
  const isAdmin = computed(() => user.value.role === 'admin')
  const userName = computed(() => user.value.name || '用户')
  const hasApiKey = computed(() => !!apiConfig.value.baiduQianfanApiKey)
  
  // 初始化用户状态
  const initializeUser = () => {
    const token = localStorage.getItem('terrainav_token')
    const savedUser = localStorage.getItem('terrainav_user')
    const savedApiConfig = localStorage.getItem('terrainav_api_config')
    const savedPreferences = localStorage.getItem('terrainav_preferences')
    
    isAuthenticated.value = !!token
    
    if (savedUser) {
      try {
        user.value = { ...user.value, ...JSON.parse(savedUser) }
      } catch (error) {
        console.error('解析用户信息失败:', error)
      }
    }
    
    if (savedApiConfig) {
      try {
        apiConfig.value = JSON.parse(savedApiConfig)
      } catch (error) {
        console.error('解析API配置失败:', error)
      }
    }
    
    if (savedPreferences) {
      try {
        preferences.value = { ...preferences.value, ...JSON.parse(savedPreferences) }
      } catch (error) {
        console.error('解析用户偏好失败:', error)
      }
    }
  }
  
  // 登录
  const login = (username: string, password: string) => {
    return new Promise((resolve, reject) => {
      // 模拟登录请求
      setTimeout(() => {
        if (username && password) {
          isAuthenticated.value = true
          
          // 更新用户信息
          user.value = {
            id: 'user_' + Date.now(),
            name: username === 'admin' ? '系统管理员' : '普通用户',
            email: username.includes('@') ? username : `${username}@example.com`,
            role: username === 'admin' ? 'admin' : 'user',
            avatar: '',
            loginTime: new Date().toISOString()
          }
          
          // 保存到本地存储
          localStorage.setItem('terrainav_token', 'mock_token_' + Date.now())
          localStorage.setItem('terrainav_user', JSON.stringify(user.value))
          
          console.log('登录成功:', user.value)
          resolve(user.value)
        } else {
          reject(new Error('用户名或密码不能为空'))
        }
      }, 1000)
    })
  }
  
  // 退出登录 - 只处理状态，不处理路由跳转
  const logout = () => {
    isAuthenticated.value = false
    user.value = {
      id: '',
      name: '访客',
      email: '',
      role: 'guest',
      avatar: '',
      loginTime: null
    }
    
    // 清除本地存储
    localStorage.removeItem('terrainav_token')
    localStorage.removeItem('terrainav_user')
    
    console.log('用户已退出登录')
    
    return true
  }
  
  // 更新API密钥
  const updateApiKey = (apiKey: string) => {
    apiConfig.value.baiduQianfanApiKey = apiKey
    apiConfig.value.lastUsed = new Date().toISOString()
    
    // 保存到本地存储
    localStorage.setItem('terrainav_api_config', JSON.stringify(apiConfig.value))
    
    return true
  }
  
  // 验证API密钥
  const validateApiKey = () => {
    if (!apiConfig.value.baiduQianfanApiKey) {
      return { valid: false, message: 'API密钥为空' }
    }
    
    // 这里可以添加实际验证逻辑
    // 模拟验证
    return { valid: true, message: 'API密钥验证通过' }
  }
  
  // 更新用户信息
  const updateUser = (userInfo: Partial<typeof user.value>) => {
    user.value = { ...user.value, ...userInfo }
    localStorage.setItem('terrainav_user', JSON.stringify(user.value))
  }
  
  // 更新偏好设置
  const updatePreferences = (newPreferences: Partial<typeof preferences.value>) => {
    preferences.value = { ...preferences.value, ...newPreferences }
    localStorage.setItem('terrainav_preferences', JSON.stringify(preferences.value))
  }
  
  // 切换主题
  const toggleTheme = () => {
    preferences.value.theme = preferences.value.theme === 'light' ? 'dark' : 'light'
    updatePreferences({ theme: preferences.value.theme })
    
    // 应用主题
    applyTheme()
  }
  
  // 应用主题
  const applyTheme = () => {
    if (preferences.value.theme === 'dark') {
      document.documentElement.classList.add('dark-theme')
    } else {
      document.documentElement.classList.remove('dark-theme')
    }
  }
  
  // 检查认证状态
  const checkAuth = () => {
    const token = localStorage.getItem('terrainav_token')
    isAuthenticated.value = !!token
    
    if (token && !user.value.id) {
      initializeUser()
    }
    
    return isAuthenticated.value
  }
  
  // 获取用户统计信息
  const getUserStats = () => {
    return {
      totalTasks: 12,
      completedTasks: 8,
      pendingTasks: 4,
      apiUsage: 45,
      lastActive: '2小时前'
    }
  }
  
  // 导出store的所有内容
  return {
    // 状态
    isAuthenticated,
    user,
    apiConfig,
    preferences,
    
    // 计算属性
    isAdmin,
    userName,
    hasApiKey,
    
    // 方法
    initializeUser,
    login,
    logout,
    updateApiKey,
    validateApiKey,
    updateUser,
    updatePreferences,
    toggleTheme,
    applyTheme,
    checkAuth,
    getUserStats
  }
})