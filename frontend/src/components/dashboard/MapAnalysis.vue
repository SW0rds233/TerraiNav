<template>
  <div class="dashboard">
    <!-- 主要内容区域 -->
    <div class="dashboard-content">
      <!-- 左侧控制面板 -->
      <div class="left-panel">
        <!-- 地图上传区域 -->
        <div class="upload-card">
          <h2 class="card-title">地形路径规划</h2>
          <p class="card-subtitle">上传地形图，生成最优巡逻路径</p>

          <div
            class="upload-area"
            @click="triggerFileInput"
            @dragover.prevent
            @drop.prevent="handleDrop"
          >
            <input
              type="file"
              ref="fileInput"
              @change="handleFileSelect"
              accept="image/*"
              style="display: none"
            />

            <div v-if="!selectedImage" class="upload-placeholder">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="48"
                height="48"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7"></path>
                <line x1="16" y1="5" x2="22" y2="5"></line>
                <line x1="19" y1="2" x2="19" y2="8"></line>
                <circle cx="9" cy="9" r="2"></circle>
                <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"></path>
              </svg>
              <p><strong>点击上传或拖拽文件到此区域</strong></p>
              <p>支持JPG、PNG格式，最大10MB</p>
              <p class="upload-hint">上传地形图、等高线图或卫星图</p>
            </div>

            <div v-else class="upload-preview">
              <div class="preview-image">
                <img :src="selectedImage" alt="地图预览" />
              </div>
              <div class="preview-info">
                <p>{{ selectedFileName }}</p>
                <p>{{ selectedFileSize }}</p>
              </div>
            </div>
          </div>

          <!-- API配置 -->
          <div class="api-config">
            <h3>API配置</h3>
            <input v-model="apiKey" type="password" placeholder="请输入API密钥" class="api-input" />
            <button class="api-test-btn" @click="testApiKey">测试连接</button>
          </div>

          <!-- 输出选项 -->
          <div class="output-options">
            <h3>输出选项</h3>
            <div class="option-group">
              <h4>输出类型</h4>
              <label>
                <input type="checkbox" v-model="outputOptions.heatmap" />
                生成威胁度热力图
              </label>
              <label>
                <input type="checkbox" v-model="outputOptions.path" />
                生成巡逻路线图
              </label>
            </div>
            <div class="option-group">
              <h4>输出质量</h4>
              <select v-model="outputOptions.quality" class="quality-select">
                <option value="low">低质量 (快速)</option>
                <option value="medium">中等质量</option>
                <option value="high">高质量 (推荐)</option>
              </select>
            </div>
          </div>

          <!-- 任务名称输入 -->
          <div class="taskname-params">
            <h3>任务名称</h3>
            <div class="param-group">
              <input
                type="text"
                v-model="taskName"
                class="param-input"
                placeholder="请输入任务名称（可选）"
              />
            </div>
          </div>
          <!-- 无人机巡逻参数 -->
          <div class="drone-params">
            <h3>无人机巡逻参数</h3>
            <div class="param-group">
              <label>巡逻起始区块 (x,y)</label>
              <input
                type="text"
                v-model="droneParams.startPoint"
                class="param-input"
                placeholder="例如: 1,1"
              />
            </div>
            <div class="param-group">
              <label>巡逻区块划分 (m×n)</label>
              <input
                type="text"
                v-model="droneParams.gridBlocks"
                class="param-input"
                placeholder="例如: 4 * 4"
                :class="{ invalid: !gridBlocksValid }"
              />
              <p class="param-hint">格式: 行数*列数，例如: 3 * 4 表示3行4列，共12个区块</p>
              <div v-if="!validateGridBlocks()" class="error-message">
                格式错误，请输入如"4 * 3"的格式
              </div>
              <div v-if="gridBlocksValid" class="grid-info">
                将划分为 {{ parsedGridBlocks.m }}×{{ parsedGridBlocks.n }} 个区块，共
                {{ parsedGridBlocks.m * parsedGridBlocks.n }} 个巡逻区块
              </div>
            </div>
          </div>

          <!-- 开始分析按钮 -->
          <button class="analyze-btn" @click="startAnalysis" :disabled="!canAnalyze">
            <svg v-if="analyzing" class="spinner" viewBox="0 0 50 50">
              <circle cx="25" cy="25" r="20" fill="none" stroke="white" stroke-width="4"></circle>
            </svg>
            <span v-if="analyzing" class="analyzing">分析中...</span>
            <span v-else>开始智能分析</span>
          </button>
          <div class="analysis-progress" v-if="analysisProgress.status !== 'idle'">
            <div class="progress-text">{{ analysisProgress.message }}</div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: analysisProgress.progress_percent + '%' }"></div>
            </div>
          </div>
          <div class="analysis-tip">
            {{ analysisTip }}
          </div>
        </div>

        <!-- 最近任务 -->
        <div class="recent-tasks">
          <div class="tasks-header">
            <h3>最近任务</h3>
            <button class="refresh-btn" @click="refreshTasks">刷新</button>
          </div>
          <div class="tasks-list">
            <div v-for="task in recentTasks" :key="task.id" class="task-item">
              <div class="task-preview">
                <img :src="task.thumbnail" :alt="task.name" />
              </div>
              <div class="task-info">
                <div class="task-name ellipsis">{{ task.name }}</div>
                <div class="task-time">{{ task.time }}</div>
                <div class="task-status" :class="task.status">{{ task.statusText }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧结果展示区域 -->
      <div class="right-panel">
        <!-- 结果展示标签页 -->
        <div class="results-tabs">
          <div class="tabs-header">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              :class="['tab-btn', { active: activeTab === tab.id }]"
              @click="activeTab = tab.id"
            >
              {{ tab.name }}
            </button>
            <div class="grid-controls" v-if="activeTab === 'original'">
              <label class="grid-toggle">
                <input type="checkbox" v-model="showGrid" />
                显示网格
              </label>
            </div>
            <div class="grid-controls" v-else-if="activeTab === 'heatmap' || activeTab === 'path'">
              <div class="opacity-control">
                <label>叠加透明度:</label>
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
            </div>
          </div>

          <!-- 标签页内容 -->
          <div class="tab-content">
            <!-- 原始地图标签页 -->
            <div v-if="activeTab === 'original'" class="tab-panel">
              <div v-if="selectedImage" class="result-display">
                <div class="result-header">
                  <h3>原始地图</h3>
                  <div class="result-actions">
                    <button class="action-btn" @click="showGrid = !showGrid">
                      {{ showGrid ? '隐藏' : '显示' }}网格
                    </button>
                  </div>
                </div>
                <div class="image-container" ref="imageContainer" @mousemove="handleMouseMove">
                  <img
                    v-if="selectedImage"
                    :src="selectedImage"
                    alt="原始地图"
                    class="result-image"
                    @load="onImageLoad"
                    ref="resultImage"
                  />

                  <!-- 网格叠加层 -->
                  <div v-if="showGrid" class="grid-overlay" :style="gridOverlayStyle">
                    <div
                      v-for="block in gridBlocks"
                      :key="block.id"
                      class="grid-block"
                      :style="{
                        width: block.width + '%',
                        height: block.height + '%',
                        left: block.left + '%',
                        top: block.top + '%',
                        backgroundColor: getBlockColor(block),
                      }"
                      @click="selectBlock(block)"
                      @mouseover="highlightBlock(block.id)"
                      @mouseout="highlightBlock(null)"
                    >
                      <div
                        class="block-label"
                        v-if="selectedBlock && selectedBlock.id === block.id"
                      >
                        {{ block.row }}, {{ block.col }}
                      </div>
                    </div>
                  </div>

                  <!-- 坐标信息 -->
                  <div v-if="mousePosition.x !== -1" class="mouse-coordinates">
                    X: {{ mousePosition.x }}, Y: {{ mousePosition.y }}
                  </div>
                </div>
                <div v-if="selectedBlock" class="block-info">
                  已选区块: 行 {{ selectedBlock.row }}, 列 {{ selectedBlock.col }}
                </div>
              </div>
              <div v-else class="no-result">
                <p>请先上传地图进行分析</p>
              </div>
            </div>

            <!-- 热力图标签页 -->
            <div v-else-if="activeTab === 'heatmap'" class="tab-panel">
              <div v-if="selectedImage" class="result-display">
                <div class="result-header">
                  <h3>威胁度热力图叠加</h3>
                  <div class="result-actions">
                    <button class="action-btn" @click="downloadImage('heatmap')">下载</button>
                  </div>
                </div>
                <div class="image-container" ref="heatmapImageContainer">
                  <img
                    v-if="selectedImage"
                    :src="selectedImage"
                    alt="原始地图"
                    class="result-image"
                    ref="heatmapBaseImage"
                  />
                  <img
                    v-if="analysisResult.heatmap"
                    :src="analysisResult.heatmap"
                    alt="热力图"
                    class="overlay-image"
                    :style="{
                      opacity: overlayOpacity / 100,
                    }"
                  />
                  <!-- 网格叠加层 -->
                  <div v-if="showGrid" class="grid-overlay" :style="gridOverlayStyle">
                    <div
                      v-for="block in gridBlocks"
                      :key="block.id"
                      class="grid-block"
                      :style="{
                        width: block.width + '%',
                        height: block.height + '%',
                        left: block.left + '%',
                        top: block.top + '%',
                        backgroundColor: getBlockColor(block),
                      }"
                      @click="selectBlock(block)"
                      @mouseover="highlightBlock(block.id)"
                      @mouseout="highlightBlock(null)"
                    >
                      <div
                        class="block-label"
                        v-if="selectedBlock && selectedBlock.id === block.id"
                      >
                        {{ block.row }}, {{ block.col }}
                      </div>
                    </div>
                  </div>
                </div>
                <div class="grid-controls" style="margin-top: 8px">
                  <label class="grid-toggle">
                    <input type="checkbox" v-model="showGrid" />
                    显示网格
                  </label>
                </div>
              </div>
              <div v-else class="no-result">
                <p>请先上传地图进行分析</p>
              </div>
            </div>

            <!-- 路径图标签页 -->
            <div v-else-if="activeTab === 'path'" class="tab-panel">
              <div v-if="selectedImage" class="result-display">
                <div class="result-header">
                  <h3>巡逻路线图叠加</h3>
                  <div class="result-actions">
                    <button class="action-btn" @click="downloadImage('path')">下载</button>
                    <button class="action-btn" @click="showPathDetails">路径详情</button>
                  </div>
                </div>
                <div class="image-container" ref="pathImageContainer">
                  <img
                    v-if="selectedImage"
                    :src="selectedImage"
                    alt="原始地图"
                    class="result-image"
                    ref="pathBaseImage"
                  />
                  <img
                    v-if="analysisResult.path"
                    :src="analysisResult.path"
                    alt="路径图"
                    class="overlay-image"
                    :style="{
                      opacity: overlayOpacity / 100,
                    }"
                  />
                  <!-- 网格叠加层 -->
                  <div v-if="showGrid" class="grid-overlay" :style="gridOverlayStyle">
                    <div
                      v-for="block in gridBlocks"
                      :key="block.id"
                      class="grid-block"
                      :style="{
                        width: block.width + '%',
                        height: block.height + '%',
                        left: block.left + '%',
                        top: block.top + '%',
                        backgroundColor: getBlockColor(block),
                      }"
                      @click="selectBlock(block)"
                      @mouseover="highlightBlock(block.id)"
                      @mouseout="highlightBlock(null)"
                    >
                      <div
                        class="block-label"
                        v-if="selectedBlock && selectedBlock.id === block.id"
                      >
                        {{ block.row }}, {{ block.col }}
                      </div>
                    </div>
                  </div>
                </div>
                <div class="grid-controls" style="margin-top: 8px">
                  <label class="grid-toggle">
                    <input type="checkbox" v-model="showGrid" />
                    显示网格
                  </label>
                </div>
              </div>
              <div v-else class="no-result">
                <p>请先上传地图进行分析</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 结果统计信息 -->
        <div v-if="analysisResult.stats" class="stats-card">
          <h3>分析统计</h3>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-icon">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <circle cx="12" cy="12" r="10"></circle>
                  <path
                    d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"
                  ></path>
                </svg>
              </div>
              <div class="stat-content">
                <span class="stat-label">最高威胁度</span>
                <span class="stat-value">{{ analysisResult.stats.maxThreat }}</span>
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-icon">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <line x1="12" y1="1" x2="12" y2="23"></line>
                  <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                </svg>
              </div>
              <div class="stat-content">
                <span class="stat-label">平均威胁度</span>
                <span class="stat-value">{{ analysisResult.stats.avgThreat }}</span>
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-icon">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <circle cx="12" cy="12" r="10"></circle>
                  <polyline points="12 6 12 12 16 14"></polyline>
                </svg>
              </div>
              <div class="stat-content">
                <span class="stat-label">分析用时</span>
                <span class="stat-value">{{ analysisResult.stats.time }} s</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 高威胁巡逻建议点表格 -->
        <div class="threat-points-card">
          <div class="threat-header">
            <h3>高威胁巡逻建议点</h3>
            <span v-if="filteredThreatPoints.length > 0" class="threat-count">
              共 {{ filteredThreatPoints.length }} 个建议点
            </span>
            <span v-else class="threat-count no-data"> 等待分析结果 </span>
          </div>

          <!-- 有威胁点数据时显示表格 -->
          <div v-if="filteredThreatPoints.length > 0" class="threat-points-table">
            <table>
              <thead>
                <tr>
                  <th>排序</th>
                  <th>所属区块</th>
                  <th>威胁度</th>
                  <th>图上坐标</th>
                  <th>威胁原因分析</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="point in filteredThreatPoints"
                  :key="point.id"
                  :class="getRowClass(point.threatScore)"
                >
                  <td class="rank-cell">
                    <span class="rank-badge" :class="getThreatColorClass(point.threatScore)">
                      {{ point.rank }}
                    </span>
                  </td>
                  <td class="block-cell">
                    <span class="block-badge">{{ point.block }}</span>
                  </td>
                  <td class="threat-score-cell">
                    <span class="threat-score" :class="getThreatColorClass(point.threatScore)">
                      {{ point.threatScore.toFixed(1) }}
                    </span>
                  </td>
                  <td class="coordinate-cell">
                    <span class="coordinate">{{ point.coordinate }}</span>
                  </td>
                  <td class="reason-cell">
                    <div class="reason-text">{{ point.reason }}</div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 无威胁点数据时显示提示 -->
          <div v-else class="no-data-section">
            <div class="no-data-placeholder">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="48"
                height="48"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
              <p>威胁度分析统计将显示在此处</p>
              <p class="hint-text">请上传地图并进行智能分析，系统将自动检测高威胁巡逻建议点</p>
            </div>
          </div>

          <!-- 威胁统计数据 -->
          <div v-if="analysisResult.threatStats" class="threat-stats">
            <div class="threat-stat-item">
              <span class="stat-label">综合高危区域</span>
              <span class="stat-value">区块 {{ analysisResult.threatStats.topThreatBlock }}</span>
            </div>
            <div class="threat-stat-item">
              <span class="stat-label">威胁点分布</span>
              <span class="stat-value">{{ analysisResult.threatStats.distribution }}</span>
            </div>
            <div class="threat-stat-item">
              <span class="stat-label">建议优先巡逻</span>
              <span class="stat-value">{{ analysisResult.threatStats.priorityPatrol }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import axios from 'axios'
import { useUserStore } from '../../stores/userStore'

// 类型定义
interface AnalysisProgress {
  status: 'idle' | 'pending' | 'running' | 'completed' | 'failed'
  message: string
  progress_percent: number
}

interface AnalysisResult {
  heatmap: string
  path: string
  stats: {
    pathLength: string
    maxThreat: string
    avgThreat: string
    time: string
  } | null
  threatPoints: ThreatPoint[]
  threatStats: {
    topThreatBlock: string
    distribution: string
    priorityPatrol: string
  } | null
  _rawData?: any
}

interface ThreatPoint {
  id: number
  rank: number
  block: string
  threatScore: number
  coordinate: string
  location: string
  description: string
  reason: string
}

interface GridBlock {
  row: number
  col: number
  id: string
  width: number
  height: number
  left: number
  top: number
  selected: boolean
}

interface RecentTask {
  id: number
  name: string
  time: string
  status: 'success' | 'failed' | 'pending'
  statusText: string
  thumbnail: string
}

const userStore = useUserStore()

// ==================== API 配置 ====================
// 后端API基础URL - 修改为你的后端服务地址
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 480000, // 8分钟超时
})

// 请求拦截器 - 添加API密钥到请求头
apiClient.interceptors.request.use(
  (config) => {
    // 从localStorage获取API密钥
    const savedApiKey = localStorage.getItem('terrainav_api_key')
    if (savedApiKey) {
      config.headers['X-API-Key'] = savedApiKey
    }

    // 如果请求是 FormData，删除已存在的 Content-Type，让浏览器自动设置 boundary
    if (config.data instanceof FormData) {
      if (config.headers) {
        delete config.headers['Content-Type']
        delete config.headers['content-type']
      }
    } else {
      config.headers['Content-Type'] = 'application/json'
    }

    return config
  },
  (error) => Promise.reject(error),
)

// 响应拦截器 - 统一错误处理
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API请求错误:', error)
    if (error.response) {
      const message = error.response.data?.error || error.response.data?.message || '服务器错误'
      throw new Error(message)
    } else if (error.request) {
      throw new Error('无法连接到服务器，请检查后端服务是否运行')
    } else {
      throw new Error('请求失败: ' + error.message)
    }
  },
)

// ==================== API 方法 ====================

// 初始化API
const initApi = async (apiKey: string) => {
  const response = await apiClient.post('/api/init', { api_key: apiKey })
  return response.data
}

// 获取威胁数据（包含热力图和路径图）
const waitForTaskResult = async (taskId: string, interval: number = 2000, timeoutMs: number = 480000) => {
  const startTime = Date.now()
  while (true) {
    const response = await apiClient.get(`/api/task_status/${taskId}`)
    const data = response.data

    if (!data.success) {
      throw new Error(data.error || '查询任务状态失败')
    }

    analysisProgress.value = {
      status: data.status,
      message: data.progress || '正在分析中，请稍候...',
      progress_percent: data.progress_percent ?? analysisProgress.value.progress_percent,
    }

    if (data.status === 'completed') {
      return data.result
    }

    if (data.status === 'failed') {
      throw new Error(data.error || '分析任务执行失败')
    }

    if (Date.now() - startTime > timeoutMs) {
      throw new Error('任务超时，请稍后重试或尝试减少分析区域分块')
    }

    await new Promise((resolve) => setTimeout(resolve, interval))
  }
}

const fetchThreatData = async (divide: string, imageFile: File) => {
  const formData = new FormData()
  formData.append('divide', divide)
  formData.append('map_picture', imageFile)
  formData.append('start_point', droneParams.value.startPoint)

  const response = await apiClient.post('/api/get_threat_data', formData)
  const data = response.data

  if (!data.success) {
    throw new Error(data.error || '任务启动失败')
  }

  return await waitForTaskResult(data.task_id)
}

// ==================== 响应式数据 ====================
const selectedImage = ref('')
const selectedFileName = ref('')
const selectedFileSize = ref('')
const apiKey = ref('')
const analyzing = ref(false)
const overlayOpacity = ref(50) // 叠加透明度，默认50%
const analysisResult = ref<AnalysisResult>({
  heatmap: '',
  path: '',
  stats: null,
  threatPoints: [],
  threatStats: null,
})
const analysisProgress = ref<AnalysisProgress>({
  status: 'idle',
  message: '准备分析',
  progress_percent: 0,
})
const activeTab = ref('original')
const fileInput = ref<HTMLInputElement | null>(null)
const showGrid = ref(true)
const selectedBlockIndex = ref<number | null>(null)
const highlightedBlockIndex = ref<number | null>(null)
const imageNaturalSize = ref({ width: 0, height: 0 })
const imageDisplayArea = ref({ width: 0, height: 0, left: 0, top: 0 })
const mousePosition = ref({ x: -1, y: -1 })
const imageContainer = ref<HTMLDivElement | null>(null)
const heatmapImageContainer = ref<HTMLDivElement | null>(null)
const pathImageContainer = ref<HTMLDivElement | null>(null)
const resultImage = ref<HTMLImageElement | null>(null)
const heatmapBaseImage = ref<HTMLImageElement | null>(null)
const pathBaseImage = ref<HTMLImageElement | null>(null)

// 标签页配置
const tabs = [
  { id: 'original', name: '原始地图' },
  { id: 'heatmap', name: '热力图叠加' },
  { id: 'path', name: '路径图叠加' },
]

// 输出选项
const outputOptions = ref({
  heatmap: true,
  path: true,
  quality: 'high',
})

// 任务名称
const taskName = ref('')
// 无人机巡逻参数
const droneParams = ref({
  startPoint: '1,1',
  gridBlocks: '4 * 4',
})

// 最近任务列表
const recentTasks = ref<RecentTask[]>([])

// 计算属性
const canAnalyze = computed(() => {
  return selectedImage.value && apiKey.value && !analyzing.value
})

const analysisTip = computed(() => {
  if (!selectedImage.value) return '请上传地图图片'
  if (!apiKey.value) return '请输入API密钥'
  if (analyzing.value) return analysisProgress.value.message || '正在分析中，请稍候...'
  if (analysisProgress.value.status === 'completed') return analysisProgress.value.message || '分析完成'
  if (analysisProgress.value.status === 'failed') return analysisProgress.value.message || '分析失败'
  return '点击"开始智能分析"按钮进行分析'
})

// 解析巡逻区块输入
const parsedGridBlocks = computed(() => {
  if (!droneParams.value.gridBlocks) return { m: 0, n: 0 }

  const parts = droneParams.value.gridBlocks.split('*').map((part) => parseInt(part.trim()))
  if (parts.length !== 2 || parts[0] === undefined || parts[1] === undefined || isNaN(parts[0]) || isNaN(parts[1])) {
    return { m: 0, n: 0 }
  }

  return { m: parts[0] || 0, n: parts[1] || 0 }
})

// 验证巡逻区块格式
const gridBlocksValid = computed(() => {
  const { m, n } = parsedGridBlocks.value
  return (m ?? 0) > 0 && (n ?? 0) > 0
})

// 生成区块数据
const gridBlocks = computed<GridBlock[]>(() => {
  const { m, n } = parsedGridBlocks.value
  const blocks: GridBlock[] = []

  const rows = n ?? 0
  const cols = m ?? 0

  if (rows <= 0 || cols <= 0) return blocks

  for (let row = 0; row <= rows - 1; row++) {
    for (let col = 0; col <= cols - 1; col++) {
      blocks.push({
        row,
        col,
        id: `${row}-${col}`,
        width: 100 / cols,
        height: 100 / rows,
        left: (col * 100) / cols,
        top: ((rows - row - 1) * 100) / rows,
        selected: false,
      })
    }
  }

  return blocks
})

// 当前选中的区块
const selectedBlock = computed<GridBlock | null>(() => {
  if (selectedBlockIndex.value === null) return null
  return gridBlocks.value[selectedBlockIndex.value] || null
})

// 网格叠加层样式 - 精确覆盖图片区域
const gridOverlayStyle = computed(() => {
  if (!imageDisplayArea.value.width) return {}

  return {
    width: `${imageDisplayArea.value.width}px`,
    height: `${imageDisplayArea.value.height}px`,
    left: `${imageDisplayArea.value.left}px`,
    top: `${imageDisplayArea.value.top}px`,
  }
})

// 根据威胁度分数返回颜色类
const getThreatColorClass = (score: number) => {
  if (score >= 75) return 'score-red'
  if (score >= 60 && score < 75) return 'score-yellow'
  if (score >= 40 && score < 60) return 'score-green'
  return 'score-default'
}

// 根据威胁度分数返回行类
const getRowClass = (score: number) => {
  if (score >= 75) return 'high-threat-row'
  if (score >= 60 && score < 75) return 'medium-threat-row'
  if (score >= 40 && score < 60) return 'low-threat-row'
  return ''
}

// 获取区块颜色
const getBlockColor = (block: GridBlock) => {
  if (
    selectedBlockIndex.value !== null &&
    gridBlocks.value[selectedBlockIndex.value]?.id === block.id
  ) {
    return 'rgba(74, 108, 247, 0.3)'
  }
  if (
    highlightedBlockIndex.value !== null &&
    gridBlocks.value[highlightedBlockIndex.value]?.id === block.id
  ) {
    return 'rgba(74, 108, 247, 0.2)'
  }
  return 'rgba(255, 255, 255, 0.1)'
}

// 过滤威胁点，只显示40分及以上的
const filteredThreatPoints = computed(() => {
  if (!analysisResult.value.threatPoints || analysisResult.value.threatPoints.length === 0) {
    return []
  }
  return analysisResult.value.threatPoints
    .filter((point) => point.threatScore >= 40)
    .sort((a, b) => b.threatScore - a.threatScore)
    .map((point, index) => ({
      ...point,
      rank: index + 1,
    }))
})

// 方法
const triggerFileInput = () => {
  if (fileInput.value) {
    fileInput.value.click()
  }
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file && file.type.startsWith('image/')) {
    selectedFileName.value = file.name
    selectedFileSize.value = `${(file.size / 1024 / 1024).toFixed(2)} MB`

    const reader = new FileReader()
    reader.onload = (e) => {
      if (e.target?.result) {
        selectedImage.value = e.target.result as string
      }
    }
    reader.readAsDataURL(file)
  }
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  const file = event.dataTransfer?.files?.[0]
  if (file && file.type.startsWith('image/')) {
    selectedFileName.value = file.name
    selectedFileSize.value = `${(file.size / 1024 / 1024).toFixed(2)} MB`

    const reader = new FileReader()
    reader.onload = (e) => {
      if (e.target?.result) {
        selectedImage.value = e.target.result as string
      }
    }
    reader.readAsDataURL(file)
  }
}

// 计算图片实际显示区域
const calculateImageDisplayArea = () => {
  let img, container

  // 根据当前标签页选择对应的图片元素和容器
  switch (activeTab.value) {
    case 'original':
      img = resultImage.value
      container = imageContainer.value
      break
    case 'heatmap':
      img = heatmapBaseImage.value
      container = heatmapImageContainer.value
      break
    case 'path':
      img = pathBaseImage.value
      container = pathImageContainer.value
      break
    default:
      img = resultImage.value
      container = imageContainer.value
  }

  if (!img || !container) return

  // 获取图片和容器的实际尺寸
  const containerRect = container.getBoundingClientRect()

  // 获取图片的自然尺寸
  const imgNaturalWidth = img.naturalWidth || 1
  const imgNaturalHeight = img.naturalHeight || 1

  // 计算图片缩放比例（保持宽高比）
  const widthRatio = containerRect.width / imgNaturalWidth
  const heightRatio = containerRect.height / imgNaturalHeight
  const scale = Math.min(widthRatio, heightRatio, 1) // 不超过原始大小

  // 计算图片在容器中居中后的尺寸和位置
  const displayWidth = imgNaturalWidth * scale
  const displayHeight = imgNaturalHeight * scale
  const left = (containerRect.width - displayWidth) / 2
  const top = (containerRect.height - displayHeight) / 2

  imageDisplayArea.value = {
    width: displayWidth,
    height: displayHeight,
    left: left,
    top: top,
  }

  imageNaturalSize.value = {
    width: imgNaturalWidth,
    height: imgNaturalHeight,
  }
}

// 图片加载完成时的处理
const onImageLoad = () => {
  nextTick(() => {
    // 延迟一小段时间确保布局稳定
    setTimeout(() => {
      calculateImageDisplayArea()
    }, 50)
  })
}

// 窗口大小变化时重新计算显示区域
const handleResize = () => {
  calculateImageDisplayArea()
}

// 标签页切换时重新计算显示区域
watch(activeTab, () => {
  nextTick(() => {
    setTimeout(() => {
      calculateImageDisplayArea()
    }, 50)
  })
})

// 网格显示变更时同步到用户偏好
watch(showGrid, (val) => {
  userStore.updatePreferences({ gridDisplay: val })
})

// 鼠标移动事件处理
const handleMouseMove = (event: MouseEvent) => {
  if (!selectedImage.value || !imageDisplayArea.value.width) {
    mousePosition.value = { x: -1, y: -1 }
    return
  }

  const container = imageContainer.value
  if (!container) return

  const rect = container.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top

  // 转换为相对于图片显示区域的坐标
  const relativeX = x - imageDisplayArea.value.left
  const relativeY = y - imageDisplayArea.value.top

  // 确保鼠标在图片区域内
  if (
    relativeX >= 0 &&
    relativeX <= imageDisplayArea.value.width &&
    relativeY >= 0 &&
    relativeY <= imageDisplayArea.value.height
  ) {
    // 将容器坐标转换为图片坐标
    const imgX = Math.round(
      relativeX * (imageNaturalSize.value.width / imageDisplayArea.value.width),
    )
    const imgY = Math.round(
      relativeY * (imageNaturalSize.value.height / imageDisplayArea.value.height),
    )

    mousePosition.value = { x: imgX, y: imgY }
  } else {
    mousePosition.value = { x: -1, y: -1 }
  }
}

const validateGridBlocks = () => {
  const regex = /^\d+\s*\*\s*\d+$/
  if (!regex.test(droneParams.value.gridBlocks)) {
    return false
  }
  return true
}

// 测试API连接
const testApiKey = async () => {
  if (!apiKey.value) {
    alert('请输入API密钥')
    return
  }

  try {
    // 先保存到localStorage
    localStorage.setItem('terrainav_api_key', apiKey.value)

    // 调用初始化API
    const result = await initApi(apiKey.value)

    if (result.success) {
      alert('API密钥验证通过，连接成功！')
    } else {
      alert('API密钥验证失败: ' + (result.error || '未知错误'))
      localStorage.removeItem('terrainav_api_key')
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : '未知错误'
    alert('API密钥验证失败: ' + errorMessage)
    localStorage.removeItem('terrainav_api_key')
  }
}

// 选择区块
const selectBlock = (block: GridBlock) => {
  const index = gridBlocks.value.findIndex((b) => b.id === block.id)
  selectedBlockIndex.value = index
  console.log(`选中区块: 行 ${block.row}, 列 ${block.col}`)
}

// 高亮区块
const highlightBlock = (blockId: string | null) => {
  if (!blockId) {
    highlightedBlockIndex.value = null
    return
  }
  const index = gridBlocks.value.findIndex((b) => b.id === blockId)
  highlightedBlockIndex.value = index
}


// 开始分析 - 调用后端API
const startAnalysis = async () => {
  if (!canAnalyze.value) return

  analyzing.value = true
  const startTime = Date.now()

  try {
      analysisProgress.value = {
        status: 'pending',
        message: '任务已提交，等待后端处理...',
        progress_percent: 5,
      }

      // 确保API已初始化
      if (!localStorage.getItem('terrainav_api_key')) {
        localStorage.setItem('terrainav_api_key', apiKey.value)
      }

      // 获取divide参数 (格式: m*n)
      const divide = droneParams.value.gridBlocks.replace(/\s*/g, '')

      // 获取上传的图片文件
      const fileInputEl = fileInput.value
      const file = fileInputEl?.files?.[0]

      if (!file) {
        throw new Error('请先上传地图图片')
      }

      console.log('开始调用后端API...')
      console.log('divide:', divide)
      console.log('file:', file.name)

      // 调用后端API获取威胁数据
      const result = await fetchThreatData(divide, file)

      analysisProgress.value = {
        status: 'completed',
        message: '分析完成',
        progress_percent: 100,
      }

      const endTime = Date.now()
      const timeSeconds = ((endTime - startTime) / 1000).toFixed(1)

    // 处理威胁矩阵
    const threatMatrix = result.threat_matrix

    // 计算统计信息
    let maxThreat = 0
    let totalThreat = 0
    let count = 0
    if (threatMatrix && threatMatrix.length > 0) {
      for (const row of threatMatrix) {
        for (const val of row) {
          if (val && val > 0) {
            maxThreat = Math.max(maxThreat, val)
            totalThreat += val
            count++
          }
        }
      }
    }
    const avgThreat = count > 0 ? (totalThreat / count).toFixed(1) : '0.0'

    // 处理巡逻点数据
    const patrolPoints = result.patrol_points || []

    // 格式化威胁点数据用于显示
    const formattedThreatPoints: ThreatPoint[] = patrolPoints.map((pt: any, idx: number) => ({
      id: idx + 1,
      rank: pt.rank || idx + 1,
      block: pt.block || '',
      threatScore: pt.threat_score || 0,
      coordinate: pt.pixel_coords ? `${pt.pixel_coords[0]}, ${pt.pixel_coords[1]}` : '',
      location: pt.block_position || '',
      description: '',
      reason: pt.threat_reason || '',
    }))

    // 构建威胁统计
    const threatStats = {
      topThreatBlock: patrolPoints[0]?.block || '-',
      distribution: `共 ${patrolPoints.length} 个高威胁点`,
      priorityPatrol:
        patrolPoints
          .slice(0, 4)
          .map((p: any) => p.block)
          .join('、') || '-',
    }

    // 获取图片URL (需要拼接完整URL)
    const getImageUrl = (relativePath: string) => {
      if (!relativePath) return ''
      if (relativePath.startsWith('http')) return relativePath
      return `${API_BASE_URL}${relativePath}`
    }

    // 更新分析结果
    analysisResult.value = {
      heatmap: getImageUrl(result.heatmap_url || ''),
      path: getImageUrl(result.pathmap_url || ''),
      stats: {
        pathLength: result.best_path_length ? result.best_path_length.toFixed(1) : '0.0',
        maxThreat: maxThreat.toFixed(1),
        avgThreat: avgThreat,
        time: timeSeconds,
      },
      threatPoints: formattedThreatPoints,
      threatStats: threatStats,
      // 保存原始数据供后续使用
      _rawData: result,
    }

    // 保存API密钥
    localStorage.setItem('terrainav_api_key', apiKey.value)

    // 保存历史记录到数据库
    let savedToBackend = false
    if (userStore.user.id && userStore.user.id > 0) {
      try {
        const historyData = {
          user_id: userStore.user.id,
          task_name: taskName.value && taskName.value.trim()
            ? taskName.value.trim()
            : selectedFileName.value.replace(/\.[^/.]+$/, '') + '分析',
          description: `AI地形分析任务 - 识别到${patrolPoints.length}个巡逻点，路径长度${result.best_path_length?.toFixed(2) || 0}`,
          input_image_url: selectedImage.value,
          heatmap_url: getImageUrl(result.heatmap_url || ''),
          route_url: getImageUrl(result.pathmap_url || ''),
          report_url: '',
          task_status: 'completed',
          task_time: new Date().toISOString()
        }

        await axios.post(`${API_BASE_URL}/api/history`, historyData)
        console.log('历史记录保存成功')
        savedToBackend = true

        // 刷新最近任务列表（从数据库加载）
        await refreshTasks()
      } catch (historyError) {
        console.error('保存历史记录失败:', historyError)
      }
    }

    // 仅在前端未保存到数据库时，才将任务添加到本地显示（避免重复）
    if (!savedToBackend) {
      const newTask: RecentTask = {
        id: Date.now(),
        name:
          taskName.value && taskName.value.trim()
            ? taskName.value.trim()
            : selectedFileName.value.replace(/\.[^/.]+$/, '') + '分析',
        time: '刚刚',
        status: 'success',
        statusText: '完成',
        thumbnail: selectedImage.value,
      }
      recentTasks.value.unshift(newTask)
      if (recentTasks.value.length > 10) {
        recentTasks.value = recentTasks.value.slice(0, 10)
      }
    }

    console.log('分析完成!', analysisResult.value)

    // 切换到"热力图叠加"标签页
    activeTab.value = 'heatmap'

    alert(`分析完成！用时 ${timeSeconds} 秒`)
  } catch (error) {
    console.error('分析失败:', error)
    const errorMessage = error instanceof Error ? error.message : '分析失败，请检查后端日志'
    analysisProgress.value = {
      status: 'failed',
      message: errorMessage,
      progress_percent: 100,
    }
    alert('分析失败: ' + errorMessage)

    // 添加失败任务
    const failedTask: RecentTask = {
      id: Date.now(),
      name: selectedFileName.value.replace(/\.[^/.]+$/, '') + '分析',
      time: '刚刚',
      status: 'failed',
      statusText: '失败',
      thumbnail: selectedImage.value,
    }
    recentTasks.value.unshift(failedTask)
  } finally {
    analyzing.value = false
  }
}

// 显示路径详情
const showPathDetails = () => {
  const rawData = analysisResult.value._rawData
  if (rawData && rawData.path_coords) {
    const pathCoords = rawData.path_coords as number[][]
    let message = `路径坐标点 (共 ${pathCoords.length} 个):\n\n`
    pathCoords.forEach((coord: number[], idx: number) => {
      message += `${idx + 1}. (${coord[0]}, ${coord[1]})\n`
    })
    if (rawData.best_path_length !== undefined && rawData.best_path_length !== null) {
      message += `\n总路径长度: ${rawData.best_path_length.toFixed(2)}`
    }
    alert(message)
  } else {
    alert('暂无路径数据')
  }
}

// 下载图片
const downloadImage = async (type: 'heatmap' | 'path') => {
  const url = type === 'heatmap' ? analysisResult.value.heatmap : analysisResult.value.path

  if (!url) {
    alert('没有可下载的图片')
    return
  }

  try {
    // 显示下载提示
    alert(`正在下载${type === 'heatmap' ? '热力图' : '路径图'}...`)

    // 创建下载链接
    const link = document.createElement('a')
    link.href = url
    link.download = `${selectedFileName.value.replace(/\.[^/.]+$/, '')}_${type}_${new Date().getTime()}.png`
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    alert(`下载${type === 'heatmap' ? '热力图' : '路径图'}成功！`)
  } catch (error) {
    console.error('下载失败:', error)
    const errorMessage = error instanceof Error ? error.message : '未知错误'
    alert('下载失败: ' + errorMessage)
  }
}

const refreshTasks = async () => {
  if (!userStore.user.id || userStore.user.id <= 0) {
    console.log('用户未登录，无法加载最近任务')
    return
  }

  try {
    const response = await axios.get(`${API_BASE_URL}/api/history/recent`, {
      params: {
        user_id: userStore.user.id,
        limit: 3
      }
    })

    if (response.data.success) {
      recentTasks.value = response.data.histories
      console.log('最近任务加载成功:', recentTasks.value)
    } else {
      console.error('加载最近任务失败:', response.data.error)
    }
  } catch (error) {
    console.error('加载最近任务失败:', error)
  }
}

onMounted(() => {
  // 加载API密钥
  const savedApiKey = localStorage.getItem('terrainav_api_key')
  if (savedApiKey) {
    apiKey.value = savedApiKey
  }

  // 加载无人机默认参数（由系统设置页保存）
  const savedDroneParams = localStorage.getItem('terrainav_drone_params')
  if (savedDroneParams) {
    try {
      const params = JSON.parse(savedDroneParams)
      if (params.gridBlocks) droneParams.value.gridBlocks = params.gridBlocks
      if (params.startPoint) droneParams.value.startPoint = params.startPoint
    } catch {
      // 解析失败则使用默认值
    }
  }

  // 加载偏好设置
  showGrid.value = userStore.preferences.gridDisplay !== false
  overlayOpacity.value = userStore.preferences.showHeatmapLegend !== false ? 50 : 0

  window.addEventListener('resize', handleResize)

  // 加载最近任务
  refreshTasks()

  // 初始计算
  nextTick(() => {
    calculateImageDisplayArea()
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.ellipsis {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  display: block;
}

.dashboard {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  min-height: 100vh;
}

.dashboard-header {
  background: linear-gradient(90deg, #1a2980, #26d0ce);
  color: white;
  padding: 1.5rem 2rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 1.5rem;
}

.dashboard-header h1 {
  font-size: 1.8rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  color: white;
}

.dashboard-header p {
  font-size: 1rem;
  margin: 0;
  opacity: 0.9;
  color: #e0f7fa;
}

.dashboard-content {
  display: flex;
  flex: 1;
  gap: 1.5rem;
  padding: 0 1.5rem 1.5rem;
  max-width: 1600px;
  margin: 0 auto;
  width: 100%;
  overflow: auto;
}

.left-panel {
  width: 320px;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  flex-shrink: 0;
  min-width: 320px;
}

.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  min-width: 0;
  overflow: auto;
}

/* 上传卡片 */
.upload-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
}

.card-title {
  font-size: 1.4rem;
  color: #1a2980;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.card-subtitle {
  color: #6b7280;
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
}

.upload-area {
  border: 2px dashed #c3cfe2;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #f8fafc;
  margin-bottom: 1.5rem;
  min-height: 180px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.upload-area:hover {
  border-color: #4a6cf7;
  background: #f0f4ff;
}

.upload-placeholder p {
  margin: 0.5rem 0;
  color: #4b5563;
}

.upload-hint {
  font-size: 0.8rem;
  color: #9ca3af;
  margin-top: 0.5rem;
}

.upload-preview {
  width: 100%;
}

.preview-image {
  width: 100%;
  height: 120px;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 0.8rem;
}

.preview-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-info p {
  margin: 0.3rem 0;
  color: #4b5563;
  font-size: 0.9rem;
  text-align: center;
}

/* API配置 */
.api-config {
  margin-bottom: 1.5rem;
}

.api-config h3 {
  font-size: 1rem;
  color: #374151;
  margin-bottom: 0.8rem;
  font-weight: 600;
}

.api-input {
  width: 100%;
  padding: 0.8rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9rem;
  margin-bottom: 0.8rem;
  transition: border-color 0.3s;
}

.api-input:focus {
  outline: none;
  border-color: #4a6cf7;
  box-shadow: 0 0 0 3px rgba(74, 108, 247, 0.1);
}

.api-test-btn {
  width: 100%;
  background: #f3f4f6;
  color: #4b5563;
  border: 1px solid #d1d5db;
  padding: 0.6rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.api-test-btn:hover {
  background: #e5e7eb;
  color: #374151;
}

/* 输出选项 */
.output-options {
  margin-bottom: 1.5rem;
}

.output-options h3 {
  font-size: 1rem;
  color: #374151;
  margin-bottom: 0.8rem;
  font-weight: 600;
}

.option-group {
  margin-bottom: 1.2rem;
}

.option-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #4b5563;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
  cursor: pointer;
}

.option-group h4 {
  font-size: 0.9rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.quality-select {
  width: 100%;
  padding: 0.6rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9rem;
  background: white;
  cursor: pointer;
}

/* 无人机巡逻参数 */
.drone-params {
  margin-bottom: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.drone-params h3 {
  font-size: 1rem;
  color: #374151;
  margin-bottom: 0.8rem;
  font-weight: 600;
}

.param-group {
  margin-bottom: 1rem;
}

.param-group label {
  display: block;
  font-size: 0.9rem;
  color: #4b5563;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.param-input {
  width: 100%;
  padding: 0.6rem 0.8rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9rem;
  background: white;
  transition: border-color 0.3s;
}

.param-input:focus {
  outline: none;
  border-color: #4a6cf7;
  box-shadow: 0 0 0 3px rgba(74, 108, 247, 0.1);
}

.param-hint {
  font-size: 0.8rem;
  color: #9ca3af;
  margin-top: 0.3rem;
  line-height: 1.3;
}

.grid-info {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #f0f9ff;
  border-radius: 4px;
  border: 1px solid #bae6fd;
  color: #0369a1;
  font-size: 0.85rem;
  font-weight: 500;
}

.error-message {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #fef2f2;
  border-radius: 4px;
  border: 1px solid #fecaca;
  color: #dc2626;
  font-size: 0.85rem;
}

/* 开始分析按钮 */
.analyze-btn {
  width: 100%;
  background: linear-gradient(90deg, #1a2980, #26d0ce);
  color: white;
  border: none;
  padding: 1rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 1rem;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
}

.analyze-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(26, 41, 128, 0.2);
}

.analyze-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.analyzing {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.spinner {
  animation: rotate 1s linear infinite;
  height: 20px;
  width: 20px;
}

.spinner circle {
  animation: dash 1.5s ease-in-out infinite;
}

@keyframes rotate {
  100% {
    transform: rotate(360deg);
  }
}

@keyframes dash {
  0% {
    stroke-dasharray: 1, 150;
    stroke-dashoffset: 0;
  }
  50% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -35;
  }
  100% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -124;
  }
}

.analysis-progress {
  margin-top: 1rem;
}

.progress-text {
  font-size: 0.9rem;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.progress-bar {
  width: 100%;
  height: 8px;
  border-radius: 9999px;
  background: #e5e7eb;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #1a2980, #26d0ce);
  transition: width 0.3s ease;
}

.analysis-tip {
  margin-top: 1rem;
  padding: 0.8rem;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 6px;
  color: #0369a1;
  font-size: 0.85rem;
  text-align: center;
}

/* 最近任务 */
.recent-tasks {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
}

.tasks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.tasks-header h3 {
  font-size: 1rem;
  color: #374151;
  font-weight: 600;
}

.refresh-btn {
  background: none;
  border: 1px solid #d1d5db;
  color: #6b7280;
  padding: 0.3rem 0.8rem;
  border-radius: 4px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.task-item {
  display: flex;
  gap: 0.8rem;
  padding: 0.8rem;
  border-radius: 8px;
  transition: background-color 0.2s;
  cursor: pointer;
}

.task-item:hover {
  background: #f9fafb;
}

.task-preview {
  width: 60px;
  height: 60px;
  border-radius: 6px;
  overflow: hidden;
  flex-shrink: 0;
}

.task-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.task-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.task-name {
  font-weight: 500;
  color: #374151;
  font-size: 0.9rem;
  margin-bottom: 0.2rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 80%;
}

.task-time {
  color: #9ca3af;
  font-size: 0.8rem;
  margin-bottom: 0.2rem;
}

.task-status {
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  border-radius: 12px;
  display: inline-block;
  width: fit-content;
}

.task-status.success {
  background: #d1fae5;
  color: #065f46;
}

.task-status.processing {
  background: #fef3c7;
  color: #92400e;
}

/* 结果标签页 */
.results-tabs {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 500px;
}

.tabs-header {
  display: flex;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  padding: 0.5rem 1.5rem;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}

.tab-btn {
  padding: 0.8rem 1.5rem;
  background: none;
  border: none;
  color: #6b7280;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  position: relative;
  transition: color 0.3s;
  white-space: nowrap;
}

.tab-btn:hover {
  color: #1a2980;
}

.tab-btn.active {
  color: #1a2980;
  font-weight: 600;
}

.tab-btn.active::after {
  content: '';
  position: absolute;
  bottom: -0.5rem;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #1a2980, #26d0ce);
  border-radius: 1px;
}

.grid-controls {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.grid-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #4b5563;
  cursor: pointer;
}

.opacity-control {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #4b5563;
}

.opacity-slider {
  width: 100px;
  cursor: pointer;
}

.tab-content {
  flex: 1;
  padding: 1.5rem;
  overflow: auto;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.tab-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1;
  min-height: 0;
}

.result-display {
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1;
  min-height: 0;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.8rem;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.result-header h3 {
  font-size: 1.2rem;
  color: #1a2980;
  font-weight: 600;
  margin: 0;
}

.result-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  align-items: center;
}

.action-btn {
  background: white;
  border: 1px solid #d1d5db;
  color: #6b7280;
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.action-btn:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
  color: #374151;
}

/* 图片容器 - 修改为居中显示 */
.image-container {
  background: #f9fafb;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
  min-height: 400px;
  width: 100%;
  cursor: crosshair;
  padding: 0rem;
  position: relative;
}

.result-image,
.overlay-image {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
  display: block;
}

.overlay-image {
  position: absolute;
  top: 50%;
  left: 0;
  transform: translateY(-50%);
  pointer-events: none;
  opacity: 0.5;
  transition: opacity 0.3s ease;
}

.no-result {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #9ca3af;
  font-size: 1.1rem;
  background: #f9fafb;
  border-radius: 8px;
  padding: 2rem;
}

.grid-overlay {
  position: absolute;
  pointer-events: none;
  z-index: 10;
}

.grid-block {
  position: absolute;
  border: 1px solid rgba(74, 108, 247, 0.3);
  box-sizing: border-box;
  cursor: pointer;
  pointer-events: auto;
  transition: all 0.2s;
  display: flex;
  justify-content: center;
  align-items: center;
}

.grid-block:hover {
  border-width: 2px;
  border-color: #4a6cf7;
  background-color: rgba(74, 108, 247, 0.2) !important;
}

.block-label {
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
  pointer-events: none;
}

.block-info {
  margin-top: 1rem;
  padding: 0.8rem;
  background: #f0f9ff;
  border-radius: 6px;
  border: 1px solid #bae6fd;
  color: #0369a1;
  font-size: 0.9rem;
  text-align: center;
  flex-shrink: 0;
}

/* 鼠标坐标显示 */
.mouse-coordinates {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-family: monospace;
  z-index: 20;
  pointer-events: none;
}

/* 统计信息卡片 */
.stats-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.stats-card h3 {
  font-size: 1.2rem;
  color: #1a2980;
  margin-bottom: 1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 1rem;
  background: linear-gradient(135deg, #f8fafc, #f1f5f9);
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #1a2980, #26d0ce);
  border-radius: 8px;
  color: white;
  flex-shrink: 0;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 0.85rem;
  color: #6b7280;
  margin-bottom: 0.3rem;
}

.stat-value {
  font-size: 1.2rem;
  color: #1a2980;
  font-weight: 600;
}

/* 高威胁巡逻建议点卡片 */
.threat-points-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
  flex-shrink: 0;
  max-height: 600px;
  overflow-y: auto;
  min-height: 300px;
}

.threat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 0.8rem;
  border-bottom: 2px solid #e5e7eb;
}

.threat-header h3 {
  font-size: 1.2rem;
  color: #1a2980;
  font-weight: 600;
  margin: 0;
}

.threat-count {
  background: linear-gradient(90deg, #1a2980, #26d0ce);
  color: white;
  padding: 0.4rem 1rem;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
}

.threat-count.no-data {
  background: #e5e7eb;
  color: #6b7280;
}

/* 无威胁点数据时的提示样式 */
.no-data-section {
  padding: 3rem 1rem;
  text-align: center;
  color: #6b7280;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px dashed #d1d5db;
  margin-bottom: 1.5rem;
}

.no-data-placeholder svg {
  color: #9ca3af;
  margin-bottom: 1rem;
}

.no-data-placeholder p {
  font-size: 1.1rem;
  color: #374151;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.hint-text {
  font-size: 0.9rem;
  color: #6b7280;
  max-width: 400px;
  margin: 0 auto;
  line-height: 1.5;
}

/* 威胁点表格样式 */
.threat-points-table {
  width: 100%;
  overflow-x: auto;
  margin-bottom: 1.5rem;
}

.threat-points-table table {
  width: 100%;
  border-collapse: collapse;
  min-width: 800px;
}

.threat-points-table th {
  background: #f9fafb;
  color: #374151;
  font-weight: 600;
  font-size: 0.9rem;
  text-align: left;
  padding: 0.8rem 1rem;
  border-bottom: 2px solid #e5e7eb;
  position: sticky;
  top: 0;
  z-index: 10;
}

.threat-points-table td {
  padding: 0.8rem 1rem;
  border-bottom: 1px solid #e5e7eb;
  font-size: 0.9rem;
  vertical-align: top;
}

.threat-points-table tbody tr:hover {
  background-color: #f8fafc;
}

/* 行样式 - 根据威胁度分数 */
.high-threat-row {
  background-color: rgba(254, 226, 226, 0.1);
  border-left: 3px solid #ef4444;
}

.high-threat-row:hover {
  background-color: rgba(254, 226, 226, 0.2);
}

.medium-threat-row {
  background-color: rgba(254, 240, 199, 0.1);
  border-left: 3px solid #f59e0b;
}

.medium-threat-row:hover {
  background-color: rgba(254, 240, 199, 0.2);
}

.low-threat-row {
  background-color: rgba(209, 250, 229, 0.1);
  border-left: 3px solid #10b981;
}

.low-threat-row:hover {
  background-color: rgba(209, 250, 229, 0.2);
}

/* 排名单元格 */
.rank-cell {
  width: 60px;
  text-align: center;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  font-weight: 600;
  font-size: 0.9rem;
  color: white;
}

/* 颜色分类样式 */
.score-red {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.8), rgba(220, 38, 38, 0.8));
  box-shadow: 0 2px 4px rgba(239, 68, 68, 0.3);
}

.score-yellow {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.8), rgba(217, 119, 6, 0.8));
  box-shadow: 0 2px 4px rgba(245, 158, 11, 0.3);
}

.score-green {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.8), rgba(5, 150, 105, 0.8));
  box-shadow: 0 2px 4px rgba(16, 185, 129, 0.3);
}

.score-default {
  background: #e5e7eb;
  color: #4b5563;
}

/* 区块单元格 */
.block-cell {
  width: 90px;
}

.block-badge {
  display: inline-block;
  background: #dbeafe;
  color: #1d4ed8;
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.85rem;
  border: 1px solid #bfdbfe;
}

/* 威胁分数单元格 */
.threat-score-cell {
  width: 80px;
}

.threat-score {
  display: inline-block;
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  font-weight: 600;
  font-size: 1rem;
  text-align: center;
  min-width: 60px;
  color: white;
}

/* 坐标单元格 */
.coordinate-cell {
  width: 100px;
}

.coordinate {
  display: inline-block;
  background: #f3f4f6;
  color: #4b5563;
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.85rem;
  border: 1px solid #e5e7eb;
}

/* 原因分析单元格 */
.reason-cell {
  min-width: 200px;
  max-width: 300px;
}

.reason-text {
  color: #4b5563;
  font-size: 0.85rem;
  line-height: 1.4;
  white-space: normal;
  word-break: break-word;
}

/* 威胁点统计 */
.threat-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
  margin-top: 1rem;
}

.threat-stat-item {
  display: flex;
  flex-direction: column;
  padding: 0.8rem;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.threat-stat-item .stat-label {
  font-size: 0.8rem;
  color: #6b7280;
  margin-bottom: 0.3rem;
}

.threat-stat-item .stat-value {
  font-size: 1rem;
  color: #1a2980;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .dashboard-content {
    flex-direction: column;
  }

  .left-panel {
    width: 100%;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .threat-stats {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dashboard-header {
    padding: 1rem;
  }

  .dashboard-content {
    padding: 1rem;
  }

  .tabs-header {
    flex-wrap: wrap;
  }

  .grid-controls {
    order: 3;
    width: 100%;
    margin-top: 0.5rem;
    margin-left: 0;
  }

  .result-actions {
    flex-wrap: wrap;
  }

  .image-container {
    min-height: 300px;
  }

  .threat-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .threat-count {
    align-self: flex-start;
  }
}
</style>
