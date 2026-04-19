import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface AnalysisResult {
  heatmap: string
  path: string
  stats: {
    pathLength: string
    maxThreat: string
    avgThreat: string
    time: string
  } | null
}

export interface Task {
  id: number
  name: string
  time: string
  status: 'success' | 'processing' | 'failed'
  statusText: string
  thumbnail: string
  description?: string
  image?: string
}

export interface DroneParams {
  patrolRadius: number
  startPoint: string
  gridBlocks: string
}

export interface OutputOptions {
  heatmap: boolean
  path: boolean
  quality: 'high' | 'medium' | 'low'
}

export interface GridBlock {
  row: number
  col: number
  id: string
  width: number
  height: number
  left: number
  top: number
  selected: boolean
}

export interface ImageDisplayArea {
  width: number
  height: number
  left: number
  top: number
}

export const useDashboardStore = defineStore('dashboard', () => {
  // 响应式数据
  const selectedImage = ref('')
  const selectedFileName = ref('')
  const selectedFileSize = ref('')
  const apiKey = ref('')
  const analyzing = ref(false)
  const analysisResult = ref<AnalysisResult>({
    heatmap: '',
    path: '',
    stats: null
  })
  const showHeatmapLegend = ref(true)
  const activeTab = ref('original')
  const showGrid = ref(false)
  const selectedBlockIndex = ref<number | null>(null)
  const highlightedBlockIndex = ref<number | null>(null)
  const imageDisplayArea = ref<ImageDisplayArea>({ width: 0, height: 0, left: 0, top: 0 })
  
  // 标签页配置
  const tabs = ref([
    { id: 'original', name: '原始地图' },
    { id: 'heatmap', name: '威胁度热力图' },
    { id: 'path', name: '巡逻路线图' }
  ])
  
  // 输出选项
  const outputOptions = ref<OutputOptions>({
    heatmap: true,
    path: true,
    quality: 'high'
  })
  
  // 无人机巡逻参数
  const droneParams = ref<DroneParams>({
    patrolRadius: 1000,
    startPoint: '100,200',
    gridBlocks: '4 * 4'
  })
  
  // 最近任务（模拟数据）
  const recentTasks = ref<Task[]>([
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
    
    // 修复：添加类型安全检查
    if (parts.length !== 2) {
      return { m: 0, n: 0 }
    }
    
    // 修复：使用非空断言或类型保护
    const m = parts[0] as number
    const n = parts[1] as number
    
    if (isNaN(m) || isNaN(n)) {
      return { m: 0, n: 0 }
    }
    
    return { m, n }
  })
  
  // 验证巡逻区块格式
  const gridBlocksValid = computed(() => {
    const { m, n } = parsedGridBlocks.value
    return m > 0 && n > 0
  })
  
  // 生成区块数据
  const gridBlocks = computed<GridBlock[]>(() => {
    const { m, n } = parsedGridBlocks.value
    const blocks: GridBlock[] = []
    
    if (m <= 0 || n <= 0) return blocks
    
    for (let row = 1; row <= n; row++) {
      for (let col = 1; col <= m; col++) {
        blocks.push({
          row,
          col,
          id: `${row}-${col}`,
          width: 100 / m,
          height: 100 / n,
          left: ((col - 1) * 100) / m,
          top: ((row - 1) * 100) / n,
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
  
  // 触发文件选择
  const triggerFileInput = (fileInput: HTMLInputElement) => {
    fileInput.click()
  }
  
  // 处理文件选择
  const handleFileSelect = (event: Event) => {
    const fileInput = event.target as HTMLInputElement
    const file = fileInput.files?.[0]
    if (file && file.type.startsWith('image/')) {
      selectedFileName.value = file.name
      selectedFileSize.value = `${(file.size / 1024 / 1024).toFixed(2)} MB`
      
      const reader = new FileReader()
      reader.onload = (e) => {
        selectedImage.value = e.target?.result as string
        // 图片加载完成后，显示网格
        showGrid.value = true
      }
      reader.readAsDataURL(file)
    }
  }
  
  // 处理文件拖放
  const handleDrop = (event: DragEvent) => {
    event.preventDefault()
    const file = event.dataTransfer?.files[0]
    if (file && file.type.startsWith('image/')) {
      selectedFileName.value = file.name
      selectedFileSize.value = `${(file.size / 1024 / 1024).toFixed(2)} MB`
      
      const reader = new FileReader()
      reader.onload = (e) => {
        selectedImage.value = e.target?.result as string
        // 图片加载完成后，显示网格
        showGrid.value = true
      }
      reader.readAsDataURL(file)
    }
  }
  
  // 计算图片实际显示区域
  const calculateImageDisplayArea = (mapImage: HTMLImageElement, imageContainer: HTMLElement) => {
    if (!mapImage || !imageContainer) {
      imageDisplayArea.value = { width: 0, height: 0, left: 0, top: 0 }
      return
    }
    
    const containerRect = imageContainer.getBoundingClientRect()
    const imgRect = mapImage.getBoundingClientRect()
    
    // 获取图片在容器中的实际显示位置和尺寸
    imageDisplayArea.value = {
      width: imgRect.width,
      height: imgRect.height,
      left: imgRect.left - containerRect.left,
      top: imgRect.top - containerRect.top
    }
  }
  
  // 验证网格区块输入格式
  const validateGridBlocks = () => {
    const regex = /^\d+\s*\*\s*\d+$/
    if (!regex.test(droneParams.value.gridBlocks)) {
      return false
    }
    return true
  }
  
  // 测试API密钥
  const testApiKey = () => {
    if (apiKey.value) {
      alert('API密钥验证通过')
      return true
    } else {
      alert('请输入API密钥')
      return false
    }
  }
  
  // 开始分析
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
      
      // 保存API密钥到本地存储
      localStorage.setItem('terrainav_api_key', apiKey.value)
      
      // 保存分析结果到最近任务
      const newTask: Task = {
        id: Date.now(),
        name: selectedFileName.value.replace(/\.[^/.]+$/, '') + '分析',
        time: '刚刚',
        status: 'success',
        statusText: '完成',
        thumbnail: selectedImage.value
      }
      
      recentTasks.value.unshift(newTask)
      if (recentTasks.value.length > 10) {
        recentTasks.value = recentTasks.value.slice(0, 10)
      }
      
      // 切换到第一个有结果的标签页
      if (analysisResult.value.heatmap) {
        activeTab.value = 'heatmap'
      }
      
    } catch (error) {
      console.error('分析失败:', error)
      alert('分析失败，请检查网络连接和API密钥')
      
      // 添加失败任务
      const failedTask: Task = {
        id: Date.now(),
        name: selectedFileName.value.replace(/\.[^/.]+$/, '') + '分析',
        time: '刚刚',
        status: 'failed',
        statusText: '失败',
        thumbnail: selectedImage.value
      }
      
      recentTasks.value.unshift(failedTask)
      if (recentTasks.value.length > 10) {
        recentTasks.value = recentTasks.value.slice(0, 10)
      }
    } finally {
      analyzing.value = false
    }
  }
  
  // 下载图片
  const downloadImage = (type: 'original' | 'heatmap' | 'path') => {
    const imageUrl = type === 'original' 
      ? selectedImage.value 
      : type === 'heatmap' 
        ? analysisResult.value.heatmap 
        : analysisResult.value.path
    
    if (!imageUrl) {
      alert('没有可下载的图片')
      return
    }
    
    const link = document.createElement('a')
    link.href = imageUrl
    link.download = `${selectedFileName.value.replace(/\.[^/.]+$/, '')}_${type}_${new Date().getTime()}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    alert(`下载${type === 'original' ? '原始地图' : type === 'heatmap' ? '热力图' : '路径图'}成功`)
  }
  
  // 放大图片
  const zoomIn = () => {
    alert('放大图片功能待实现')
  }
  
  // 缩小图片
  const zoomOut = () => {
    alert('缩小图片功能待实现')
  }
  
  // 切换热力图图例显示
  const toggleHeatmapLegend = () => {
    showHeatmapLegend.value = !showHeatmapLegend.value
  }
  
  // 切换网格显示
  const toggleGrid = () => {
    showGrid.value = !showGrid.value
    if (!showGrid.value) {
      selectedBlockIndex.value = null
      highlightedBlockIndex.value = null
    }
  }
  
  // 获取区块样式
  const getBlockStyle = (block: GridBlock) => {
    return {
      width: `${block.width}%`,
      height: `${block.height}%`,
      left: `${block.left}%`,
      top: `${block.top}%`
    }
  }
  
  // 高亮区块
  const highlightBlock = (block: GridBlock) => {
    const index = gridBlocks.value.findIndex(b => b.id === block.id)
    if (index !== -1) {
      highlightedBlockIndex.value = index
    }
  }
  
  // 取消高亮区块
  const unhighlightBlock = () => {
    highlightedBlockIndex.value = null
  }
  
  // 选择区块
  const selectBlock = (block: GridBlock) => {
    const index = gridBlocks.value.findIndex(b => b.id === block.id)
    if (selectedBlockIndex.value === index) {
      selectedBlockIndex.value = null
    } else {
      selectedBlockIndex.value = index
    }
  }
  
  // 显示路径详情
  const showPathDetails = () => {
    if (analysisResult.value.stats) {
      alert(`路径详情：
路径长度: ${analysisResult.value.stats.pathLength} 米
最高威胁度: ${analysisResult.value.stats.maxThreat}
平均威胁度: ${analysisResult.value.stats.avgThreat}
分析用时: ${analysisResult.value.stats.time} 秒`)
    } else {
      alert('暂无路径详情数据')
    }
  }
  
  // 刷新任务列表
  const refreshTasks = () => {
    // 这里可以添加从服务器获取最新任务列表的逻辑
    alert('刷新任务列表')
  }
  
  // 退出登录
  const handleLogout = () => {
    // 清除本地存储的API密钥
    localStorage.removeItem('terrainav_api_key')
    
    // 重置状态
    resetState()
    
    alert('已退出登录')
  }
  
  // 重置状态
  const resetState = () => {
    selectedImage.value = ''
    selectedFileName.value = ''
    selectedFileSize.value = ''
    apiKey.value = ''
    analyzing.value = false
    analysisResult.value = {
      heatmap: '',
      path: '',
      stats: null
    }
    activeTab.value = 'original'
    showGrid.value = false
    selectedBlockIndex.value = null
    highlightedBlockIndex.value = null
    imageDisplayArea.value = { width: 0, height: 0, left: 0, top: 0 }
  }
  
  // 初始化API密钥
  const initApiKey = () => {
    const savedApiKey = localStorage.getItem('terrainav_api_key')
    if (savedApiKey) {
      apiKey.value = savedApiKey
    }
  }
  
  // 添加窗口大小变化监听
  const addResizeListener = (callback: () => void) => {
    window.addEventListener('resize', callback)
  }
  
  // 移除窗口大小变化监听
  const removeResizeListener = (callback: () => void) => {
    window.removeEventListener('resize', callback)
  }
  
  return {
    // 状态
    selectedImage,
    selectedFileName,
    selectedFileSize,
    apiKey,
    analyzing,
    analysisResult,
    showHeatmapLegend,
    activeTab,
    tabs,
    showGrid,
    selectedBlockIndex,
    highlightedBlockIndex,
    imageDisplayArea,
    outputOptions,
    droneParams,
    recentTasks,
    
    // 计算属性
    canAnalyze,
    analysisTip,
    parsedGridBlocks,
    gridBlocksValid,
    gridBlocks,
    selectedBlock,
    
    // 方法
    triggerFileInput,
    handleFileSelect,
    handleDrop,
    calculateImageDisplayArea,
    validateGridBlocks,
    testApiKey,
    startAnalysis,
    downloadImage,
    zoomIn,
    zoomOut,
    toggleHeatmapLegend,
    toggleGrid,
    getBlockStyle,
    highlightBlock,
    unhighlightBlock,
    selectBlock,
    showPathDetails,
    refreshTasks,
    handleLogout,
    resetState,
    initApiKey,
    addResizeListener,
    removeResizeListener
  }
})