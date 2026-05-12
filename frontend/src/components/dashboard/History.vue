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
            <img :src="task.image" :alt="task.name" />
          </div>
          <div class="history-info">
            <h3>{{ task.name }}</h3>
            <p class="history-time">{{ task.time }}</p>
            <p class="history-desc">{{ task.description }}</p>
            <div class="history-actions">
              <button class="btn" @click="viewDetails(task)">查看详情</button>
              <button class="btn" @click="downloadReport(task)">下载报告</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '../../stores/userStore'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'
const userStore = useUserStore()

const historyTasks = ref([])
const loading = ref(false)
const error = ref('')

onMounted(() => {
  loadHistories()
})

const loadHistories = async () => {
  if (!userStore.user.id) {
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
      historyTasks.value = response.data.histories.map(h => ({
        id: h.id,
        name: h.task_name,
        time: h.created_at ? new Date(h.created_at).toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit'
        }) : '',
        description: `输入图像: ${h.input_image_url || '无'}`,
        image: h.input_image_url || '/pictures/background1.jpg',
        status: 'completed',
        outputRouteUrl: h.output_route_url,
        routeData: h.route_data
      }))
    } else {
      error.value = response.data.error || '加载失败'
    }
  } catch (err) {
    console.error('加载历史记录失败:', err)
    error.value = (err as any)?.response?.data?.error || (err as Error).message || '加载失败'
  } finally {
    loading.value = false
  }
}

const viewDetails = (task) => {
  alert(`查看任务详情: ${task.name}\n\n巡逻路线数据: ${task.routeData || '无'}`)
}

const downloadReport = (task) => {
  if (task.outputRouteUrl) {
    window.open(task.outputRouteUrl, '_blank')
  } else {
    alert('该任务没有可下载的报告')
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
}

.history-actions {
  display: flex;
  gap: 0.5rem;
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

.btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .history-item {
    flex-direction: column;
  }

  .history-preview {
    width: 100%;
    height: 200px;
  }
}
</style>
