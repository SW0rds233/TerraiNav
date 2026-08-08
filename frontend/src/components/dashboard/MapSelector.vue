<template>
  <div class="map-selector">
    <div ref="mapContainer" class="map-container"></div>

    <!-- 搜索定位 -->
    <div class="map-search-bar">
      <input
        v-model="searchText"
        @keyup.enter="doSearch"
        type="text"
        placeholder="输入地名或经纬度 (例: 北京 / 39.9,116.4)"
        class="search-input"
      />
      <button @click="doSearch" class="search-btn" title="搜索定位">&#x1F50D;</button>
    </div>

    <!-- 图例/状态条 -->
    <div class="map-status-bar">
      <div class="status-item" v-if="scaleDisplay">
        <span class="status-label">比例尺</span>
        <span class="status-value">{{ scaleDisplay }}</span>
      </div>
      <div class="status-item" v-if="regionSize">
        <span class="status-label">区域</span>
        <span class="status-value">{{ regionSize }}</span>
      </div>
      <div class="status-item">
        <span class="status-label">网格</span>
        <span class="status-value">{{ gridRows }}×{{ gridCols }}</span>
      </div>
      <div class="status-item" v-if="startBlock">
        <span class="status-label">起点</span>
        <span class="status-value">{{ startLabel }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// ========== Props ==========
const props = withDefaults(
  defineProps<{
    gridRows: number
    gridCols: number
    startPoint?: string
    editable?: boolean
    centerLat?: number
    centerLng?: number
    zoomLevel?: number
    tileSource?: string
    contourOverlayUrl?: string | null
    contourOverlayBounds?: { north: number; south: number; east: number; west: number } | null
    contourOpacity?: number
    heatmapOverlayUrl?: string | null
    heatmapOverlayBounds?: { north: number; south: number; east: number; west: number } | null
    heatmapOpacity?: number
    pathOverlayUrl?: string | null
    pathOverlayBounds?: { north: number; south: number; east: number; west: number } | null
    pathOpacity?: number
  }>(),
  {
    startPoint: '0,0',
    editable: true,
    centerLat: 30.273,
    centerLng: 120.132,
    zoomLevel: 16,
    tileSource: 'esri',
    contourOverlayUrl: null,
    contourOverlayBounds: null,
    contourOpacity: 50,
    heatmapOverlayUrl: null,
    heatmapOverlayBounds: null,
    heatmapOpacity: 60,
    pathOverlayUrl: null,
    pathOverlayBounds: null,
    pathOpacity: 60,
  },
)

// ========== Emits ==========
const emit = defineEmits<{
  'update:bounds': [bounds: MapBounds]
  'update:scale': [scale: number]
  'selectBlock': [blockId: number, lat: number, lng: number, row: number, col: number]
}>()

// ========== Types ==========
interface MapBounds {
  north: number
  south: number
  east: number
  west: number
  zoom: number
}

// ========== Refs ==========
const mapContainer = ref<HTMLDivElement | null>(null)
let mapInstance: L.Map | null = null
let tileLayer: L.TileLayer | null = null
let gridLayer: L.LayerGroup | null = null
let contourOverlay: L.ImageOverlay | null = null
let heatmapOverlay: L.ImageOverlay | null = null
let pathOverlay: L.ImageOverlay | null = null
const startBlock = ref<number | null>(null)
const startLabel = computed(() => {
  if (startBlock.value === null) return ''
  const id = startBlock.value - 1
  const cols = props.gridCols || 1
  return `${Math.floor(id / cols)},${id % cols}`
})
const searchText = ref('')

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

// ========== 搜索定位 ==========
async function doSearch() {
  const q = searchText.value.trim()
  if (!q || !mapInstance) return

  // 尝试解析为经纬度 (例如: 39.9,116.4 或 39.9 116.4)
  const coordMatch = q.match(/^(-?\d+\.?\d*)\s*[,，\s]\s*(-?\d+\.?\d*)$/)
  if (coordMatch) {
    const lat = parseFloat(coordMatch[1]!)
    const lon = parseFloat(coordMatch[2]!)
    if (lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
      mapInstance.setView([lat, lon], 14)
      return
    }
  }

  // 通过后端代理地理编码
  try {
    const resp = await fetch(`${API_BASE_URL}/api/geocode?q=${encodeURIComponent(q)}`)
    const json = await resp.json() as { success: boolean; results?: Array<{ lat: number; lon: number; display_name: string }>; error?: string }
    if (json.success && json.results && json.results.length > 0) {
      const r = json.results[0]!
      mapInstance.setView([r.lat, r.lon], 14)
      searchText.value = r.display_name.split(',')[0] ?? q
    } else {
      const hint = json.error || '搜索失败'
      const msg = hint.includes('经纬度') ? hint : `${hint}。请尝试直接输入经纬度，如 39.9,116.4`
      alert(msg)
    }
  } catch {
    alert('搜索失败，请检查网络后重试。\n或直接输入经纬度，如 39.9,116.4')
  }
}

// ========== 瓦片图层切换 ==========
function getTileUrl(source: string): string {
  if (source === 'demcontour') {
    return `${API_BASE_URL}/api/tile/demcontour/{z}/{x}/{y}.png`
  }
  return 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
}

function swapTileLayer(source: string) {
  if (!mapInstance) return
  if (tileLayer) mapInstance.removeLayer(tileLayer)
  tileLayer = L.tileLayer(getTileUrl(source), {
    attribution: source === 'demcontour'
      ? '© Open-Meteo DEM | TerraiNav'
      : '© Esri, Maxar, Earthstar Geographics',
    maxZoom: 19,
  }).addTo(mapInstance)
}

// ========== Constants ==========
const GROUND_RESOLUTION_CONST = 156543.03392
const TILE_SIZE = 256

// ========== Computed ==========
const scaleDisplay = computed(() => {
  if (!mapInstance) return ''
  const center = mapInstance.getCenter()
  const scale = GROUND_RESOLUTION_CONST * Math.cos((center.lat * Math.PI) / 180) / 2 ** mapInstance.getZoom()
  const ratio = Math.round(scale * 3779.5) // 96dpi → 1:N scale
  return `${scale.toFixed(2)} m/px (约 1:${ratio.toLocaleString()})`
})

const regionSize = computed(() => {
  if (!mapInstance) return ''
  const bounds = mapInstance.getBounds()
  const nw = bounds.getNorthWest()
  const se = bounds.getSouthEast()
  const latMid = (nw.lat + se.lat) / 2
  const cosLat = Math.cos((latMid * Math.PI) / 180)
  const degToM = 111320
  const widthKm = ((se.lng - nw.lng) * degToM * cosLat) / 1000
  const heightKm = ((nw.lat - se.lat) * degToM) / 1000
  return `${widthKm.toFixed(1)}×${heightKm.toFixed(1)} km`
})

// ========== Grid绘制 ==========
function updateGrid() {
  if (!mapInstance) return
  if (gridLayer) mapInstance.removeLayer(gridLayer)
  gridLayer = L.layerGroup().addTo(mapInstance)

  const bounds = mapInstance.getBounds()
  const nw = bounds.getNorthWest()
  const se = bounds.getSouthEast()
  const rows = props.gridRows
  const cols = props.gridCols
  if (rows <= 0 || cols <= 0) return

  const latStep = (nw.lat - se.lat) / rows
  const lngStep = (se.lng - nw.lng) / cols

  // 网格线
  for (let i = 0; i <= rows; i++) {
    const lat = nw.lat - i * latStep
    L.polyline(
      [
        [lat, nw.lng],
        [lat, se.lng],
      ],
      { color: '#4a6cf7', weight: 2, opacity: 0.6 },
    ).addTo(gridLayer!)
  }
  for (let j = 0; j <= cols; j++) {
    const lng = nw.lng + j * lngStep
    L.polyline(
      [
        [nw.lat, lng],
        [se.lat, lng],
      ],
      { color: '#4a6cf7', weight: 2, opacity: 0.6 },
    ).addTo(gridLayer!)
  }

  // 块号标签
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const centerLat = nw.lat - (r + 0.5) * latStep
      const centerLng = nw.lng + (c + 0.5) * lngStep
      const id = r * cols + c + 1
      const isStart = id === startBlock.value

      const icon = L.divIcon({
        html: `<div style="
          background:${isStart ? '#4a6cf7' : 'rgba(0,0,0,0.75)'};
          color:${isStart ? '#fff' : '#ff0'};
          padding:2px 5px; font-size:10px; border-radius:3px;
          font-weight:bold; white-space:nowrap; font-family:monospace;
          border:${isStart ? '2px solid #fff' : '1px solid rgba(255,255,255,0.3)'};
        ">${r},${c}</div>`,
        className: '',
      })

      const marker = L.marker([centerLat, centerLng], { icon }).addTo(gridLayer!)

      if (props.editable) {
        marker.on('click', () => {
          startBlock.value = id
          updateGrid()
          emit('selectBlock', id, centerLat, centerLng, r, c)
        })
      }
    }
  }
}

// ========== 边界发射 ==========
function emitBounds() {
  if (!mapInstance) return
  const b = mapInstance.getBounds()
  emit('update:bounds', {
    north: b.getNorth(),
    south: b.getSouth(),
    east: b.getEast(),
    west: b.getWest(),
    zoom: mapInstance.getZoom(),
  })

  const center = mapInstance.getCenter()
  const scale = GROUND_RESOLUTION_CONST * Math.cos((center.lat * Math.PI) / 180) / 2 ** mapInstance.getZoom()
  emit('update:scale', scale)
}

// ========== 块选择 ==========
function parseStartPoint(sp: string): { r: number; c: number } | null {
  // 格式: row,col (0-based, 如 0,0 = 左上角)
  const parts = sp.split(',').map((s) => parseInt(s.trim()))
  if (parts.length !== 2 || isNaN(parts[0]) || isNaN(parts[1])) return null
  return { r: parts[0], c: parts[1] }
}

// ========== 生命周期 ==========
onMounted(() => {
  if (!mapContainer.value) return

  mapInstance = L.map(mapContainer.value, {
    center: [props.centerLat, props.centerLng],
    zoom: props.zoomLevel,
    zoomControl: true,
    attributionControl: false,
  })

  // Esri 卫星底图
  swapTileLayer(props.tileSource)

  // Leaflet 自带比例尺控件
  L.control
    .scale({
      metric: true,
      imperial: false,
      position: 'bottomleft',
    })
    .addTo(mapInstance)

  // 初始网格 + 起点
  const sp = parseStartPoint(props.startPoint)
  if (sp) startBlock.value = sp.r * props.gridCols + sp.c + 1

  updateGrid()
  emitBounds()

  mapInstance.on('moveend zoomend', () => {
    updateGrid()
    emitBounds()
  })

  nextTick(() => {
    mapInstance?.invalidateSize()
  })
})

onUnmounted(() => {
  if (mapInstance) {
    mapInstance.remove()
    mapInstance = null
  }
})

// 若 startPoint prop 变化, 更新起点标记
watch(
  () => props.startPoint,
  (val) => {
    const sp = parseStartPoint(val)
    if (sp) {
      startBlock.value = sp.r * props.gridCols + sp.c + 1
    } else {
      startBlock.value = null
    }
    updateGrid()
  },
)

// 若网格参数变换, 重新画网格
watch([() => props.gridRows, () => props.gridCols], () => {
  nextTick(() => {
    updateGrid()
  })
})

// 瓦片源切换
watch(() => props.tileSource, (src) => {
  swapTileLayer(src)
})

// 等高线叠加层管理
function updateContourOverlay() {
  if (!mapInstance) return
  // 移除旧层
  if (contourOverlay) {
    mapInstance.removeLayer(contourOverlay)
    contourOverlay = null
  }
  // 添加新层
  if (props.contourOverlayUrl && props.contourOverlayBounds) {
    const b = props.contourOverlayBounds
    contourOverlay = L.imageOverlay(
      props.contourOverlayUrl,
      [[b.south, b.west], [b.north, b.east]],
      { opacity: 1 - props.contourOpacity / 100 },
    ).addTo(mapInstance)
  }
}

watch(() => props.contourOverlayUrl, () => { updateContourOverlay() })
watch(() => props.contourOverlayBounds, () => { updateContourOverlay() }, { deep: true })

// 透明度变化只更新现有层
watch(() => props.contourOpacity, (val) => {
  if (contourOverlay) contourOverlay.setOpacity(1 - val / 100)
})

// ========== 热力图叠加层 ==========
function updateHeatmapOverlay() {
  if (!mapInstance) return
  if (heatmapOverlay) { mapInstance.removeLayer(heatmapOverlay); heatmapOverlay = null }
  if (props.heatmapOverlayUrl && props.heatmapOverlayBounds) {
    const b = props.heatmapOverlayBounds
    heatmapOverlay = L.imageOverlay(
      props.heatmapOverlayUrl,
      [[b.south, b.west], [b.north, b.east]],
      { opacity: 1 - props.heatmapOpacity / 100 },
    ).addTo(mapInstance)
  }
}
watch(() => props.heatmapOverlayUrl, () => { updateHeatmapOverlay() })
watch(() => props.heatmapOverlayBounds, () => { updateHeatmapOverlay() }, { deep: true })
watch(() => props.heatmapOpacity, (val) => {
  if (heatmapOverlay) heatmapOverlay.setOpacity(1 - val / 100)
})

// ========== 路径图叠加层 ==========
function updatePathOverlay() {
  if (!mapInstance) return
  if (pathOverlay) { mapInstance.removeLayer(pathOverlay); pathOverlay = null }
  if (props.pathOverlayUrl && props.pathOverlayBounds) {
    const b = props.pathOverlayBounds
    pathOverlay = L.imageOverlay(
      props.pathOverlayUrl,
      [[b.south, b.west], [b.north, b.east]],
      { opacity: 1 - props.pathOpacity / 100 },
    ).addTo(mapInstance)
  }
}
watch(() => props.pathOverlayUrl, () => { updatePathOverlay() })
watch(() => props.pathOverlayBounds, () => { updatePathOverlay() }, { deep: true })
watch(() => props.pathOpacity, (val) => {
  if (pathOverlay) pathOverlay.setOpacity(1 - val / 100)
})

// 暴露方法供父组件调用 (热力图/路径叠加)
defineExpose({
  getMap: () => mapInstance,
  addOverlayLayer: (layer: L.Layer) => {
    if (mapInstance) layer.addTo(mapInstance)
  },
  clearOverlays: () => {
    // 保留 gridLayer, 清除其他
  },
})
</script>

<style scoped>
.map-selector {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 8px;
  overflow: hidden;
}

.map-container {
  width: 100%;
  height: 100%;
  min-height: 400px;
  aspect-ratio: 1 / 1;
}

.map-status-bar {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  display: flex;
  gap: 12px;
  background: rgba(0, 0, 0, 0.75);
  border-radius: 8px;
  padding: 6px 16px;
  pointer-events: none;
}

.status-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.status-label {
  font-size: 10px;
  color: #9ca3af;
  text-transform: uppercase;
}

.status-value {
  font-size: 13px;
  color: #fff;
  font-weight: 600;
  white-space: nowrap;
}

/* 搜索定位 */
.map-search-bar {
  position: absolute;
  top: 10px;
  left: 50px;
  z-index: 1000;
  display: flex;
  gap: 0;
  box-shadow: 0 2px 6px rgba(0,0,0,0.3);
  border-radius: 6px;
  overflow: hidden;
}

.search-input {
  width: 240px;
  padding: 0.45rem 0.7rem;
  border: none;
  font-size: 0.82rem;
  outline: none;
  background: white;
  color: #374151;
}

.search-input::placeholder {
  color: #9ca3af;
}

.search-btn {
  padding: 0.45rem 0.7rem;
  border: none;
  background: #4a6cf7;
  color: white;
  cursor: pointer;
  font-size: 0.9rem;
}

.search-btn:hover {
  background: #3b5fe0;
}
</style>
