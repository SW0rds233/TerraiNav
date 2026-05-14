<template>
  <div class="history-page">
    <div class="page-header">
      <h2>历史记录</h2>
      <p>查看所有已完成的巡逻分析任务</p>
    </div>

    <div class="history-content">
      <div v-if="loading" class="loading-state">
        <p>加载中...</p>
      </div>

      <div v-else-if="error" class="error-state">
        <p>{{ error }}</p>
        <button class="btn" @click="loadHistories">重试</button>
      </div>

      <div v-else-if="historyTasks.length === 0" class="empty-state">
        <p>暂无历史记录</p>
      </div>

      <div v-else class="history-list">
        <div v-for="task in historyTasks" :key="task.id" class="history-item">
          <div class="history-preview">
            <img :src="getImageUrl(task.input_image_url)" :alt="task.task_name" @error="onImageError" />
          </div>
          <div class="history-info">
            <h3>{{ task.task_name }}</h3>
            <p class="history-time">{{ formatTime(task.created_at) }}</p>
            <p class="history-desc">{{ task.description || '无描述' }}</p>

            <div class="history-actions">
              <button class="btn" @click="toggleDetail(task)">
                {{ expandedTaskId === task.id ? '收起详情' : '查看详情' }}
              </button>
              <button class="btn" @click="downloadReport(task)" :disabled="!task.route_url || !task.input_image_url">
                下载路线图
              </button>
              <button class="btn btn-danger" @click="deleteHistory(task)" :disabled="deleting === task.id">
                {{ deleting === task.id ? '删除中...' : '删除' }}
              </button>
            </div>

            <!-- 展开详情：原始地图 + 路径规划图叠加 -->
            <div v-if="expandedTaskId === task.id" class="task-detail-expand">
              <div class="detail-row">
                <span>任务时间：</span>{{ formatTime(task.task_time) }}
              </div>
              <div class="detail-row">
                <span>创建时间：</span>{{ formatTime(task.created_at) }}
              </div>
              <div class="detail-row">
                <span>任务状态：</span>{{ task.task_status }}
              </div>
              <div class="detail-row">
                <span>巡逻路线：</span>
                <span class="path-desc">{{ task.description || '无数据' }}</span>
              </div>

              <!-- 叠加图：原始地图 + 路线图透明叠放 -->
              <div v-if="task.route_url && task.input_image_url" class="overlay-section">
                <div class="overlay-controls">
                  <label>路线图透明度：</label>
                  <input
                    type="range"
                    v-model="overlayOpacity"
                    min="0"
                    max="100"
                    step="1"
                    class="opacity-slider"
                  />
                  <span>{{ overlayOpacity }}%</span>
                </div>
                <div class="overlay-container">
                  <img
                    :src="getImageUrl(task.input_image_url)"
                    class="base-img"
                    @error="onImageError"
                  />
                  <img
                    :src="getImageUrl(task.route_url)"
                    class="overlay-img"
                    :style="{ opacity: overlayOpacity / 100 }"
                    @error="onImageError"
                  />
                </div>
              </div>
              <div v-else class="img-group">
                <p class="no-overlay-hint">缺少原始地图或路线图，无法显示叠加效果</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUserStore } from '../../stores/userStore'
import axios from 'axios'

interface HistoryTask {
  id: number
  task_name: string
  description: string
  input_image_url: string
  heatmap_url: string
  route_url: string
  report_url: string
  task_status: string
  task_time: string
  created_at: string
  updated_at: string
}

interface HistoryResponse {
  id: number
  task_name: string
  description: string
  input_image_url: string
  heatmap_url: string
  route_url: string
  report_url: string
  task_status: string
  task_time: string
  created_at: string
  updated_at: string
}

interface AxiosError {
  response?: {
    data?: {
      error?: string
    }
  }
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'
const userStore = useUserStore()

const historyTasks = ref<HistoryTask[]>([])
const loading = ref(false)
const error = ref('')
const expandedTaskId = ref<number | null>(null)
const deleting = ref<number | null>(null)
const overlayOpacity = ref(50)

onMounted(() => {
  loadHistories()
})

const getImageUrl = (url: string) => {
  if (!url) return '/pictures/background1.jpg'

  if (url.startsWith('/static/')) {
    return `${API_BASE_URL}${url}`
  }

  if (url.startsWith('/uploads/')) {
    return `${API_BASE_URL}${url}`
  }

  if (url.startsWith('data:')) {
    return url
  }

  if (url.startsWith('http')) return url

  return url
}

const onImageError = (e: Event) => {
  const img = e.target as HTMLImageElement
  if (img) {
    img.src = '/pictures/background1.jpg'
  }
}

const loadHistories = async () => {
  if (!userStore.user.id || userStore.user.id <= 0) {
    error.value = '请先登录'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const response = await axios.get(`${API_BASE_URL}/api/history`, {
      params: {
        user_id: userStore.user.id,
        limit: 20
      }
    })

    if (response.data.success) {
      historyTasks.value = response.data.histories.map((h: HistoryResponse) => ({
        id: h.id,
        task_name: h.task_name,
        description: h.description || '',
        input_image_url: h.input_image_url || '',
        heatmap_url: h.heatmap_url || '',
        route_url: h.route_url || '',
        report_url: h.report_url || '',
        task_status: h.task_status || 'completed',
        task_time: h.task_time || '',
        created_at: h.created_at || '',
        updated_at: h.updated_at || ''
      }))
    } else {
      error.value = response.data.error || '加载失败'
    }
  } catch (err) {
    console.error('加载历史记录失败:', err)
    const axiosError = err as AxiosError
    error.value = axiosError?.response?.data?.error || (err as Error).message || '加载失败'
  } finally {
    loading.value = false
  }
}

const toggleDetail = (task: HistoryTask) => {
  if (expandedTaskId.value === task.id) {
    expandedTaskId.value = null
  } else {
    expandedTaskId.value = task.id
    overlayOpacity.value = 50
  }
}

const formatTime = (time: string) => {
  if (!time) return '未知时间'
  return new Date(time).toLocaleString('zh-CN')
}

const downloadReport = (task: HistoryTask) => {
  if (!task.route_url || !task.input_image_url) {
    alert('该任务缺少路线图或原始地图')
    return
  }
  window.open(getImageUrl(task.route_url), '_blank')
}

const deleteHistory = async (task: HistoryTask) => {
  if (!confirm(`确定要删除任务 "${task.task_name}" 吗？此操作不可恢复。`)) return

  deleting.value = task.id
  try {
    const response = await axios.delete(`${API_BASE_URL}/api/history/${task.id}`)
    if (response.data.success) {
      historyTasks.value = historyTasks.value.filter((h) => h.id !== task.id)
      if (expandedTaskId.value === task.id) {
        expandedTaskId.value = null
      }
    } else {
      alert('删除失败: ' + (response.data.error || '未知错误'))
    }
  } catch (err) {
    console.error('删除历史记录失败:', err)
    const axiosError = err as AxiosError
    alert('删除失败: ' + (axiosError?.response?.data?.error || (err as Error).message || '未知错误'))
  } finally {
    deleting.value = null
  }
}
</script>

<style scoped>
.history-page {
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

.history-content {
  min-height: 400px;
}

.loading-state, .error-state, .empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  font-size: 1rem;
  color: #9ca3af;
}

.error-state {
  flex-direction: column;
  gap: 1rem;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.history-item {
  display: flex;
  gap: 1.5rem;
  padding: 1.5rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
  transition: transform 0.3s, box-shadow 0.3s;
}

.history-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.history-preview {
  width: 200px;
  height: 150px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
}

.history-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.history-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.history-info h3 {
  font-size: 1.2rem;
  color: #1a2980;
  margin-bottom: 0.5rem;
}

.history-time {
  color: #9ca3af;
  font-size: 0.9rem;
  margin-bottom: 0.8rem;
}

.history-desc {
  color: #4b5563;
  line-height: 1.5;
  margin-bottom: 1rem;
  flex: 1;
  font-family: 'Consolas', 'Courier New', monospace;
  word-break: break-all;
}

.history-actions {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.task-detail-expand {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px dashed #e5e7eb;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  font-size: 0.9rem;
  color: #374151;
}

.detail-row {
  display: flex;
}

.detail-row span:first-child {
  min-width: 100px;
  font-weight: 500;
  color: #1a2980;
}

.path-desc {
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 0.85rem;
  color: #374151;
  word-break: break-all;
}

/* 叠加图样式 */
.overlay-section {
  margin-top: 12px;
}

.overlay-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 13px;
  color: #4b5563;
}

.opacity-slider {
  width: 120px;
  accent-color: #1a2980;
}

.overlay-container {
  position: relative;
  display: grid;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  max-width: 500px;
}

.overlay-container > * {
  grid-area: 1 / 1;
}

.base-img,
.overlay-img {
  width: 100%;
  height: auto;
  display: block;
  object-fit: contain;
}

.overlay-img {
  pointer-events: none;
}

.no-overlay-hint {
  color: #9ca3af;
  font-size: 0.85rem;
}

.img-group {
  margin-top: 12px;
}

.btn {
  background: linear-gradient(90deg, #1a2980, #26d0ce);
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  opacity: 0.6;
}

.btn:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
}

.btn-danger {
  background: linear-gradient(90deg, #dc2626, #ef4444);
}

.btn-danger:hover:not(:disabled) {
  background: linear-gradient(90deg, #b91c1c, #dc2626);
}

@media (max-width: 768px) {
  .history-item {
    flex-direction: column;
  }

  .history-preview {
    width: 100%;
    height: 200px;
  }

  .overlay-container {
    max-width: 100%;
  }
}
</style>
