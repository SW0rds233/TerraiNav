<template>
  <div class="upload-card">
    <h2 class="card-title">地形路径规划</h2>
    <p class="card-subtitle">在地图上选择区域，自动生成最优巡逻路径</p>

    <!-- 区域信息 -->
    <div class="region-info">
      <p>在地图上拖拽/缩放，调整目标区域</p>
      <div class="map-source-selector">
        <label>地图图层</label>
        <select :value="tileSource" @change="onTileSourceChange" class="source-select">
          <option value="esri">卫星影像 (Esri)</option>
          <option value="demcontour">等高线地形图 (自动构造)</option>
        </select>
      </div>
      <div v-if="mapScale > 0" class="scale-display">
        比例尺: {{ mapScale.toFixed(2) }} m/px
      </div>
    </div>

    <!-- 等高线叠加 -->
    <div class="contour-controls">
      <button
        class="contour-btn"
        :class="{ active: contourEnabled }"
        @click="$emit('toggle-contour')"
        :disabled="!canContour"
      >
        {{ contourEnabled ? '取消等高线叠加' : '固定区域 / 生成等高线' }}
      </button>
      <div v-if="contourEnabled" class="opacity-control">
        <label>叠加透明度:</label>
        <input type="range" :value="contourOpacity" @input="onOpacityChange" min="0" max="100" class="opacity-slider" />
        <span>{{ contourOpacity }}%</span>
      </div>
    </div>

    <!-- API配置 -->
    <div class="api-config">
      <h3>API配置</h3>
      <input :value="apiKey" @input="onApiKeyChange" type="password" placeholder="请输入API密钥" class="api-input" />
      <button class="api-test-btn" @click="$emit('test-api')">测试连接</button>
    </div>

    <!-- 输出选项 -->
    <div class="output-options">
      <h3>输出选项</h3>
      <div class="option-group">
        <h4>输出类型</h4>
        <label><input type="checkbox" v-model="localOutputOptions.heatmap" />生成威胁度热力图</label>
        <label><input type="checkbox" v-model="localOutputOptions.path" />生成巡逻路线图</label>
      </div>
      <div class="option-group">
        <h4>输出质量</h4>
        <select v-model="localOutputOptions.quality" class="quality-select">
          <option value="low">低质量 (快速)</option>
          <option value="medium">中等质量</option>
          <option value="high">高质量 (推荐)</option>
        </select>
      </div>
    </div>

    <!-- 任务名称 -->
    <div class="taskname-params">
      <h3>任务名称</h3>
      <div class="param-group">
        <input type="text" :value="taskName" @input="onTaskNameChange" class="param-input" placeholder="请输入任务名称（可选）" />
      </div>
    </div>

    <!-- 无人机巡逻参数 -->
    <div class="drone-params">
      <h3>无人机巡逻参数</h3>
      <div class="param-group">
        <label>巡逻起始区块 (x,y)</label>
        <input type="text" :value="startPoint" @input="onStartPointChange" class="param-input" placeholder="例如: 1,1" />
      </div>
      <div class="param-group">
        <label>巡逻区块划分 (m×n)</label>
        <input type="text" :value="gridBlocks" @input="onGridBlocksChange" class="param-input" placeholder="例如: 4 * 4" :class="{ invalid: !gridBlocksValid }" />
        <p class="param-hint">格式: 行数*列数，例如: 3 * 4 表示3行4列，共12个区块</p>
        <div v-if="!gridBlocksValid && gridBlocks" class="error-message">
          格式错误，请输入如"4 * 3"的格式
        </div>
        <div v-if="gridBlocksValid" class="grid-info">
          将划分为 {{ parsedGridRows }}×{{ parsedGridCols }} 个区块，共
          {{ parsedGridRows * parsedGridCols }} 个巡逻区块
        </div>
      </div>
    </div>

    <!-- 开始分析按钮 -->
    <button class="analyze-btn" @click="$emit('start-analysis')" :disabled="!canAnalyze">
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
    <div class="analysis-tip">{{ analysisTip }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface AnalysisProgress {
  status: 'idle' | 'pending' | 'running' | 'completed' | 'failed'
  message: string
  progress_percent: number
}

const props = defineProps<{
  tileSource: string
  apiKey: string
  taskName: string
  startPoint: string
  gridBlocks: string
  analyzing: boolean
  canAnalyze: boolean
  mapScale: number
  gridBlocksValid: boolean
  parsedGridRows: number
  parsedGridCols: number
  analysisProgress: AnalysisProgress
  analysisTip: string
  outputOptions: { heatmap: boolean; path: boolean; quality: string }
  contourEnabled: boolean
  canContour: boolean
  contourOpacity: number
}>()

const emit = defineEmits<{
  'update:tileSource': [value: string]
  'update:apiKey': [value: string]
  'update:taskName': [value: string]
  'update:startPoint': [value: string]
  'update:gridBlocks': [value: string]
  'update:outputOptions': [value: { heatmap: boolean; path: boolean; quality: string }]
  'update:contourOpacity': [value: number]
  'test-api': []
  'start-analysis': []
  'toggle-contour': []
}>()

const localOutputOptions = ref({ ...props.outputOptions })

watch(localOutputOptions, (val) => emit('update:outputOptions', { ...val }), { deep: true })
watch(() => props.outputOptions, (val) => { localOutputOptions.value = { ...val } })

function onTileSourceChange(e: Event) { emit('update:tileSource', (e.target as HTMLSelectElement).value) }
function onApiKeyChange(e: Event) { emit('update:apiKey', (e.target as HTMLInputElement).value) }
function onTaskNameChange(e: Event) { emit('update:taskName', (e.target as HTMLInputElement).value) }
function onStartPointChange(e: Event) { emit('update:startPoint', (e.target as HTMLInputElement).value) }
function onGridBlocksChange(e: Event) { emit('update:gridBlocks', (e.target as HTMLInputElement).value) }
function onOpacityChange(e: Event) { emit('update:contourOpacity', parseInt((e.target as HTMLInputElement).value)) }
</script>

<style scoped>
/* 卡片基础 */
.upload-card {
  background: white; border-radius: 12px; padding: 1.5rem 1.5rem 1.25rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04); border: 1px solid #e5e7eb;
}
.card-title { font-size: 1.2rem; color: #1a2980; margin-bottom: 0.25rem; font-weight: 700; }
.card-subtitle { color: #6b7280; font-size: 0.82rem; margin-bottom: 1.25rem; }

/* 区域信息 */
.region-info {
  border: 1px dashed #cbd5e1; border-radius: 8px; padding: 0.75rem 1rem;
  background: #f8fafc; margin-bottom: 1.25rem;
}
.region-info p { margin: 0 0 0.5rem 0; color: #475569; font-weight: 500; font-size: 0.82rem; }
.map-source-selector { margin-bottom: 0.5rem; }
.map-source-selector label { font-size: 0.78rem; color: #64748b; margin-bottom: 0.25rem; display: block; font-weight: 500; }
.source-select { width: 100%; padding: 0.45rem 0.6rem; border: 1px solid #d1d5db; border-radius: 6px; font-size: 0.82rem; background: white; transition: border-color 0.15s; }
.source-select:focus { outline: none; border-color: #4a6cf7; box-shadow: 0 0 0 3px rgba(74,108,247,0.1); }
.scale-display { font-size: 0.8rem; color: #475569; font-weight: 500; }

/* 等高线叠加 */
.contour-controls { margin-bottom: 1.25rem; }
.contour-btn { width: 100%; padding: 0.55rem; border: 1px solid #c7d2fe; border-radius: 6px; background: #eef2ff; color: #4338ca; cursor: pointer; font-size: 0.82rem; font-weight: 500; transition: all 0.15s; }
.contour-btn:hover { background: #e0e7ff; border-color: #a5b4fc; }
.contour-btn.active { background: #4f46e5; color: white; border-color: #4f46e5; }
.contour-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.opacity-control { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.5rem; font-size: 0.78rem; color: #64748b; }
.opacity-slider { flex: 1; accent-color: #4f46e5; height: 4px; }

/* API配置 */
.api-config { margin-bottom: 1.25rem; }
.api-config h3 { font-size: 0.85rem; color: #334155; margin-bottom: 0.5rem; font-weight: 600; }
.api-input { width: 100%; padding: 0.55rem 0.7rem; border: 1px solid #d1d5db; border-radius: 6px; font-size: 0.82rem; margin-bottom: 0.5rem; transition: border-color 0.15s, box-shadow 0.15s; }
.api-input:focus { outline: none; border-color: #4a6cf7; box-shadow: 0 0 0 3px rgba(74,108,247,0.1); }
.api-input::placeholder { color: #9ca3af; }
.api-test-btn { width: 100%; background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; padding: 0.45rem; border-radius: 6px; cursor: pointer; font-size: 0.8rem; transition: background 0.15s; }
.api-test-btn:hover { background: #e2e8f0; }

/* 输出选项 */
.output-options { margin-bottom: 1.25rem; }
.output-options h3 { font-size: 0.85rem; color: #334155; margin-bottom: 0.5rem; font-weight: 600; }
.option-group { margin-bottom: 0.5rem; }
.option-group h4 { font-size: 0.78rem; color: #64748b; margin-bottom: 0.25rem; font-weight: 500; }
.option-group label { display: flex; align-items: center; gap: 0.4rem; color: #475569; font-size: 0.82rem; margin-bottom: 0.3rem; cursor: pointer; }
.option-group input[type="checkbox"] { accent-color: #4a6cf7; width: 15px; height: 15px; }
.quality-select { width: 100%; padding: 0.45rem 0.6rem; border: 1px solid #d1d5db; border-radius: 6px; font-size: 0.82rem; background: white; transition: border-color 0.15s; }
.quality-select:focus { outline: none; border-color: #4a6cf7; box-shadow: 0 0 0 3px rgba(74,108,247,0.1); }

/* 任务名称 */
.taskname-params { margin-bottom: 1.25rem; }
.taskname-params h3 { font-size: 0.85rem; color: #334155; margin-bottom: 0.5rem; font-weight: 600; }

/* 无人机参数 */
.drone-params { margin-bottom: 1.25rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; }
.drone-params h3 { font-size: 0.9rem; color: #1e293b; margin-bottom: 0.6rem; font-weight: 700; }
.param-group { margin-bottom: 0.75rem; }
.param-group:last-child { margin-bottom: 0; }
.param-group label { display: block; color: #475569; font-size: 0.8rem; margin-bottom: 0.25rem; font-weight: 500; }
.param-input { width: 100%; padding: 0.55rem 0.7rem; border: 1px solid #d1d5db; border-radius: 6px; font-size: 0.82rem; transition: border-color 0.15s, box-shadow 0.15s; }
.param-input:focus { outline: none; border-color: #4a6cf7; box-shadow: 0 0 0 3px rgba(74,108,247,0.1); }
.param-input::placeholder { color: #9ca3af; }
.param-input.invalid { border-color: #ef4444; box-shadow: 0 0 0 3px rgba(239,68,68,0.1); }
.param-hint { font-size: 0.72rem; color: #94a3b8; margin-top: 0.2rem; line-height: 1.3; }
.grid-info { margin-top: 0.4rem; padding: 0.5rem 0.7rem; background: #f0f9ff; border-radius: 6px; border: 1px solid #bae6fd; color: #0369a1; font-size: 0.75rem; font-weight: 500; line-height: 1.3; }
.error-message { margin-top: 0.3rem; padding: 0.4rem 0.7rem; background: #fef2f2; border-radius: 6px; border: 1px solid #fecaca; color: #dc2626; font-size: 0.75rem; line-height: 1.3; }

/* 分析按钮 */
.analyze-btn {
  width: 100%; background: #1e40af; color: white; padding: 0.75rem; border: none; border-radius: 8px;
  font-size: 0.9rem; font-weight: 600; cursor: pointer; margin-bottom: 0.6rem; transition: background 0.15s;
}
.analyze-btn:hover:not(:disabled) { background: #1e3a8a; }
.analyze-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.analyze-btn .spinner { animation: spin 1s linear infinite; width: 18px; height: 18px; margin-right: 6px; }
@keyframes spin { 100% { transform: rotate(360deg); } }
.analyzing { display: inline-flex; align-items: center; }

/* 进度条 */
.analysis-progress { margin-bottom: 0.6rem; }
.progress-text { color: #475569; font-size: 0.78rem; margin-bottom: 0.25rem; }
.progress-bar { background: #e5e7eb; border-radius: 4px; height: 5px; overflow: hidden; }
.progress-fill { background: #1e40af; height: 100%; transition: width 0.3s; }

.analysis-tip { color: #64748b; font-size: 0.78rem; text-align: center; }
</style>
