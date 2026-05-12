<template>
  <div class="help-page">
    <div class="page-header">
      <h1>帮助中心</h1>
      <p>常见问题和使用指南</p>
    </div>

    <div class="help-search">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索帮助内容..."
        class="search-input"
        @keyup.enter="searchHelp"
      />
      <button class="search-btn" @click="searchHelp">
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
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
      </button>
    </div>

    <div class="help-content">
      <div class="help-sections">
        <!-- 快速入门 -->
        <div class="help-section">
          <h2>快速入门</h2>
          <div class="section-content">
            <p>
              欢迎使用 TerraiNav 地形适应无人机巡逻系统。以下是一个简明的入门指南，帮助您快速上手：
            </p>

            <div class="guide-steps">
              <div class="guide-step">
                <h3>第一步：注册与登录</h3>
                <p>如果您是新用户，请先注册账户。已有账户的用户可以直接登录。</p>
              </div>

              <div class="guide-step">
                <h3>第二步：配置 API 密钥</h3>
                <p>进入"地图分析"页面，在左侧面板的"API配置"区域输入您的阿里云百炼 API 密钥。</p>
              </div>

              <div class="guide-step">
                <h3>第三步：上传地图</h3>
                <p>点击上传区域，选择您要分析的地形图片。系统支持 JPG 和 PNG 格式。</p>
              </div>

              <div class="guide-step">
                <h3>第四步：设置参数</h3>
                <p>配置无人机巡逻参数，包括任务名、起点区块和网格分区数量。</p>
              </div>

              <div class="guide-step">
                <h3>第五步：开始分析</h3>
                <p>点击"开始智能分析"按钮，系统将自动分析地形并生成巡逻路径。</p>
              </div>

              <div class="guide-step">
                <h3>第六步：查看结果</h3>
                <p>在右侧面板查看分析结果，包括热力图、巡逻路径和统计信息。</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 常见问题 -->
        <div class="help-section">
          <h2>常见问题</h2>
          <div class="section-content">
            <div class="faq-list">
              <div v-for="faq in filteredFAQs" :key="faq.id" class="faq-item">
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
        </div>

        <!-- 故障排除 -->
        <div class="help-section">
          <h2>故障排除</h2>
          <div class="section-content">
            <div class="troubleshooting-list">
              <div class="trouble-item">
                <h3>无法上传地图</h3>
                <p><strong>可能原因：</strong>文件格式不支持、文件大小超过限制、网络连接问题</p>
                <p>
                  <strong>解决方法：</strong>检查文件格式（支持 JPG、PNG），确保文件大小不超过
                  24MB，检查网络连接
                </p>
              </div>

              <div class="trouble-item">
                <h3>API 密钥验证失败</h3>
                <p><strong>可能原因：</strong>密钥输入错误、密钥已过期、权限不足</p>
                <p>
                  <strong>解决方法：</strong>检查密钥是否正确，重新生成密钥，确保密钥有足够的权限
                </p>
              </div>

              <div class="trouble-item">
                <h3>分析结果不准确</h3>
                <p><strong>可能原因：</strong>地图质量差、参数设置不当、网络延迟</p>
                <p><strong>解决方法：</strong>使用高质量地图，调整巡逻参数，检查网络连接</p>
              </div>

              <div class="trouble-item">
                <h3>系统运行缓慢</h3>
                <p>
                  <strong>可能原因：</strong>网络延迟、浏览器缓存过多、硬件性能不足、分块数量过多
                </p>
                <p>
                  <strong>解决方法：</strong
                  >检查网络连接，清除浏览器缓存，升级硬件配置，减少分块数量
                </p>
              </div>

              <div class="trouble-item">
                <h3>无法导出结果</h3>
                <p><strong>可能原因：</strong>浏览器限制、文件权限问题、存储空间不足</p>
                <p><strong>解决方法：</strong>检查浏览器设置，确保有文件写入权限，清理存储空间</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 最佳实践 -->
        <div class="help-section">
          <h2>最佳实践</h2>
          <div class="section-content">
            <div class="practice-list">
              <div class="practice-item">
                <h3>地图选择建议</h3>
                <ul>
                  <li>使用高分辨率、无压缩的地图图片</li>
                  <li>确保地图比例尺准确</li>
                  <li>避免使用有过多文字标注的地图</li>
                  <li>选择包含完整地形特征的地图</li>
                </ul>
              </div>

              <div class="practice-item">
                <h3>参数设置建议</h3>
                <ul>
                  <li>根据实际巡逻范围设置合适的巡逻分块数量</li>
                  <li>起点坐标应设置在易于起飞且便于到达的位置</li>
                  <li>网格分区数量根据巡逻精度需求调整</li>
                  <li>初次使用时建议使用默认参数</li>
                </ul>
              </div>

              <div class="practice-item">
                <h3>系统使用建议</h3>
                <ul>
                  <li>定期保存工作进度</li>
                  <li>导出重要分析结果进行备份</li>
                  <li>及时更新 API 密钥</li>
                  <li>定期清理浏览器缓存</li>
                </ul>
              </div>

              <div class="practice-item">
                <h3>性能优化建议</h3>
                <ul>
                  <li>在良好的网络环境下使用系统</li>
                  <li>使用现代浏览器（Chrome、Firefox 等）</li>
                  <li>关闭不必要的浏览器标签页</li>
                  <li>定期重启浏览器</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <!-- 联系我们 -->
        <div class="help-section">
          <h2>联系我们</h2>
          <div class="section-content">
            <div class="contact-info">
              <div class="contact-item">
                <h3>技术支持</h3>
                <p><strong>邮箱：</strong>2698889584@qq.com</p>
                <p><strong>工作时间：</strong>周一至周五 9:00-18:00</p>
              </div>

              <div class="contact-item">
                <h3>源码资源</h3>
                <p><strong>GitHub 仓库：</strong>https://github.com/SW0rds233/TerraiNav</p>
              </div>

              <div class="contact-item">
                <h3>社区支持</h3>
                <p><strong>GitHub Issues：</strong>https://github.com/SW0rds233/issues</p>
                <p><strong>Stack Overflow：</strong>标签 #terrainav</p>
              </div>

              <div class="contact-item">
                <h3>关注我们</h3>
                <p><strong>GitHub：</strong>@terrainav</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

// 搜索查询
const searchQuery = ref('')

// 常见问题列表
const faqs = ref([
  {
    id: 1,
    question: '如何获取阿里云百炼 API 密钥？',
    answer:
      '访问百度智能云官网（cloud.baidu.com），注册账号后进入控制台，在"产品服务"中找到"千帆"，按照指引创建应用并获取 API 密钥。您需要完成实名认证才能使用 API 服务。',
  },
  {
    id: 2,
    question: '支持哪些地图格式和大小？',
    answer:
      '系统支持 JPG 和 PNG 格式的地图图片，最大文件大小为 24MB。建议使用分辨率在 1920×1080 到 3840×2160 之间的图片，以获得最佳分析效果。',
  },
  {
    id: 3,
    question: '分析结果可以导出哪些格式？',
    answer:
      '可以导出 PNG 格式的热力图和巡逻路径图，以及 PDF 格式的分析报告。点击分析结果页面的"下载"按钮即可导出。',
  },
  {
    id: 4,
    question: '系统对浏览器有什么要求？',
    answer:
      '推荐使用现代浏览器，如 Chrome 90+、Firefox 88+、Safari 14+ 或 Edge 90+。需要启用 JavaScript 和 Cookies。',
  },
  {
    id: 5,
    question: '数据是否安全？',
    answer:
      '所有上传的地图数据和分析结果都存储在您的本地浏览器中，不会上传到我们的服务器。API 调用通过 HTTPS 加密传输，确保数据传输安全。',
  },
  {
    id: 6,
    question: '如何设置合适的巡逻参数？',
    answer:
      '网格分区数量建议为 4×4 到 8×8，分区越多分析越精细但耗时越长。起点坐标建议设置在易于起飞的位置。',
  },
  {
    id: 7,
    question: '分析需要多长时间？',
    answer:
      '分析时间取决于地图大小、网格分区数量和网络状况。通常 50分块以下 的地图分析需要 4 分钟左右。如果分析时间过长，可以尝试减小地图尺寸或减少网格分区。',
  },
  {
    id: 8,
    question: '可以同时分析多个地图吗？',
    answer:
      '目前系统支持单任务分析。您需要完成当前地图的分析后，才能上传和分析下一个地图。您可以在"历史记录"中查看所有已完成的分析任务。',
  },
  {
    id: 9,
    question: '如何备份我的工作？',
    answer:
      '建议定期导出分析结果进行备份。您也可以在系统设置中启用"自动保存"功能，系统会在您工作时自动保存已完成的任务。',
  },
  {
    id: 10,
    question: '遇到问题如何获得帮助？',
    answer:
      '您可以通过以下方式获得帮助：1) 查看本帮助中心；2) 在社区论坛发帖；3) 联系技术支持邮箱；4) 查看在线文档和教程。',
  },
])

// 展开的FAQ
const expandedFAQ = ref<number | null>(null)

// 过滤后的FAQ（根据搜索）
const filteredFAQs = computed(() => {
  if (!searchQuery.value.trim()) {
    return faqs.value
  }

  const query = searchQuery.value.toLowerCase()
  return faqs.value.filter(
    (faq) => faq.question.toLowerCase().includes(query) || faq.answer.toLowerCase().includes(query),
  )
})

// 切换FAQ展开状态
const toggleFAQ = (id: number) => {
  if (expandedFAQ.value === id) {
    expandedFAQ.value = null
  } else {
    expandedFAQ.value = id
  }
}

// 搜索帮助
const searchHelp = () => {
  if (searchQuery.value.trim()) {
    // 如果有搜索结果，展开第一个匹配的FAQ
    if (filteredFAQs.value.length > 0 && filteredFAQs.value[0]) {
      expandedFAQ.value = filteredFAQs.value[0].id
    }

    // 滚动到FAQ部分
    const faqSection = document.querySelector('.help-section:nth-child(2)')
    if (faqSection) {
      faqSection.scrollIntoView({ behavior: 'smooth' })
    }
  }
}
</script>

<style scoped>
.help-page {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 3rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid #e5e7eb;
}

.page-header h1 {
  font-size: 2.5rem;
  color: #1a2980;
  margin-bottom: 0.5rem;
  background: linear-gradient(90deg, #1a2980, #26d0ce);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-header p {
  font-size: 1.2rem;
  color: #6b7280;
}

.help-search {
  max-width: 600px;
  margin: 0 auto 3rem;
  position: relative;
  display: flex;
  gap: 0.5rem;
}

.search-input {
  flex: 1;
  padding: 0.8rem 1.5rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.3s;
  background: white;
}

.search-input:focus {
  outline: none;
  border-color: #4a6cf7;
  box-shadow: 0 0 0 3px rgba(74, 108, 247, 0.1);
}

.search-btn {
  padding: 0.8rem 1.5rem;
  background: linear-gradient(90deg, #1a2980, #26d0ce);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.search-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(26, 41, 128, 0.2);
}

.search-btn svg {
  width: 20px;
  height: 20px;
}

.help-content {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
}

.help-sections {
  display: flex;
  flex-direction: column;
  gap: 3rem;
}

.help-section h2 {
  font-size: 1.8rem;
  color: #1a2980;
  margin-bottom: 1.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #e5e7eb;
}

.section-content {
  padding: 0 0.5rem;
}

.section-content > p {
  color: #4b5563;
  line-height: 1.6;
  margin-bottom: 1.5rem;
  font-size: 1.05rem;
}

/* 快速入门样式 */
.guide-steps {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.guide-step {
  padding: 1.5rem;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  transition: transform 0.3s;
  counter-increment: step;
  position: relative;
  padding-left: 4rem;
}

.guide-step:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
}

.guide-step::before {
  content: counter(step);
  position: absolute;
  left: 1.5rem;
  top: 1.5rem;
  width: 2rem;
  height: 2rem;
  background: linear-gradient(90deg, #1a2980, #26d0ce);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.9rem;
}

.guide-step h3 {
  color: #1a2980;
  margin-bottom: 0.5rem;
  font-size: 1.2rem;
}

.guide-step p {
  color: #4b5563;
  line-height: 1.5;
}

/* 常见问题样式 */
.faq-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.faq-item {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.3s;
}

.faq-item:hover {
  border-color: #1a2980;
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
  font-size: 1rem;
}

.faq-question:hover {
  background: #f3f4f6;
}

.faq-icon {
  font-size: 1.2rem;
  font-weight: bold;
  color: #1a2980;
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
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 500px;
  }
}

/* 故障排除样式 */
.troubleshooting-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.trouble-item {
  padding: 1.5rem;
  background: #fef2f2;
  border-radius: 8px;
  border: 1px solid #fecaca;
  border-left: 4px solid #ef4444;
}

.trouble-item h3 {
  color: #dc2626;
  margin-bottom: 0.8rem;
  font-size: 1.1rem;
}

.trouble-item p {
  color: #4b5563;
  line-height: 1.5;
  margin-bottom: 0.5rem;
}

.trouble-item strong {
  color: #374151;
  font-weight: 600;
}

/* 最佳实践样式 */
.practice-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.practice-item {
  padding: 1.5rem;
  background: #f0f9ff;
  border-radius: 8px;
  border: 1px solid #bae6fd;
  border-left: 4px solid #0ea5e9;
}

.practice-item h3 {
  color: #0369a1;
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.practice-item ul {
  list-style-type: none;
  padding: 0;
  margin: 0;
}

.practice-item li {
  color: #4b5563;
  padding: 0.4rem 0;
  padding-left: 1.5rem;
  position: relative;
  line-height: 1.5;
}

.practice-item li:before {
  content: '✓';
  position: absolute;
  left: 0;
  color: #0ea5e9;
  font-weight: bold;
}

/* 联系我们样式 */
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
  transition:
    transform 0.3s,
    box-shadow 0.3s;
}

.contact-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
}

.contact-item h3 {
  color: #1a2980;
  margin-bottom: 1rem;
  font-size: 1.1rem;
  border-bottom: 2px solid #e5e7eb;
  padding-bottom: 0.5rem;
}

.contact-item p {
  color: #4b5563;
  margin-bottom: 0.5rem;
  line-height: 1.5;
  font-size: 0.95rem;
}

.contact-item strong {
  color: #374151;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .help-page {
    padding: 1rem;
  }

  .page-header h1 {
    font-size: 2rem;
  }

  .guide-step {
    padding: 1rem;
    padding-left: 3.5rem;
  }

  .guide-step::before {
    left: 1rem;
    top: 1rem;
  }
}
</style>
