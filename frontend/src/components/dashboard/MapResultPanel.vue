<template>
  <!-- 空状态 - 引导文案 -->
  <div v-if="!hasResult && analysisProgress.status !== 'running' && analysisProgress.status !== 'pending'" class="empty-state">
    <div class="empty-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7"/><line x1="16" y1="5" x2="22" y2="5"/><line x1="19" y1="2" x2="19" y2="8"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>
      </svg>
    </div>
    <p class="empty-title">暂无分析结果</p>
    <p class="empty-desc">在地图中选定区域并设置网格参数后，<br/>点击左侧"开始智能分析"即可查看威胁评估数据</p>
  </div>

  <!-- 结果统计信息 -->
  <div v-if="stats" class="stats-card">
    <h3>分析统计</h3>
    <div class="stats-grid">
      <div class="stat-item">
        <div class="stat-icon"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg></div>
        <div class="stat-content"><span class="stat-label">最高威胁度</span><span class="stat-value">{{ stats.maxThreat }}</span></div>
      </div>
      <div class="stat-item">
        <div class="stat-icon"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg></div>
        <div class="stat-content"><span class="stat-label">平均威胁度</span><span class="stat-value">{{ stats.avgThreat }}</span></div>
      </div>
      <div class="stat-item">
        <div class="stat-icon"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
        <div class="stat-content"><span class="stat-label">分析用时</span><span class="stat-value">{{ stats.time }} s</span></div>
      </div>
      <div class="stat-item" v-if="stats.pathLength">
        <div class="stat-icon"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></div>
        <div class="stat-content"><span class="stat-label">路径长度</span><span class="stat-value">{{ stats.pathLength }}</span></div>
      </div>
    </div>
    <div class="result-actions" v-if="stats">
      <button class="action-btn" @click="$emit('show-path-details')">查看详细坐标</button>
      <button class="action-btn" @click="$emit('download-image', 'heatmap')">下载热力图</button>
      <button class="action-btn" @click="$emit('download-image', 'path')">下载路径图</button>
    </div>
  </div>

  <!-- 高威胁巡逻建议点表格 -->
  <div class="threat-points-card">
    <div class="threat-header">
      <h3>高威胁巡逻建议点</h3>
      <span v-if="threatPoints.length > 0" class="threat-count">共 {{ threatPoints.length }} 个建议点</span>
      <span v-else class="threat-count no-data">等待分析结果</span>
    </div>
    <div v-if="threatPoints.length > 0" class="threat-points-table">
      <table>
        <thead><tr><th>排序</th><th>所属区块</th><th>威胁度</th><th>图上坐标</th><th>威胁原因分析</th></tr></thead>
        <tbody>
          <tr v-for="point in threatPoints" :key="point.id" :class="getRowClass(point.threatScore)">
            <td class="rank-cell"><span class="rank-badge" :class="getThreatColorClass(point.threatScore)">{{ point.rank }}</span></td>
            <td class="block-cell"><span class="block-badge">{{ point.block }}</span></td>
            <td class="threat-score-cell"><span class="threat-score" :class="getThreatColorClass(point.threatScore)">{{ point.threatScore.toFixed(1) }}</span></td>
            <td class="coordinate-cell"><span class="coordinate">{{ point.coordinate }}</span></td>
            <td class="reason-cell"><div class="reason-text">{{ point.reason }}</div></td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="no-data-section">
      <div class="no-data-placeholder">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
        <p>暂无高威胁巡逻建议点</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

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

interface Stats {
  pathLength: string
  maxThreat: string
  avgThreat: string
  time: string
}

const props = defineProps<{
  stats: Stats | null
  threatPoints: ThreatPoint[]
  analysisProgress: { status: string }
}>()

defineEmits<{
  'download-image': [type: 'heatmap' | 'path']
  'show-path-details': []
}>()

const hasResult = computed(() => props.stats !== null)

function getThreatColorClass(score: number) {
  if (score >= 75) return 'score-red'
  if (score >= 60) return 'score-yellow'
  if (score >= 40) return 'score-green'
  return 'score-default'
}

function getRowClass(score: number) {
  if (score >= 75) return 'high-threat-row'
  if (score >= 60) return 'medium-threat-row'
  if (score >= 40) return 'low-threat-row'
  return ''
}
</script>

<style scoped>
.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 2rem 1rem; text-align: center;
  background: white; border-radius: 12px; border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  min-height: 140px;
}
.empty-icon { margin-bottom: 0.75rem; opacity: 0.6; }
.empty-title { font-size: 0.95rem; color: #475569; font-weight: 600; margin-bottom: 0.3rem; }
.empty-desc { font-size: 0.8rem; color: #94a3b8; line-height: 1.5; margin: 0; }

.stats-card {
  background: white; border-radius: 12px; padding: 0.9rem 1.25rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04); border: 1px solid #e5e7eb; margin-bottom: 0.75rem;
}
.stats-card h3 { font-size: 0.9rem; color: #334155; margin-bottom: 0.5rem; font-weight: 600; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 0.5rem; }
.stat-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.6rem; background: #f8fafc; border-radius: 6px; }
.stat-icon { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; background: #eef2ff; border-radius: 6px; color: #4f46e5; flex-shrink: 0; }
.stat-icon svg { width: 16px; height: 16px; }
.stat-label { display: block; font-size: 0.7rem; color: #64748b; }
.stat-value { font-size: 1rem; font-weight: 600; color: #0f172a; }
.result-actions { margin-top: 0.5rem; display: flex; gap: 0.35rem; flex-wrap: wrap; }
.action-btn { padding: 0.35rem 0.7rem; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 5px; cursor: pointer; font-size: 0.75rem; color: #475569; transition: background 0.15s; }
.action-btn:hover { background: #e2e8f0; }

.threat-points-card {
  background: white; border-radius: 12px; padding: 0.9rem 1.25rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04); border: 1px solid #e5e7eb;
}
.threat-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
.threat-header h3 { font-size: 0.9rem; color: #334155; font-weight: 600; }
.threat-count { font-size: 0.75rem; color: #64748b; }
.threat-count.no-data { color: #94a3b8; }
.threat-points-table { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
th { text-align: left; padding: 0.4rem 0.5rem; font-size: 0.72rem; color: #64748b; border-bottom: 2px solid #e5e7eb; font-weight: 600; text-transform: uppercase; letter-spacing: 0.025em; }
td { padding: 0.35rem 0.5rem; font-size: 0.8rem; border-bottom: 1px solid #f1f5f9; }
.rank-badge { display: inline-flex; width: 22px; height: 22px; align-items: center; justify-content: center; border-radius: 50%; font-size: 0.7rem; font-weight: 600; color: white; }
.score-red { background: #ef4444; }
.score-yellow { background: #f59e0b; }
.score-green { background: #10b981; }
.score-default { background: #94a3b8; }
.block-badge { padding: 0.15rem 0.4rem; background: #eff6ff; color: #2563eb; border-radius: 4px; font-size: 0.72rem; font-weight: 500; }
.threat-score { font-weight: 600; }
.coordinate { font-size: 0.75rem; color: #64748b; }
.reason-text { font-size: 0.75rem; color: #475569; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.high-threat-row { background: #fef2f2; }
.medium-threat-row { background: #fffbeb; }
.low-threat-row { background: #f0fdf4; }
.no-data-section { text-align: center; padding: 1rem; }
.no-data-placeholder svg { width: 32px; height: 32px; opacity: 0.4; }
.no-data-placeholder p { color: #94a3b8; margin-top: 0.3rem; font-size: 0.82rem; }
</style>
