<template>
  <div class="history-page">
    <div class="page-header">
      <h2>历史记录</h2>
      <p>查看所有已完成的巡逻分析任务</p>
    </div>
    
    <div class="history-content">
      <div class="history-list">
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
import { ref } from 'vue'

// 模拟历史任务数据
const historyTasks = ref([
  {
    id: 1,
    name: '山区地形威胁度分析',
    time: '2026-04-15 14:30',
    description: '完成山区地形威胁度分析，生成巡逻路径和热力图',
    image: '/pictures/background1.jpg',
    status: 'completed'
  },
  {
    id: 2,
    name: '城市区域巡逻规划',
    time: '2026-04-14 10:15',
    description: '城市区域无人机巡逻路径规划，包含多个兴趣点',
    image: '/pictures/background1.jpg',
    status: 'completed'
  },
  {
    id: 3,
    name: '森林火灾监测区域',
    time: '2026-04-13 16:45',
    description: '森林火灾监测区域的无人机巡逻路径设计',
    image: '/pictures/background1.jpg',
    status: 'completed'
  },
  {
    id: 4,
    name: '海岸线巡逻任务',
    time: '2026-01-12 09:20',
    description: '海岸线区域无人机巡逻任务，包含多个检查点',
    image: '/pictures/background1.jpg',
    status: 'completed'
  }
])

// 查看详情
const viewDetails = (task) => {
  alert(`查看任务详情: ${task.name}`)
}

// 下载报告
const downloadReport = (task) => {
  alert(`下载任务报告: ${task.name}`)
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