import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

export const useUserStore = defineStore('user', () => {
  const isAuthenticated = ref(false)

  const user = ref({
    id: 0,
    name: '访客',
    email: '',
    role: 'guest',
    avatar: '',
    loginTime: null as string | null
  })

  const apiConfig = ref({
    baiduQianfanApiKey: '',
    lastUsed: ''
  })

  const preferences = ref({
    theme: 'light',
    language: 'zh-CN',
    notifications: true,
    autoSave: true,
    gridDisplay: true,
    showHeatmapLegend: true
  })

  const isAdmin = computed(() => user.value.role === 'admin')
  const userName = computed(() => user.value.name || '用户')
  const hasApiKey = computed(() => !!apiConfig.value.baiduQianfanApiKey)

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

  const login = async (username: string, password: string) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/login`, {
        username,
        password
      })

      if (response.data.success) {
        isAuthenticated.value = true

        const userData = response.data.user
        user.value = {
          id: userData.id,
          name: userData.username,
          email: userData.email,
          role: userData.usertype,
          avatar: '',
          loginTime: new Date().toISOString()
        }

        localStorage.setItem('terrainav_token', response.data.token)
        localStorage.setItem('terrainav_user', JSON.stringify(user.value))

        console.log('登录成功:', user.value)
        return user.value
      } else {
        throw new Error(response.data.error || '登录失败')
      }
    } catch (error: unknown) {
      console.error('登录失败:', error)
      const err = error as Error
      const axiosError = error as { response?: { data?: { error?: string } } }
      throw new Error(axiosError?.response?.data?.error || err.message || '登录失败')
    }
  }

  const register = async (username: string, email: string, password: string) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/register`, {
        username,
        email,
        password
      })

      if (response.data.success) {
        console.log('注册成功:', response.data.user)
        return response.data.user
      } else {
        throw new Error(response.data.error || '注册失败')
      }
    } catch (error: unknown) {
      console.error('注册失败:', error)
      const err = error as Error
      const axiosError = error as { response?: { data?: { error?: string } } }
      throw new Error(axiosError?.response?.data?.error || err.message || '注册失败')
    }
  }

  const logout = () => {
    isAuthenticated.value = false
    user.value = {
      id: 0,
      name: '访客',
      email: '',
      role: 'guest',
      avatar: '',
      loginTime: null
    }

    localStorage.removeItem('terrainav_token')
    localStorage.removeItem('terrainav_user')

    console.log('用户已退出登录')

    return true
  }

  const updateApiKey = (apiKey: string) => {
    apiConfig.value.baiduQianfanApiKey = apiKey
    apiConfig.value.lastUsed = new Date().toISOString()

    localStorage.setItem('terrainav_api_config', JSON.stringify(apiConfig.value))

    return true
  }

  const validateApiKey = () => {
    if (!apiConfig.value.baiduQianfanApiKey) {
      return { valid: false, message: 'API密钥为空' }
    }

    return { valid: true, message: 'API密钥验证通过' }
  }

  const updateUser = (userInfo: Partial<typeof user.value>) => {
    user.value = { ...user.value, ...userInfo }
    localStorage.setItem('terrainav_user', JSON.stringify(user.value))
  }

  const updatePreferences = (newPreferences: Partial<typeof preferences.value>) => {
    preferences.value = { ...preferences.value, ...newPreferences }
    localStorage.setItem('terrainav_preferences', JSON.stringify(preferences.value))
  }

  const toggleTheme = () => {
    preferences.value.theme = preferences.value.theme === 'light' ? 'dark' : 'light'
    updatePreferences({ theme: preferences.value.theme })

    applyTheme()
  }

  const applyTheme = () => {
    if (preferences.value.theme === 'dark') {
      document.documentElement.classList.add('dark-theme')
    } else {
      document.documentElement.classList.remove('dark-theme')
    }
  }

  const checkAuth = () => {
    const token = localStorage.getItem('terrainav_token')
    isAuthenticated.value = !!token

    if (token && !user.value.id) {
      initializeUser()
    }

    return isAuthenticated.value
  }

  const getUserStats = () => {
    return {
      totalTasks: 12,
      completedTasks: 8,
      pendingTasks: 4,
      apiUsage: 45,
      lastActive: '2小时前'
    }
  }

  return {
    isAuthenticated,
    user,
    apiConfig,
    preferences,
    isAdmin,
    userName,
    hasApiKey,
    initializeUser,
    login,
    register,
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
