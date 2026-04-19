<template>
  <div class="dashboard">
    <!-- 顶部导航栏 -->
    <header class="app-header">
      <div class="header-left">
        <div class="logo">
          <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#1a2980" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
            <polyline points="9 22 9 12 15 12 15 22"></polyline>
          </svg>
          <span class="app-name">TerraiNav地形适应无人机巡逻系统</span>
        </div>
        <nav class="main-nav">
          <a href="#" class="nav-item active">地图分析</a>
          <a href="#" class="nav-item">历史记录</a>
          <a href="#" class="nav-item">系统设置</a>
          <a href="#" class="nav-item">使用教程</a>
        </nav>
      </div>
      <div class="header-right">
        <div class="user-info">
          <span>管理员</span>
          <button class="logout-btn" @click="handleLogout">退出</button>
        </div>
      </div>
    </header>

    <main class="dashboard-content">
      <!-- 左侧上传和配置面板 -->
      <div class="left-panel">
        <div class="upload-card">
          <h2 class="card-title">上传地图</h2>
          <p class="card-subtitle">上传地形图片进行智能威胁度分析</p>
          
          <div class="upload-area" @click="triggerFileInput" @dragover.prevent @drop.prevent="handleDrop">
            <div v-if="!selectedImage" class="upload-placeholder">
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#4a6cf7" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1-2-2h7"></path>
                <line x1="16" y1="5" x2="22" y2="5"></line>
                <line x1="19" y1="2" x2="19" y2="8"></line>
                <circle cx="9" cy="9" r="2"></circle>
                <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"></path>
              </svg>
              <p>点击或拖拽上传地形图片</p>
              <p class="upload-hint">支持 JPG、PNG 格式，最大 24MB</p>
            </div>
            <div v-else class="upload-preview">
              <div class="preview-image">
                <img :src="selectedImage" alt="已选地图" />
              </div>
              <div class="preview-info">
                <p>已选择：{{ selectedFileName }}</p>
                <p>{{ selectedFileSize }}</p>
              </div>
            </div>
            <input 
              ref="fileInput"
              type="file"
              accept="image/*"
              @change="handleFileSelect"
              style="display: none"
            />
          </div>
          
          <!-- API密钥配置 -->
          <div class="api-config">
            <h3>API配置</h3>
            <input 
              v-model="apiKey"
              type="password"
              placeholder="请输入百度千帆API密钥"
              class="api-input"
            />
            <button class="api-test-btn" @click="testApiKey">验证密钥</button>
          </div>
          
          <!-- 输出选项 -->
          <div class="output-options">
            <h3>输出设置</h3>
            <div class="option-group">
              <label>
                <input type="checkbox" v-model="outputOptions.heatmap" /> 威胁度热力图
              </label>
              <label>
                <input type="checkbox" v-model="outputOptions.path" /> 巡逻路线图
              </label>
            </div>
            <div class="option-group">
              <h4>输出质量</h4>
              <select v-model="outputOptions.quality" class="quality-select">
                <option value="high">高清 (1920×1080)</option>
                <option value="medium">标准 (1280×720)</option>
                <option value="low">快速 (960×540)</option>
              </select>
            </div>
          </div>
          
          <!-- 新增：无人机巡逻参数配置 -->
          <div class="drone-params">
            <h3>无人机巡逻参数</h3>
            
            <!-- 无人机巡逻半径 -->
            <div class="param-group">
              <label for="patrol-radius">巡逻半径 (米)</label>
              <input 
                id="patrol-radius"
                v-model="droneParams.patrolRadius"
                type="number"
                placeholder="例如：1000"
                min="100"
                max="10000"
                class="param-input"
              />
              <div class="param-hint">无人机单次巡逻覆盖范围</div>
            </div>
            
            <!-- 巡逻起点 -->
            <div class="param-group">
              <label for="start-point">巡逻起点 (x,y)</label>
              <input 
                id="start-point"
                v-model="droneParams.startPoint"
                type="text"
                placeholder="例如：100,200"
                class="param-input"
              />
              <div class="param-hint">地图坐标系中的起始位置</div>
            </div>
            
            <!-- 巡逻区块数量 -->
            <div class="param-group">
              <label for="grid-blocks">巡逻区块数量 (M*N)</label>
              <input 
                id="grid-blocks"
                v-model="droneParams.gridBlocks"
                type="text"
                placeholder="例如：4 * 4"
                class="param-input"
                @input="validateGridBlocks"
              />
              <div class="param-hint">将巡逻区域划分为 M(横向)×N(纵向) 个区块</div>
              <div v-if="gridBlocksValid" class="grid-info">
                <span>已划分: {{ parsedGridBlocks.m }}×{{ parsedGridBlocks.n }} 个区块</span>
              </div>
              <div v-else class="error-message">
                格式错误，请输入 M*N 格式，如 4 * 4
              </div>
            </div>
          </div>
          
          <!-- 开始分析按钮 -->
          <button 
            class="analyze-btn" 
            :disabled="!canAnalyze" 
            @click="startAnalysis"
          >
            <span v-if="!analyzing">开始智能分析</span>
            <span v-else class="analyzing">
              <svg class="spinner" viewBox="0 0 50 50">
                <circle cx="25" cy="25" r="20" fill="none" stroke="currentColor" stroke-width="5"></circle>
              </svg>
              分析中...
            </span>
          </button>
          
          <!-- 提示信息 -->
          <div v-if="analysisTip" class="analysis-tip">
            <p>{{ analysisTip }}</p>
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
                <p class="task-name">{{ task.name }}</p>
                <p class="task-time">{{ task.time }}</p>
                <p class="task-status" :class="task.status">{{ task.statusText }}</p>
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
          </div>
          
          <!-- 原图标签 -->
          <div v-if="activeTab === 'original'" class="tab-content">
            <!-- 当有图片时显示结果展示区域 -->
            <div v-if="selectedImage" class="result-display">
              <div class="result-header">
                <h3>原始地图</h3>
                <div class="result-actions">
                  <button class="action-btn" @click="downloadImage('original')">下载</button>
                  <button class="action-btn" @click="zoomIn">放大</button>
                  <button class="action-btn" @click="zoomOut">缩小</button>
                  <button class="action-btn" @click="toggleGrid">网格 {{ showGrid ? '隐藏' : '显示' }}</button>
                </div>
              </div>
              
              <div class="image-container" :class="{ 'has-image': selectedImage }" ref="imageContainer">
                <img 
                  v-if="selectedImage" 
                  :src="selectedImage" 
                  alt="原始地图" 
                  ref="mapImage"
                  @load="onImageLoad"
                />
                
                <!-- 巡逻区块网格 - 使用图片的实际显示区域 -->
                <div 
                  v-if="showGrid && gridBlocksValid && imageDisplayArea.width > 0" 
                  class="grid-overlay"
                  :style="{
                    width: imageDisplayArea.width + 'px',
                    height: imageDisplayArea.height + 'px',
                    left: imageDisplayArea.left + 'px',
                    top: imageDisplayArea.top + 'px'
                  }"
                >
                  <div 
                    v-for="(block, index) in gridBlocks" 
                    :key="index"
                    class="grid-block"
                    :style="getBlockStyle(block)"
                    @mouseenter="highlightBlock(block)"
                    @mouseleave="unhighlightBlock(block)"
                    @click="selectBlock(block)"
                    :class="{ 
                      selected: selectedBlockIndex === index,
                      highlighted: highlightedBlockIndex === index
                    }"
                  >
                    <span class="block-label">{{ block.row }}-{{ block.col }}</span>
                  </div>
                </div>
                
                <!-- 无图片时的提示 -->
                <div v-if="!selectedImage" class="no-result">
                  <p>请先上传地图进行分析</p>
                </div>
              </div>
              
              <!-- 区块统计信息 -->
              <div v-if="gridBlocksValid && showGrid" class="grid-stats">
                <h4>区块统计</h4>
                <div class="stats-details">
                  <p>总计区块: {{ parsedGridBlocks.m * parsedGridBlocks.n }} 个</p>
                  <p>区块尺寸: {{ parsedGridBlocks.m }}×{{ parsedGridBlocks.n }}</p>
                  <p v-if="selectedBlockIndex !== null">选中区块: {{ selectedBlock.row }}-{{ selectedBlock.col }}</p>
                  <p v-if="imageDisplayArea.width > 0">图片显示区域: {{ imageDisplayArea.width.toFixed(0) }}×{{ imageDisplayArea.height.toFixed(0) }}px</p>
                </div>
              </div>
            </div>
            
            <!-- 当无图片时显示提示 -->
            <div v-else class="no-result">
              <p>请先上传地图进行分析</p>
            </div>
          </div>
          
          <!-- 热力图标签 -->
          <div v-if="activeTab === 'heatmap'" class="tab-content">
            <div v-if="analysisResult.heatmap" class="result-display">
              <div class="result-header">
                <h3>威胁度热力图叠加</h3>
                <div class="result-actions">
                  <button class="action-btn" @click="downloadImage('heatmap')">下载</button>
                  <button class="action-btn" @click="toggleHeatmapLegend">图例</button>
                </div>
              </div>
              <div class="image-container" :class="{ 'has-image': analysisResult.heatmap }">
                <img v-if="analysisResult.heatmap" :src="analysisResult.heatmap" alt="威胁度热力图" />
                <div v-if="showHeatmapLegend" class="heatmap-legend">
                  <div class="legend-gradient"></div>
                  <div class="legend-labels">
                    <span>低威胁</span>
                    <span>高威胁</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="no-result">
              <p>暂无热力图数据，请先进行分析</p>
            </div>
          </div>
          
          <!-- 路径图标签 -->
          <div v-if="activeTab === 'path'" class="tab-content">
            <div v-if="analysisResult.path" class="result-display">
              <div class="result-header">
                <h3>巡逻路线图叠加</h3>
                <div class="result-actions">
                  <button class="action-btn" @click="downloadImage('path')">下载</button>
                  <button class="action-btn" @click="showPathDetails">详情</button>
                </div>
              </div>
              <div class="image-container" :class="{ 'has-image': analysisResult.path }">
                <img v-if="analysisResult.path" :src="analysisResult.path" alt="巡逻路线图" />
              </div>
            </div>
            <div v-else class="no-result">
              <p>暂无路径规划数据，请先进行分析</p>
            </div>
          </div>
        </div>
        
        <!-- 结果统计信息 -->
        <div v-if="analysisResult.stats" class="results-stats">
          <h3>分析统计</h3>
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-label">路径长度</span>
              <span class="stat-value">{{ analysisResult.stats.pathLength }} m</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">最高威胁度</span>
              <span class="stat-value">{{ analysisResult.stats.maxThreat }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">平均威胁度</span>
              <span class="stat-value">{{ analysisResult.stats.avgThreat }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">分析用时</span>
              <span class="stat-value">{{ analysisResult.stats.time }} s</span>
            </div>
          </div>
        </div>
      </div>
    </main>
    
    <!-- 底部版权信息 -->
    <footer class="app-footer">
      <div class="footer-content">
        <p>© 2024 TerraiNav 地形适应无人机巡逻系统. 版权所有.</p>
        <p>技术支持邮箱: support@terrainav.com | 服务热线: 400-123-4567</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 响应式数据
const selectedImage = ref('')
const selectedFileName = ref('')
const selectedFileSize = ref('')
const apiKey = ref('')
const analyzing = ref(false)
const analysisResult = ref({
  heatmap: '',
  path: '',
  stats: null
})
const showHeatmapLegend = ref(true)
const activeTab = ref('original')
const fileInput = ref(null)
const mapImage = ref(null)
const imageContainer = ref(null)
const showGrid = ref(false)
const selectedBlockIndex = ref(null)
const highlightedBlockIndex = ref(null)
const imageNaturalSize = ref({ width: 0, height: 0 })
const imageDisplayArea = ref({ width: 0, height: 0, left: 0, top: 0 })

// 标签页配置
const tabs = [
  { id: 'original', name: '原始地图' },
  { id: 'heatmap', name: '威胁度热力图' },
  { id: 'path', name: '巡逻路线图' }
]

// 输出选项
const outputOptions = ref({
  heatmap: true,
  path: true,
  quality: 'high'
})

// 无人机巡逻参数
const droneParams = ref({
  patrolRadius: 1000,
  startPoint: '100,200',
  gridBlocks: '4 * 4'  // 默认4 * 4个区块
})

// 最近任务（模拟数据）
const recentTasks = ref([
  { id: 1, name: '山区地形分析', time: '今天 14:30', status: 'success', statusText: '完成', thumbnail: '/pictures/background1.jpg' },
  { id: 2, name: '城区巡逻路径', time: '昨天 10:15', status: 'processing', statusText: '处理中', thumbnail: '/pictures/background1.jpg' },
  { id: 3, name: '森林区域评估', time: '前天 16:45', status: 'success', statusText: '完成', thumbnail: '/pictures/background1.jpg' }
])

// 计算属性
const canAnalyze = computed(() => {
  return selectedImage.value && apiKey.value && !analyzing.value
})

const analysisTip = computed(() => {
  if (!selectedImage.value) return '请上传地图图片'
  if (!apiKey.value) return '请输入API密钥'
  if (analyzing.value) return '正在分析中，请稍候...'
  return '点击"开始智能分析"按钮进行分析'
})

// 解析巡逻区块输入
const parsedGridBlocks = computed(() => {
  if (!droneParams.value.gridBlocks) return { m: 0, n: 0 }
  
  const parts = droneParams.value.gridBlocks.split('*').map(part => parseInt(part.trim()))
  if (parts.length !== 2 || isNaN(parts[0]) || isNaN(parts[1])) {
    return { m: 0, n: 0 }
  }
  
  return { m: parts[0], n: parts[1] }
})

// 验证巡逻区块格式
const gridBlocksValid = computed(() => {
  const { m, n } = parsedGridBlocks.value
  return m > 0 && n > 0
})

// 生成区块数据
const gridBlocks = computed(() => {
  const { m, n } = parsedGridBlocks.value
  const blocks = []
  
  if (m <= 0 || n <= 0) return blocks
  
  for (let row = 1; row <= n; row++) {
    for (let col = 1; col <= m; col++) {
      blocks.push({
        row,
        col,
        id: `${row}-${col}`,
        width: 100 / m,  // 百分比宽度
        height: 100 / n, // 百分比高度
        left: ((col - 1) * 100) / m,  // 左偏移百分比
        top: ((row - 1) * 100) / n,   // 上偏移百分比
        selected: false
      })
    }
  }
  
  return blocks
})

// 当前选中的区块
const selectedBlock = computed(() => {
  if (selectedBlockIndex.value === null) return null
  return gridBlocks.value[selectedBlockIndex.value]
})

// 方法
const triggerFileInput = () => {
  fileInput.value.click()
}

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file && file.type.startsWith('image/')) {
    selectedFileName.value = file.name
    selectedFileSize.value = `${(file.size / 1024 / 1024).toFixed(2)} MB`
    
    const reader = new FileReader()
    reader.onload = (e) => {
      selectedImage.value = e.target.result
      // 图片加载完成后，显示网格
      showGrid.value = true
    }
    reader.readAsDataURL(file)
  }
}

const handleDrop = (event) => {
  event.preventDefault()
  const file = event.dataTransfer.files[0]
  if (file && file.type.startsWith('image/')) {
    selectedFileName.value = file.name
    selectedFileSize.value = `${(file.size / 1024 / 1024).toFixed(2)} MB`
    
    const reader = new FileReader()
    reader.onload = (e) => {
      selectedImage.value = e.target.result
      // 图片加载完成后，显示网格
      showGrid.value = true
    }
    reader.readAsDataURL(file)
  }
}

// 计算图片实际显示区域
const calculateImageDisplayArea = () => {
  if (!mapImage.value || !imageContainer.value) {
    imageDisplayArea.value = { width: 0, height: 0, left: 0, top: 0 }
    return
  }
  
  const containerRect = imageContainer.value.getBoundingClientRect()
  const imgRect = mapImage.value.getBoundingClientRect()
  
  // 获取图片在容器中的实际显示位置和尺寸
  imageDisplayArea.value = {
    width: imgRect.width,
    height: imgRect.height,
    left: imgRect.left - containerRect.left,
    top: imgRect.top - containerRect.top
  }
}

// 图片加载完成时的处理
const onImageLoad = () => {
  if (mapImage.value) {
    imageNaturalSize.value = {
      width: mapImage.value.naturalWidth,
      height: mapImage.value.naturalHeight
    }
    
    // 等待DOM更新后计算显示区域
    nextTick(() => {
      calculateImageDisplayArea()
    })
  }
}

// 窗口大小变化时重新计算显示区域
const handleResize = () => {
  if (selectedImage.value && mapImage.value) {
    calculateImageDisplayArea()
  }
}

const validateGridBlocks = () => {
  // 验证输入格式
  const regex = /^\d+\s*\*\s*\d+$/
  if (!regex.test(droneParams.value.gridBlocks)) {
    return false
  }
  return true
}

const testApiKey = () => {
  if (apiKey.value) {
    alert('API密钥验证通过')
  } else {
    alert('请输入API密钥')
  }
}

const startAnalysis = async () => {
  if (!canAnalyze.value) return
  
  analyzing.value = true
  
  try {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // 模拟分析结果
    analysisResult.value = {
      heatmap: selectedImage.value, // 这里应该使用后端返回的图片URL
      path: selectedImage.value,    // 这里应该使用后端返回的图片URL
      stats: {
        pathLength: '1245.6',
        maxThreat: '0.87',
        avgThreat: '0.42',
        time: '2.3'
      }
    }
    
    // 切换到第一个有结果的标签页
    if (analysisResult.value.heatmap) {
      activeTab.value = 'heatmap'
    }
    
  } catch (error) {
    console.error('分析失败:', error)
    alert('分析失败，请检查网络连接和API密钥')
  } finally {
    analyzing.value = false
  }
}

const downloadImage = (type) => {
  alert(`下载${type === 'original' ? '原始地图' : type === 'heatmap' ? '热力图' : '路径图'}`)
}

const zoomIn = () => {
  alert('放大图片')
}

const zoomOut = () => {
  alert('缩小图片')
}

const toggleHeatmapLegend = () => {
  showHeatmapLegend.value = !showHeatmapLegend.value
}

const toggleGrid = () => {
  showGrid.value = !showGrid.value
  if (!showGrid.value) {
    selectedBlockIndex.value = null
    highlightedBlockIndex.value = null
  }
}

const getBlockStyle = (block) => {
  return {
    width: `${block.width}%`,
    height: `${block.height}%`,
    left: `${block.left}%`,
    top: `${block.top}%`
  }
}

const highlightBlock = (block) => {
  highlightedBlockIndex.value = gridBlocks.value.findIndex(b => b.id === block.id)
}

const unhighlightBlock = () => {
  highlightedBlockIndex.value = null
}

const selectBlock = (block) => {
  const index = gridBlocks.value.findIndex(b => b.id === block.id)
  if (selectedBlockIndex.value === index) {
    selectedBlockIndex.value = null
  } else {
    selectedBlockIndex.value = index
  }
}

const showPathDetails = () => {
  alert('显示路径详情')
}

const refreshTasks = () => {
  alert('刷新任务列表')
}

const handleLogout = () => {
  router.push('/login')
}

onMounted(() => {
  // 页面加载时，可以检查本地存储的API密钥
  const savedApiKey = localStorage.getItem('terrainav_api_key')
  if (savedApiKey) {
    apiKey.value = savedApiKey
  }
  
  // 添加窗口大小变化监听
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  // 移除窗口大小变化监听
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
}

/* 顶部导航栏 */
.app-header {
  background: white;
  border-bottom: 1px solid #e5e7eb;
  padding: 0.8rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.app-name {
  font-size: 1.2rem;
  font-weight: 600;
  color: #1a2980;
  background: linear-gradient(90deg, #1a2980, #26d0ce);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.main-nav {
  display: flex;
  gap: 1.5rem;
}

.nav-item {
  color: #6b7280;
  text-decoration: none;
  padding: 0.5rem 0;
  font-size: 0.95rem;
  position: relative;
  transition: color 0.3s;
}

.nav-item:hover {
  color: #1a2980;
}

.nav-item.active {
  color: #1a2980;
  font-weight: 600;
}

.nav-item.active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #1a2980, #26d0ce);
  border-radius: 1px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  color: #4b5563;
  font-size: 0.9rem;
}

.logout-btn {
  background: #f3f4f6;
  color: #6b7280;
  border: 1px solid #d1d5db;
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.logout-btn:hover {
  background: #e5e7eb;
  color: #374151;
}

/* 主要内容区域 */
.dashboard-content {
  display: flex;
  flex: 1;
  padding: 2rem;
  gap: 2rem;
  max-width: 1600px;
  margin: 0 auto;
  width: 100%;
}

/* 左侧面板 */
.left-panel {
  width: 320px;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
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
  margin: 0.2rem 0;
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
  100% { transform: rotate(360deg); }
}

@keyframes dash {
  0% { stroke-dasharray: 1, 150; stroke-dashoffset: 0; }
  50% { stroke-dasharray: 90, 150; stroke-dashoffset: -35; }
  100% { stroke-dasharray: 90, 150; stroke-dashoffset: -124; }
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

/* 右侧面板 */
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  min-width: 0; /* 防止内容溢出 */
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
}

.tabs-header {
  display: flex;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  padding: 0.5rem 1.5rem;
  gap: 0.5rem;
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

.tab-content {
  flex: 1;
  padding: 1.5rem;
  overflow: auto;
  display: flex;
  flex-direction: column;
}

.result-display {
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1;
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

/* 图片容器 - 修改后的样式 */
.image-container {
  position: relative;
  background: #f9fafb;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
  min-height: 400px; /* 无图片时的固定高度 */
  width: 100%;
}

/* 有图片时的样式 */
.image-container.has-image {
  min-height: 0;
  height: auto;
  display: block;
  position: relative;
  overflow: hidden;
}

.image-container.has-image img {
  display: block;
  width: 100%;
  height: auto;
  max-width: 100%;
  object-fit: contain;
}

/* 无图片时的提示信息 */
.image-container .no-result {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #9ca3af;
  font-size: 1.1rem;
  background: #f9fafb;
}

/* 巡逻区块网格 - 精确定位在图片上 */
.grid-overlay {
  position: absolute;
  pointer-events: none;
  z-index: 2;
}

.grid-block {
  position: absolute;
  border: 2px solid rgba(74, 108, 247, 0.7);
  box-sizing: border-box;
  pointer-events: auto;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(74, 108, 247, 0.1);
}

.grid-block:hover {
  background-color: rgba(74, 108, 247, 0.2);
  border-color: rgba(74, 108, 247, 1);
  z-index: 2;
}

.grid-block.highlighted {
  background-color: rgba(16, 185, 129, 0.2);
  border-color: rgba(16, 185, 129, 0.8);
  z-index: 1;
}

.grid-block.selected {
  background-color: rgba(239, 68, 68, 0.3);
  border-color: rgba(239, 68, 68, 1);
  border-width: 3px;
  z-index: 3;
}

.block-label {
  background-color: rgba(255, 255, 255, 0.9);
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
  color: #4a6cf7;
  pointer-events: none;
}

.grid-block.selected .block-label {
  background-color: rgba(255, 255, 255, 0.95);
  color: #ef4444;
  font-weight: 700;
}

.grid-stats {
  margin-top: 1rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.grid-stats h4 {
  color: #1a2980;
  font-size: 1rem;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.stats-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.5rem;
}

.stats-details p {
  margin: 0.3rem 0;
  color: #4b5563;
  font-size: 0.9rem;
}

.heatmap-legend {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background: rgba(255, 255, 255, 0.9);
  padding: 0.8rem;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  min-width: 100px;
}

.legend-gradient {
  height: 20px;
  background: linear-gradient(90deg, #3b82f6, #ef4444);
  border-radius: 4px;
  margin-bottom: 0.5rem;
}

.legend-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #6b7280;
}

/* 结果统计信息 */
.results-stats {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.results-stats h3 {
  font-size: 1rem;
  color: #374151;
  margin-bottom: 1rem;
  font-weight: 600;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  padding: 0.8rem;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.stat-label {
  font-size: 0.8rem;
  color: #6b7280;
  margin-bottom: 0.3rem;
}

.stat-value {
  font-size: 1.1rem;
  color: #1a2980;
  font-weight: 600;
}

/* 底部版权信息 */
.app-footer {
  background: linear-gradient(90deg, #1a2980, #26d0ce);
  color: white;
  padding: 1.5rem 2rem;
  text-align: center;
  margin-top: auto;
  flex-shrink: 0;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.footer-content p {
  margin: 0;
  font-size: 0.9rem;
  opacity: 0.9;
}

.footer-content p:first-child {
  font-weight: 500;
  font-size: 1rem;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .dashboard-content {
    flex-direction: column;
  }
  
  .left-panel {
    width: 100%;
  }
  
  .stats-details {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .app-header {
    padding: 0.8rem 1rem;
    flex-direction: column;
    gap: 1rem;
  }
  
  .header-left, .header-right {
    width: 100%;
    justify-content: space-between;
  }
  
  .main-nav {
    gap: 1rem;
  }
  
  .dashboard-content {
    padding: 1rem;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .app-footer {
    padding: 1rem;
  }
  
  .footer-content p {
    font-size: 0.8rem;
  }
  
  .result-actions {
    flex-wrap: wrap;
  }
  
  .image-container {
    min-height: 300px;
  }
}
</style>