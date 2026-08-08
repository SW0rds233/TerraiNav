<template>
  <div class="dashboard">
    <div class="dashboard-content">
      <!-- 左侧控制面板 -->
      <div class="left-panel">
        <MapControls
          :tile-source="tileSource"
          :api-key="apiKey"
          :api-provider="apiProvider"
          :api-base-url="apiBaseUrl"
          :api-model="apiModel"
          :api-model-custom="apiModelCustom"
          :api-max-workers="apiMaxWorkers"
          :task-name="taskName"
          :start-point="droneParams.startPoint"
          :grid-blocks="droneParams.gridBlocks"
          :analyzing="analyzing"
          :can-analyze="canAnalyze"
          :map-scale="mapScale"
          :grid-blocks-valid="gridBlocksValid"
          :parsed-grid-rows="parsedGridBlocks.n"
          :parsed-grid-cols="parsedGridBlocks.m"
          :analysis-progress="analysisProgress"
          :analysis-tip="analysisTip"
          :output-options="outputOptions"
          :contour-enabled="contourEnabled"
          :can-contour="canContour"
          :contour-opacity="contourOpacity"
          :has-result="analysisResult.stats !== null"
          :heatmap-opacity="heatmapOpacity"
          :path-opacity="pathOpacity"
          @update:tile-source="onTileSourceChange"
          @update:api-key="onApiKeyChange"
          @update:api-provider="(v: string) => apiProvider = v"
          @update:api-base-url="(v: string) => apiBaseUrl = v"
          @update:api-model="(v: string) => apiModel = v"
          @update:api-model-custom="(v: string) => apiModelCustom = v"
          @update:api-max-workers="(v: number) => apiMaxWorkers = v"
          @update:task-name="onTaskNameChange"
          @update:start-point="onStartPointChange"
          @update:grid-blocks="onGridBlocksChange"
          @update:output-options="onOutputOptionsChange"
          @update:contour-opacity="(v: number) => contourOpacity = v"
          @update:heatmap-opacity="(v: number) => heatmapOpacity = v"
          @update:path-opacity="(v: number) => pathOpacity = v"
          @test-api="testApiKey"
          @start-analysis="startAnalysis"
          @toggle-contour="onToggleContour"
        />

        <!-- 最近任务 -->
        <div class="recent-tasks">
          <div class="tasks-header">
            <h3>最近任务</h3>
            <button class="refresh-btn" @click="refreshTasks">刷新</button>
          </div>
          <div class="tasks-list">
            <div v-for="task in recentTasks" :key="task.id" class="task-item">
              <div class="task-preview">
                <div class="task-thumb-placeholder"></div>
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

      <!-- 右侧：地图 + 结果 -->
      <div class="right-panel">
        <div class="map-panel">
          <MapSelector
            ref="mapSelectorRef"
            :grid-rows="parsedGridBlocks.m"
            :grid-cols="parsedGridBlocks.n"
            :start-point="droneParams.startPoint"
            :tile-source="tileSource"
            :contour-overlay-url="contourOverlayUrl"
            :contour-overlay-bounds="contourOverlayBounds"
            :contour-opacity="contourOpacity"
            :heatmap-overlay-url="heatmapOverlayUrl"
            :heatmap-overlay-bounds="resultOverlayBounds"
            :heatmap-opacity="heatmapOpacity"
            :path-overlay-url="pathOverlayUrl"
            :path-overlay-bounds="resultOverlayBounds"
            :path-opacity="pathOpacity"
            @update:bounds="onMapBoundsChange"
            @update:scale="onMapScaleUpdate"
            @select-block="onMapBlockSelect"
          />
        </div>
        <MapResultPanel
          :stats="analysisResult.stats"
          :threat-points="filteredThreatPoints"
          :analysis-progress="analysisProgress"
          @download-image="downloadImage"
          @show-path-details="showPathDetails"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import axios from 'axios'
import { useUserStore } from '../../stores/userStore'
import MapSelector from './MapSelector.vue'
import MapControls from './MapControls.vue'
import MapResultPanel from './MapResultPanel.vue'

interface AnalysisProgress {
  status: 'idle' | 'pending' | 'running' | 'completed' | 'failed'
  message: string
  progress_percent: number
}

interface AnalysisResult {
  heatmap: string
  path: string
  stats: { pathLength: string; maxThreat: string; avgThreat: string; time: string } | null
  threatPoints: ThreatPoint[]
  threatStats: { topThreatBlock: string; distribution: string; priorityPatrol: string } | null
  _rawData?: any
}

interface ThreatPoint {
  id: number; rank: number; block: string; threatScore: number
  coordinate: string; location: string; description: string; reason: string
}

interface RecentTask {
  id: number; name: string; time: string; status: 'success' | 'failed' | 'pending'; statusText: string; thumbnail: string
}

interface MapBounds {
  north: number; south: number; east: number; west: number; zoom: number
}

const userStore = useUserStore()
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

const apiClient = axios.create({ baseURL: API_BASE_URL, timeout: 480000 })
apiClient.interceptors.request.use((config) => {
  const k = localStorage.getItem('terrainav_api_key')
  if (k) config.headers['X-API-Key'] = k
  const session = localStorage.getItem('terrainav_session_token')
  if (session) config.headers['X-Session-Token'] = session
  return config
}, (e) => Promise.reject(e))
apiClient.interceptors.response.use((r) => r, (error) => {
  const msg = error.response?.data?.error || error.response?.data?.message || '请求失败'
  throw new Error(msg)
})

// ========== 状态 ==========
const mapSelectorRef = ref<InstanceType<typeof MapSelector> | null>(null)
const mapBounds = ref<MapBounds | null>(null)
const mapScale = ref(0)
const tileSource = ref('esri')
const apiKey = ref('')
const apiProvider = ref('dashscope')
const apiBaseUrl = ref('')
const apiModel = ref('qwen3.6-plus')
const apiModelCustom = ref('')
const apiMaxWorkers = ref(4)
const analyzing = ref(false)
const taskName = ref('')
const droneParams = ref({ startPoint: '0,0', gridBlocks: '4 * 4' })
const outputOptions = ref({ heatmap: true, path: true, quality: 'high' })
const recentTasks = ref<RecentTask[]>([])

// 等高线叠加
const contourEnabled = ref(false)
const contourOverlayUrl = ref<string | null>(null)
const contourOverlayBounds = ref<{ north: number; south: number; east: number; west: number } | null>(null)
const contourOpacity = ref(50)

// 热力图 / 路径图叠加 (分析完成后显示在地图上)
const heatmapOverlayUrl = ref<string | null>(null)
const pathOverlayUrl = ref<string | null>(null)
const resultOverlayBounds = ref<{ north: number; south: number; east: number; west: number } | null>(null)
const heatmapOpacity = ref(60)
const pathOpacity = ref(60)

const analysisResult = ref<AnalysisResult>({ heatmap: '', path: '', stats: null, threatPoints: [], threatStats: null })
const analysisProgress = ref<AnalysisProgress>({ status: 'idle', message: '准备分析', progress_percent: 0 })

// ========== 计算属性 ==========
const canAnalyze = computed(() => apiKey.value && !analyzing.value && mapBounds.value !== null)

const analysisTip = computed(() => {
  if (analyzing.value) return analysisProgress.value.message || '正在分析中...'
  if (analysisProgress.value.status === 'completed') return '分析完成'
  if (mapBounds.value) return '点击"开始智能分析"提交当前地图区域'
  return '在地图上拖拽/缩放以选择目标区域'
})

const parsedGridBlocks = computed(() => {
  const parts = droneParams.value.gridBlocks.split('*').map((p) => parseInt(p.trim()))
  return { m: parts[0] || 0, n: parts[1] || 0 }
})

const gridBlocksValid = computed(() => {
  const { m, n } = parsedGridBlocks.value
  return (m ?? 0) > 0 && (n ?? 0) > 0
})

const filteredThreatPoints = computed(() => {
  return (analysisResult.value.threatPoints || [])
    .filter((p) => p.threatScore >= 40)
    .sort((a, b) => b.threatScore - a.threatScore)
    .map((p, i) => ({ ...p, rank: i + 1 }))
})

const canContour = computed(() => mapBounds.value !== null && !analyzing.value)

// ========== 事件处理 ==========
function onTileSourceChange(v: string) { tileSource.value = v }
function onApiKeyChange(v: string) { apiKey.value = v }
function onTaskNameChange(v: string) { taskName.value = v }
function onStartPointChange(v: string) { droneParams.value.startPoint = v }
function onGridBlocksChange(v: string) { droneParams.value.gridBlocks = v }
function onOutputOptionsChange(v: { heatmap: boolean; path: boolean; quality: string }) { outputOptions.value = { ...v } }
function onMapBoundsChange(bounds: MapBounds) { mapBounds.value = bounds }
function onMapScaleUpdate(scale: number) { mapScale.value = scale }
function onMapBlockSelect(_blockId: number, _lat: number, _lng: number, row: number, col: number) {
  droneParams.value.startPoint = `${row},${col}`
}

const onToggleContour = async () => {
  if (!canContour.value || !mapBounds.value) return
  contourEnabled.value = !contourEnabled.value
  if (!contourEnabled.value) {
    contourOverlayUrl.value = null
    contourOverlayBounds.value = null
    return
  }
  try {
    const { data } = await apiClient.post('/api/map_overlay', {
      north: mapBounds.value.north,
      south: mapBounds.value.south,
      east: mapBounds.value.east,
      west: mapBounds.value.west,
      zoom: mapBounds.value.zoom,
    })
    if (data.success) {
      contourOverlayUrl.value = API_BASE_URL + data.image_url
      contourOverlayBounds.value = data.bounds
    } else {
      contourEnabled.value = false
      alert('生成等高线失败: ' + (data.error || '未知错误'))
    }
  } catch (e: any) {
    contourEnabled.value = false
    alert('生成等高线失败: ' + e.message)
  }
}

// ========== API ==========
const initApi = async (key: string) => {
  const payload: Record<string, any> = { api_key: key }
  const model = apiModel.value === 'custom-model' ? apiModelCustom.value : apiModel.value
  if (model) payload.model = model
  if (apiBaseUrl.value) payload.base_url = apiBaseUrl.value
  payload.max_workers = apiMaxWorkers.value
  return (await apiClient.post('/api/init', payload)).data
}

const waitForTaskResult = async (taskId: string) => {
  const start = Date.now()
  while (true) {
    const { data } = await apiClient.get(`/api/task_status/${taskId}`)
    if (!data.success) throw new Error(data.error || '查询任务状态失败')
    analysisProgress.value = {
      status: data.status,
      message: data.progress || '正在分析中...',
      progress_percent: data.progress_percent ?? analysisProgress.value.progress_percent,
    }
    if (data.status === 'completed') return data.result
    if (data.status === 'failed') throw new Error(data.error || '任务失败')
    if (Date.now() - start > 480000) throw new Error('任务超时')
    await new Promise((r) => setTimeout(r, 2000))
  }
}

const testApiKey = async () => {
  if (!apiKey.value) { alert('请输入API密钥'); return }
  try {
    const r = await initApi(apiKey.value)
    if (r.success) {
      localStorage.setItem('terrainav_api_key', apiKey.value)
      localStorage.setItem('terrainav_session_token', r.session_token || '')
      alert(r.message || '连接成功')
    } else {
      localStorage.removeItem('terrainav_api_key')
      localStorage.removeItem('terrainav_session_token')
      alert('连接失败: ' + (r.error || '未知错误'))
    }
  } catch (e: any) {
    alert('连接失败: ' + e.message)
    localStorage.removeItem('terrainav_api_key')
    localStorage.removeItem('terrainav_session_token')
  }
}

const startAnalysis = async () => {
  if (!canAnalyze.value) return
  analyzing.value = true
  const t0 = Date.now()
  try {
    analysisProgress.value = { status: 'pending', message: '已提交...', progress_percent: 5 }
    if (!localStorage.getItem('terrainav_api_key')) localStorage.setItem('terrainav_api_key', apiKey.value)
    if (!mapBounds.value) throw new Error('请先选择地图区域')

    const divide = droneParams.value.gridBlocks.replace(/\s*/g, '')
    const res = await apiClient.post('/api/analyze_map_region', {
      north: mapBounds.value.north, south: mapBounds.value.south,
      east: mapBounds.value.east, west: mapBounds.value.west,
      zoom: mapBounds.value.zoom, divide, start_point: droneParams.value.startPoint,
      tile_source: tileSource.value,
    })
    if (!res.data.success) throw new Error(res.data.error || '任务启动失败')

    const result = await waitForTaskResult(res.data.task_id)
    const t1 = ((Date.now() - t0) / 1000).toFixed(1)
    analysisProgress.value = { status: 'completed', message: '分析完成', progress_percent: 100 }

    // 处理威胁矩阵
    const tm = result.threat_matrix || []
    let maxT = 0, totalT = 0, cnt = 0
    for (const row of tm) for (const v of row) { if (v > 0) { maxT = Math.max(maxT, v); totalT += v; cnt++ } }
    const avgT = cnt > 0 ? (totalT / cnt).toFixed(1) : '0.0'

    const pts: ThreatPoint[] = (result.patrol_points || []).map((pt: any, idx: number) => ({
      id: idx + 1, rank: pt.rank || idx + 1, block: pt.block || '',
      threatScore: pt.threat_score || 0,
      coordinate: pt.pixel_coords ? `${pt.pixel_coords[0]},${pt.pixel_coords[1]}` : '',
      location: pt.block_position || '', description: '', reason: pt.threat_reason || '',
    }))

    analysisResult.value = {
      heatmap: `${API_BASE_URL}${result.heatmap_url || ''}`,
      path: `${API_BASE_URL}${result.pathmap_url || ''}`,
      stats: { pathLength: result.best_path_length?.toFixed(1) || '0.0', maxThreat: maxT.toFixed(1), avgThreat: avgT, time: t1 },
      threatPoints: pts,
      threatStats: {
        topThreatBlock: pts[0]?.block || '-',
        distribution: `共 ${pts.length} 个高威胁点`,
        priorityPatrol: pts.slice(0, 4).map((p) => p.block).join('、') || '-',
      },
      _rawData: result,
    }

    // 热力图 / 路径图叠加到地图上
    resultOverlayBounds.value = mapBounds.value ? { ...mapBounds.value } : null
    heatmapOverlayUrl.value = result.heatmap_url ? `${API_BASE_URL}${result.heatmap_url}` : null
    pathOverlayUrl.value = result.pathmap_url ? `${API_BASE_URL}${result.pathmap_url}` : null

    localStorage.setItem('terrainav_api_key', apiKey.value)

    // 保存历史
    if (userStore.user.id && userStore.user.id > 0) {
      try {
        await axios.post(`${API_BASE_URL}/api/history`, {
          user_id: userStore.user.id,
          task_name: taskName.value.trim() || `地图分析 ${new Date().toLocaleDateString()}`,
          description: result.path_description || '路径规划任务',
          input_image_url: result.heatmap_url || '',
          heatmap_url: result.heatmap_url || '',
          route_url: result.pathmap_url || '',
          report_url: '', task_status: 'completed', task_time: new Date().toISOString(),
        })
        await refreshTasks()
      } catch (e) { console.error('保存历史失败:', e) }
    }

    alert(`分析完成！用时 ${t1} 秒`)
  } catch (e: any) {
    analysisProgress.value = { status: 'failed', message: e.message, progress_percent: 100 }
    alert('分析失败: ' + e.message)
  } finally { analyzing.value = false }
}

const showPathDetails = () => {
  const raw = analysisResult.value._rawData
  if (raw?.path_coords) {
    const coords = raw.path_coords as number[][]
    let msg = `路径坐标 (共 ${coords.length} 个):\n\n`
    coords.forEach((c, i) => { msg += `${i + 1}. (${c[0]}, ${c[1]})\n` })
    if (raw.best_path_length) msg += `\n总路径长度: ${raw.best_path_length.toFixed(2)}`
    alert(msg)
  } else alert('暂无路径数据')
}

const downloadImage = async (type: 'heatmap' | 'path') => {
  const url = type === 'heatmap' ? analysisResult.value.heatmap : analysisResult.value.path
  if (!url) { alert('没有可下载的图片'); return }
  const link = document.createElement('a')
  link.href = url; link.download = `map_${type}_${Date.now()}.png`; link.target = '_blank'
  document.body.appendChild(link); link.click(); document.body.removeChild(link)
}

const refreshTasks = async () => {
  if (!userStore.user.id || userStore.user.id <= 0) return
  try {
    const { data } = await axios.get(`${API_BASE_URL}/api/history/recent`, {
      params: { user_id: userStore.user.id, limit: 3 },
    })
    if (data.success) recentTasks.value = data.histories
  } catch (e) { console.error('加载任务失败:', e) }
}

onMounted(() => {
  const savedKey = localStorage.getItem('terrainav_api_key')
  if (savedKey) apiKey.value = savedKey
  const savedDP = localStorage.getItem('terrainav_drone_params')
  if (savedDP) {
    try { const p = JSON.parse(savedDP); if (p.gridBlocks) droneParams.value.gridBlocks = p.gridBlocks; if (p.startPoint) droneParams.value.startPoint = p.startPoint } catch {}
  }
  refreshTasks()
})

onUnmounted(() => {})
</script>

<style scoped>
.dashboard { height: 100%; display: flex; flex-direction: column; background: #f1f5f9; min-height: 100vh; }
.dashboard-content { display: flex; flex: 1; gap: 1rem; padding: 0 1rem 1rem; max-width: 1600px; margin: 0 auto; width: 100%; overflow: auto; }
.left-panel { width: 320px; display: flex; flex-direction: column; gap: 0.65rem; flex-shrink: 0; }
.right-panel { flex: 1; display: flex; flex-direction: column; gap: 0.75rem; min-width: 0; overflow-x: hidden; overflow-y: auto; }
.map-panel { flex-shrink: 0; aspect-ratio: 1 / 1; width: 100%; border-radius: 12px; overflow: hidden; border: none; background: #000; box-shadow: 0 2px 8px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04); transition: box-shadow 0.2s; }
.map-panel:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.12), 0 8px 24px rgba(0,0,0,0.06); }

/* 最近任务 */
.recent-tasks { background: white; border-radius: 10px; padding: 0.85rem 1.1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04); border: 1px solid #e2e8f0; }
.tasks-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
.tasks-header h3 { font-size: 0.82rem; color: #334155; font-weight: 600; }
.refresh-btn { padding: 0.2rem 0.5rem; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 4px; cursor: pointer; font-size: 0.7rem; color: #64748b; transition: all 0.15s; }
.refresh-btn:hover { background: #e2e8f0; color: #334155; }
.tasks-list { display: flex; flex-direction: column; gap: 0.5rem; }
.task-item { display: flex; gap: 0.5rem; align-items: center; padding: 0.35rem 0; border-radius: 6px; transition: background 0.15s; }
.task-item:hover { background: #f8fafc; }
.task-preview { width: 32px; height: 32px; border-radius: 5px; overflow: hidden; flex-shrink: 0; }
.task-thumb-placeholder { width: 100%; height: 100%; background: linear-gradient(135deg, #818cf8, #6366f1); border-radius: 5px; }
.task-info { flex: 1; min-width: 0; }
.task-name { font-size: 0.76rem; color: #334155; font-weight: 500; }
.task-time { font-size: 0.66rem; color: #94a3b8; }
.task-status { font-size: 0.66rem; padding: 0.1rem 0.3rem; border-radius: 3px; display: inline-block; }
.task-status.success { background: #dcfce7; color: #166534; }
.task-status.failed { background: #fee2e2; color: #991b1b; }
.task-status.pending { background: #fef9c3; color: #854d0e; }
.ellipsis { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%; display: block; }
</style>
