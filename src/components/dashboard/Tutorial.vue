<template>
  <div class="tutorial-page">
    <div class="page-header">
      <h2>使用教程</h2>
      <p>了解如何使用 TerraiNav 系统的各项功能</p>
    </div>
    
    <div class="tutorial-content">
      <!-- 教程目录 -->
      <div class="tutorial-sidebar">
        <div class="sidebar-nav">
          <button 
            v-for="section in sections" 
            :key="section.id"
            class="nav-btn"
            :class="{ active: activeSection === section.id }"
            @click="activeSection = section.id"
          >
            {{ section.title }}
          </button>
        </div>
      </div>
      
      <!-- 教程内容 -->
      <div class="tutorial-main">
        <!-- 快速开始 -->
        <div v-if="activeSection === 'getting-started'" class="tutorial-section">
          <h3>快速开始</h3>
          <div class="tutorial-steps">
            <div class="step">
              <div class="step-number">1</div>
              <div class="step-content">
                <h4>上传地图</h4>
                <p>点击"上传地图"区域，选择您要分析的地形图片。支持 JPG、PNG 格式，最大 24MB。</p>
              </div>
            </div>
            
            <div class="step">
              <div class="step-number">2</div>
              <div class="step-content">
                <h4>配置 API 密钥</h4>
                <p>在 API 配置区域输入您的百度千帆 API 密钥。如果您还没有密钥，需要先申请。</p>
              </div>
            </div>
            
            <div class="step">
              <div class="step-number">3</div>
              <div class="step-content">
                <h4>设置无人机参数</h4>
                <p>配置巡逻半径、起点坐标和网格分区数量。系统将根据这些参数规划巡逻路径。</p>
              </div>
            </div>
            
            <div class="step">
              <div class="step-number">4</div>
              <div class="step-content">
                <h4>开始分析</h4>
                <p>点击"开始智能分析"按钮，系统将自动分析地形威胁度并生成巡逻路径。</p>
              </div>
            </div>
            
            <div class="step">
              <div class="step-number">5</div>
              <div class="step-content">
                <h4>查看结果</h4>
                <p>在右侧面板中查看热力图、巡逻路径和分析统计信息。可以下载结果或查看详细信息。</p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 地图分析 -->
        <div v-if="activeSection === 'map-analysis'" class="tutorial-section">
          <h3>地图分析功能</h3>
          <div class="feature-grid">
            <div class="feature-card">
              <div class="feature-icon">🗺️</div>
              <h4>网格分区</h4>
              <p>将地图划分为 M×N 个区块，便于分区巡逻和管理。点击区块可以查看详细信息和操作。</p>
            </div>
            
            <div class="feature-card">
              <div class="feature-icon">🔥</div>
              <h4>威胁度分析</h4>
              <p>基于我们独创的AI分析+威胁度计算算法分析地形威胁度，生成热力图。红色表示高威胁区域，蓝色表示低威胁区域。</p>
            </div>
            
            <div class="feature-card">
              <div class="feature-icon">🛣️</div>
              <h4>路径规划</h4>
              <p>自动生成最优巡逻路径，帮助排查高威胁区域，确保无人机巡逻安全和高效。</p>
            </div>
            
            <div class="feature-card">
              <div class="feature-icon">📊</div>
              <h4>统计分析</h4>
              <p>提供详细的统计数据，包括路径长度、巡逻点判定和统计等。</p>
            </div>
          </div>
        </div>
        
        <!-- 无人机参数配置 -->
        <div v-if="activeSection === 'drone-params'" class="tutorial-section">
          <h3>无人机参数配置</h3>
          <div class="param-guide">
            <div class="param-item">
              <h4>巡逻半径</h4>
              <p>无人机单次巡逻能够覆盖的范围半径。值越大，单次巡逻覆盖面积越大，但可能降低精度。</p>
              <p class="param-hint">一般范围为10-100米</p>
            </div>
            
            <div class="param-item">
              <h4>巡逻起点</h4>
              <p>无人机巡逻的起始位置坐标。格式为"x,y"，例如"100,200"。我们会在视图上显示该点以帮助您定位。</p>
              <p class="param-hint">若是机动部署，建议选择地图边缘或易于起飞的位置</p>
            </div>
            
            <div class="param-item">
              <h4>网格分区</h4>
              <p>将巡逻区域划分为 M(横向)×N(纵向) 个区块。格式为"M*N"，例如"4 * 4"。</p>
              <p class="param-hint">区块越多，巡逻越精细，但分析时间越长</p>
            </div>
            
            <div class="param-item">
              <h4>输出质量</h4>
              <p>选择分析结果的输出质量。高质量适合打印和演示，低质量适合快速预览。</p>
              <p class="param-hint">高清：1920×1080 | 标准：1280×720 | 快速：960×540</p>
            </div>
          </div>
        </div>
        
        <!-- 常见问题 -->
        <div v-if="activeSection === 'faq'" class="tutorial-section">
          <h3>常见问题</h3>
          <div class="faq-list">
            <div v-for="faq in faqs" :key="faq.id" class="faq-item">
              <button class="faq-question" @click="toggleFAQ(faq.id)">
                {{ faq.question }}
                <span class="faq-icon">{{ expandedFAQ === faq.id ? '−' : '+' }}</span>
              </button>
              <div v-if="expandedFAQ === faq.id" class="faq-answer">
                {{ faq.answer }}
              </div>
            </div>
          </div>
        </div>
        
        <!-- 联系我们 -->
        <div v-if="activeSection === 'contact'" class="tutorial-section">
          <h3>联系我们</h3>
          <div class="contact-info">
            <div class="contact-item">
              <h4>技术支持</h4>
              <p>邮箱：13227088780@163.com</p>
            </div>
            
            <div class="contact-item">
              <h4>官方网站</h4>
              <p>https://www.terrainav.com</p>
            </div>
            
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

// 激活的教程部分
const activeSection = ref('getting-started')

// 教程部分列表
const sections = [
  { id: 'getting-started', title: '快速开始' },
  { id: 'map-analysis', title: '地图分析' },
  { id: 'drone-params', title: '参数配置' },
  { id: 'faq', title: '常见问题' },
  { id: 'contact', title: '联系我们' }
]

// 常见问题
const faqs = ref([
  {
    id: 1,
    question: '如何获取百度千帆 API 密钥？',
    answer: '访问百度智能云官网，注册账号后进入控制台，在"产品服务"中找到"千帆"，按照指引创建应用并获取 API 密钥。'
  },
  {
    id: 2,
    question: '支持哪些地图格式？',
    answer: '支持 JPG、PNG 格式的图片，最大文件大小为 24MB。建议使用高清、无压缩的地图图片以获得最佳分析效果。'
  },
  {
    id: 3,
    question: '分析结果可以导出吗？',
    answer: '可以，在分析结果页面点击"下载"按钮，可以导出热力图、巡逻路径图和分析报告。'
  },
  {
    id: 4,
    question: '系统对硬件有什么要求？',
    answer: '推荐使用现代浏览器（Chrome 90+、Firefox 88+、Safari 14+），需要网络连接以调用 API 服务。'
  },
  {
    id: 5,
    question: '数据安全如何保障？',
    answer: '所有上传的地图数据和分析结果都存储在本地，不会上传到服务器。API 调用通过 HTTPS 加密传输。'
  }
])

// 展开的FAQ
const expandedFAQ = ref(null)

// 切换FAQ展开状态
const toggleFAQ = (id) => {
  if (expandedFAQ.value === id) {
    expandedFAQ.value = null
  } else {
    expandedFAQ.value = id
  }
}
</script>

<style scoped>
.tutorial-page {
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

.tutorial-content {
  display: flex;
  gap: 2rem;
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
}

/* 侧边栏 */
.tutorial-sidebar {
  width: 240px;
  flex-shrink: 0;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  position: sticky;
  top: 2rem;
}

.nav-btn {
  padding: 0.8rem 1rem;
  text-align: left;
  border: none;
  background: none;
  color: #6b7280;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.3s;
  font-size: 0.95rem;
  position: relative;
}

.nav-btn:hover {
  background: #f3f4f6;
  color: #1a2980;
}

.nav-btn.active {
  background: linear-gradient(90deg, rgba(26, 41, 128, 0.1), rgba(38, 208, 206, 0.1));
  color: #1a2980;
  font-weight: 500;
}

.nav-btn.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, #1a2980, #26d0ce);
  border-radius: 0 4px 4px 0;
}

/* 主要内容 */
.tutorial-main {
  flex: 1;
  min-width: 0;
}

.tutorial-section {
  animation: fadeIn 0.3s ease;
}

.tutorial-section h3 {
  font-size: 1.5rem;
  color: #1a2980;
  margin-bottom: 1.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #e5e7eb;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 步骤样式 */
.tutorial-steps {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.step {
  display: flex;
  gap: 1.5rem;
  padding: 1.5rem;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  transition: transform 0.3s;
}

.step:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
}

.step-number {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(90deg, #1a2980, #26d0ce);
  color: white;
  border-radius: 50%;
  font-weight: bold;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.step-content h4 {
  font-size: 1.2rem;
  color: #1a2980;
  margin-bottom: 0.5rem;
}

.step-content p {
  color: #4b5563;
  line-height: 1.5;
}

/* 功能网格 */
.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.feature-card {
  padding: 1.5rem;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  transition: transform 0.3s, box-shadow 0.3s;
}

.feature-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.05);
}

.feature-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.feature-card h4 {
  font-size: 1.1rem;
  color: #1a2980;
  margin-bottom: 0.5rem;
}

.feature-card p {
  color: #4b5563;
  font-size: 0.9rem;
  line-height: 1.5;
}

/* 参数指南 */
.param-guide {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.param-item {
  padding: 1.5rem;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.param-item h4 {
  font-size: 1.1rem;
  color: #1a2980;
  margin-bottom: 0.5rem;
}

.param-item p {
  color: #4b5563;
  line-height: 1.5;
  margin-bottom: 0.5rem;
}

.param-hint {
  font-size: 0.9rem;
  color: #6b7280;
  font-style: italic;
  background: rgba(255, 255, 255, 0.8);
  padding: 0.5rem 0.8rem;
  border-radius: 4px;
  border-left: 3px solid #1a2980;
}

/* 常见问题 */
.faq-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.faq-item {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.faq-question {
  width: 100%;
  padding: 1rem 1.5rem;
  text-align: left;
  border: none;
  background: #f9fafb;
  color: #1a2980;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background 0.3s;
}

.faq-question:hover {
  background: #f3f4f6;
}

.faq-icon {
  font-size: 1.2rem;
  font-weight: bold;
}

.faq-answer {
  padding: 1.5rem;
  background: white;
  color: #4b5563;
  line-height: 1.6;
  border-top: 1px solid #e5e7eb;
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from { opacity: 0; max-height: 0; }
  to { opacity: 1; max-height: 500px; }
}

/* 联系信息 */
.contact-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.contact-item {
  padding: 1.5rem;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.contact-item h4 {
  font-size: 1.1rem;
  color: #1a2980;
  margin-bottom: 1rem;
}

.contact-item p {
  color: #4b5563;
  margin-bottom: 0.5rem;
  line-height: 1.5;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .tutorial-content {
    flex-direction: column;
  }
  
  .tutorial-sidebar {
    width: 100%;
  }
  
  .sidebar-nav {
    flex-direction: row;
    overflow-x: auto;
    padding-bottom: 0.5rem;
  }
  
  .nav-btn {
    white-space: nowrap;
  }
  
  .step {
    flex-direction: column;
    gap: 1rem;
  }
  
  .step-number {
    align-self: flex-start;
  }
}
</style>