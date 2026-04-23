<template>
  <div class="settings-page">
    <div class="page-header">
      <h2>系统设置</h2>
      <p>配置系统参数和用户偏好</p>
    </div>

    <div class="settings-content">
      <div class="settings-sections">
        <!-- API设置 -->
        <div class="settings-section">
          <h3>API设置</h3>
          <div class="setting-item">
            <label for="api-key">阿里云百炼API密钥</label>
            <input
              id="api-key"
              v-model="apiKey"
              type="password"
              placeholder="请输入您的API密钥"
              class="setting-input"
            />
            <p class="setting-hint">用于访问阿里云百炼AI服务，请妥善保管</p>
            <button class="btn" @click="saveApiKey">保存API密钥</button>
          </div>
        </div>

        <!-- 偏好设置 -->
        <div class="settings-section">
          <h3>偏好设置</h3>
          <div class="setting-item">
            <label>主题</label>
            <select v-model="theme" class="setting-select">
              <option value="light">浅色主题</option>
              <option value="dark">深色主题</option>
              <option value="auto">自动</option>
            </select>
          </div>

          <div class="setting-item">
            <label>语言</label>
            <select v-model="language" class="setting-select">
              <option value="zh-CN">简体中文</option>
              <option value="en-US">English</option>
            </select>
          </div>

          <div class="setting-item">
            <label>
              <input type="checkbox" v-model="autoSave" />
              自动保存工作
            </label>
          </div>

          <div class="setting-item">
            <label>
              <input type="checkbox" v-model="notifications" />
              启用通知
            </label>
          </div>

          <div class="setting-item">
            <label>
              <input type="checkbox" v-model="gridDisplay" />
              显示网格
            </label>
          </div>

          <div class="setting-item">
            <label>
              <input type="checkbox" v-model="showLegend" />
              显示图例
            </label>
          </div>
        </div>

        <!-- 无人机默认参数 -->
        <div class="settings-section">
          <h3>无人机默认参数</h3>
          <div class="setting-item">
            <label for="default-grid">默认网格分区 (M*N)</label>
            <input
              id="default-grid"
              v-model="defaultGrid"
              type="text"
              placeholder="例如：4 * 4"
              class="setting-input"
            />
            <p class="setting-hint">将巡逻区域划分为 M×N 个区块</p>
          </div>

          <div class="setting-item">
            <label for="default-start">默认起点区块 (行,列)</label>
            <input
              id="default-start"
              v-model="defaultStartPoint"
              type="text"
              placeholder="例如：1,1"
              class="setting-input"
            />
            <p class="setting-hint">无人机巡逻的起始区块位置</p>
          </div>
        </div>

        <!-- 系统信息 -->
        <div class="settings-section">
          <h3>系统信息</h3>
          <div class="setting-item">
            <label>系统版本</label>
            <div class="system-info">v1.0.0</div>
          </div>

          <div class="setting-item">
            <label>最后更新</label>
            <div class="system-info">2026-04-14</div>
          </div>

          <div class="setting-item">
            <label>存储空间</label>
            <div class="system-info">
              <div class="storage-bar">
                <div class="storage-fill" :style="{ width: storageUsed + '%' }"></div>
              </div>
              <span class="storage-text"
                >{{ storageUsed }}% 已使用 ({{ usedSpace }} MB / {{ totalSpace }} MB)</span
              >
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="settings-actions">
          <button class="btn btn-primary" @click="saveSettings">保存设置</button>
          <button class="btn" @click="resetSettings">恢复默认</button>
          <button class="btn btn-danger" @click="clearData">清除所有数据</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useUserStore } from '../../stores/userStore'

const userStore = useUserStore()

// API设置
const apiKey = ref('')

// 偏好设置
const theme = ref('light')
const language = ref('zh-CN')
const autoSave = ref(true)
const notifications = ref(true)
const gridDisplay = ref(true)
const showLegend = ref(true)

// 无人机参数
const defaultGrid = ref('4 * 4')
const defaultStartPoint = ref('1,1')

// 系统信息
const storageUsed = ref(45)
const usedSpace = ref(450)
const totalSpace = ref(1000)

// 应用主题
const applyTheme = () => {
  let targetTheme = theme.value

  // 处理自动主题
  if (targetTheme === 'auto') {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    targetTheme = prefersDark ? 'dark' : 'light'
  }

  // 应用主题到 document
  if (targetTheme === 'dark') {
    document.documentElement.classList.add('dark-theme')
    document.documentElement.setAttribute('data-theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark-theme')
    document.documentElement.setAttribute('data-theme', 'light')
  }

  // 更新 store 中的主题设置
  userStore.updatePreferences({ theme: theme.value })
}

// 监听主题变化
watch(theme, () => {
  applyTheme()
})

// 监听系统主题变化（当设置为 auto 时）
const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
const handleSystemThemeChange = () => {
  if (theme.value === 'auto') {
    applyTheme()
  }
}
mediaQuery.addEventListener('change', handleSystemThemeChange)

// 加载设置
const loadSettings = () => {
  // 从userStore加载设置
  apiKey.value = userStore.apiConfig.baiduQianfanApiKey || ''
  theme.value = userStore.preferences.theme
  language.value = userStore.preferences.language
  autoSave.value = userStore.preferences.autoSave
  notifications.value = userStore.preferences.notifications
  gridDisplay.value = userStore.preferences.gridDisplay
  showLegend.value = userStore.preferences.showHeatmapLegend

  // 尝试从localStorage加载无人机参数
  const savedDroneParams = localStorage.getItem('terrainav_drone_params')
  if (savedDroneParams) {
    try {
      const params = JSON.parse(savedDroneParams)
      defaultGrid.value = params.gridBlocks || '4 * 4'
      defaultStartPoint.value = params.startPoint || '1,1'
    } catch (error) {
      console.error('加载无人机参数失败:', error)
    }
  }

  // 应用初始主题
  applyTheme()
}

// 保存API密钥
const saveApiKey = () => {
  if (apiKey.value) {
    userStore.updateApiKey(apiKey.value)
    alert('API密钥保存成功')
  } else {
    alert('请输入API密钥')
  }
}

// 保存设置
const saveSettings = () => {
  // 保存到userStore
  userStore.updatePreferences({
    theme: theme.value,
    language: language.value,
    autoSave: autoSave.value,
    notifications: notifications.value,
    gridDisplay: gridDisplay.value,
    showHeatmapLegend: showLegend.value,
  })

  // 保存无人机参数到localStorage
  const droneParams = {
    gridBlocks: defaultGrid.value,
    startPoint: defaultStartPoint.value,
  }
  localStorage.setItem('terrainav_drone_params', JSON.stringify(droneParams))

  // 应用主题
  applyTheme()

  alert('设置保存成功')
}

// 恢复默认设置
const resetSettings = () => {
  if (confirm('确定要恢复默认设置吗？当前设置将会被覆盖。')) {
    // 重置偏好设置
    userStore.updatePreferences({
      theme: 'light',
      language: 'zh-CN',
      autoSave: true,
      notifications: true,
      gridDisplay: true,
      showHeatmapLegend: true,
    })

    // 重置本地设置
    theme.value = 'light'
    language.value = 'zh-CN'
    autoSave.value = true
    notifications.value = true
    gridDisplay.value = true
    showLegend.value = true

    // 重置无人机参数
    defaultGrid.value = '4 * 4'
    defaultStartPoint.value = '1,1'

    // 应用主题
    applyTheme()

    alert('已恢复默认设置')
  }
}

// 清除所有数据
const clearData = () => {
  if (confirm('确定要清除所有数据吗？此操作不可撤销。')) {
    localStorage.clear()
    userStore.logout()
    alert('所有数据已清除，页面将重新加载')
    window.location.reload()
  }
}

// 组件挂载时加载设置
onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings-page {
  padding: 1rem;
}

.page-header {
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.page-header h2 {
  font-size: 1.8rem;
  color: #1a2980;
  margin-bottom: 0.5rem;
}

.page-header p {
  color: #6b7280;
  font-size: 1rem;
}

.settings-content {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
}

.settings-sections {
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
}

.settings-section h3 {
  font-size: 1.3rem;
  color: #374151;
  margin-bottom: 1.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #e5e7eb;
}

.setting-item {
  margin-bottom: 1.5rem;
}

.setting-item label {
  display: block;
  font-weight: 500;
  color: #4b5563;
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
}

.setting-input {
  width: 100%;
  max-width: 400px;
  padding: 0.6rem 0.8rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9rem;
  background: white;
  transition: border-color 0.3s;
}

.setting-input:focus {
  outline: none;
  border-color: #4a6cf7;
  box-shadow: 0 0 0 3px rgba(74, 108, 247, 0.1);
}

.setting-select {
  width: 100%;
  max-width: 400px;
  padding: 0.6rem 0.8rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9rem;
  background: white;
  cursor: pointer;
}

.setting-hint {
  font-size: 0.85rem;
  color: #9ca3af;
  margin-top: 0.3rem;
  line-height: 1.4;
}

.setting-item input[type='checkbox'] {
  margin-right: 0.5rem;
}

.system-info {
  padding: 0.6rem 0.8rem;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  color: #4b5563;
  font-size: 0.9rem;
}

.storage-bar {
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  overflow: hidden;
}

.storage-fill {
  height: 100%;
  background: linear-gradient(90deg, #1a2980, #26d0ce);
  border-radius: 4px;
  transition: width 0.3s;
}

.storage-text {
  font-size: 0.85rem;
  color: #6b7280;
}

.settings-actions {
  display: flex;
  gap: 1rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
  margin-top: 1rem;
}

.btn {
  padding: 0.7rem 1.5rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
  background: #f3f4f6;
  color: #4b5563;
}

.btn-primary {
  background: linear-gradient(90deg, #1a2980, #26d0ce);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(26, 41, 128, 0.2);
}

.btn:hover {
  background: #e5e7eb;
  transform: translateY(-1px);
}

.btn-danger {
  background: #fee2e2;
  color: #dc2626;
}

.btn-danger:hover {
  background: #fecaca;
}

@media (max-width: 768px) {
  .settings-actions {
    flex-direction: column;
  }

  .btn {
    width: 100%;
  }
}
</style>
