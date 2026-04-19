<template>
  <div class="about-page">
    <div class="page-header">
      <h1>关于 TerraiNav</h1>
      <p>地形适应无人机巡逻系统</p>
    </div>
    
    <div class="about-content">
      <div class="about-hero">
        <div class="hero-text">
          <h2>智能无人机巡逻解决方案</h2>
          <p>TerraiNav 是一款先进的地形适应无人机巡逻系统，专为复杂地形环境下的无人机巡逻任务设计。系统结合了人工智能、计算机视觉和路径规划算法，能够智能分析地形威胁度，生成最优巡逻路径。</p>
        </div>
        <div class="hero-image">
          <!-- 这里可以添加系统架构图或演示图 -->
          <div class="placeholder-image">系统架构图</div>
        </div>
      </div>
      
      <div class="tech-section">
        <h2>技术特点</h2>
        <div class="tech-grid">
          <div class="tech-card">
            <div class="tech-icon">🤖</div>
            <h3>先进 AI 算法</h3>
            <p>集成百度千帆大模型，具备强大的地形识别和威胁评估能力。</p>
          </div>
          
          <div class="tech-card">
            <div class="tech-icon">🛣️</div>
            <h3>实时路径优化</h3>
            <p>基于实时威胁数据动态调整巡逻路径，实现自适应飞行控制。</p>
          </div>
          
          <div class="tech-card">
            <div class="tech-icon">📱</div>
            <h3>多终端支持</h3>
            <p>支持 Web 端、移动端访问，提供一致的用户体验和功能。</p>
          </div>
          
          <div class="tech-card">
            <div class="tech-icon">🔒</div>
            <h3>数据安全</h3>
            <p>所有数据处理在本地完成，API 调用通过 HTTPS 加密，保障数据安全。</p>
          </div>
        </div>
      </div>
      
      <div class="features-section">
        <h2>核心功能</h2>
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon">🤖</div>
            <h3>智能威胁度分析</h3>
            <p>基于百度千帆 AI 大模型，自动识别地形特征，评估威胁程度，生成高精度热力图。</p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">🗺️</div>
            <h3>自适应路径规划</h3>
            <p>根据威胁度分析结果，自动规划最优巡逻路径，排查区域内所有高风险点位。</p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">📊</div>
            <h3>多区块任务分配</h3>
            <p>支持将大面积巡逻区域划分为多个区块，实现分区精细化管理。</p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">📕</div>
            <h3>历史任务与管理</h3>
            <p>支持任务进度跟踪和历史数据追溯，便于任务管理和数据分析。</p>
          </div>
        </div>
      </div>
      
      <div class="team-section">
        <h2>开发团队</h2>
        <div class="team-grid">
          <div class="team-member">
            <div class="member-avatar">S</div>
            <h3>SW0rds</h3>
            <p>项目负责人</p>
            <p class="member-desc">项目提出者和前端开发者，负责整体架构设计和技术方案制定。常处于睡不够状态。</p>
          </div>
          
          <div class="team-member">
            <div class="member-avatar">梅</div>
            <h3>哈基梅</h3>
            <p>后端开发者</p>
            <p class="member-desc">古希腊掌管摸鱼的神，优秀的单模块和算法构建者（为什么是单模块好难猜）</p>
          </div>
          
          <div class="team-member">
            <div class="member-avatar">R</div>
            <h3>Relight</h3>
            <p>后端开发者</p>
            <p class="member-desc">一块砖，哪里需要往哪搬。灞桥区伟大的的AI工程师与整体架构调试者。</p>
          </div>
          
          <div class="team-member">
            <div class="member-avatar">陈</div>
            <h3>A11</h3>
            <p>策划与设计</p>
            <p class="member-desc">整体架构的设计参与者，项目的表述输出大师。</p>
          </div>
        </div>
      </div>
      
      <div class="contact-section">
        <h2>联系我们</h2>
        <div class="contact-info">
          <div class="contact-item">
            <h3>技术支持</h3>
            <p>邮箱：13227088780@163.com</p>
          </div>
          
          <div class="contact-item">
            <h3>官方网站</h3>
            <p>https://www.terrainav.com</p>
          </div>
          
          <div class="contact-item">
            <h3>GitHub 仓库</h3>
            <p>https://github.com/terrainav</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 组件逻辑
</script>

<style scoped>
.about-page {
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
  color: #4b5563;
}

.about-hero {
  display: flex;
  align-items: center;
  gap: 3rem;
  margin-bottom: 4rem;
  padding: 2rem;
  background: linear-gradient(135deg, rgba(26, 41, 128, 0.05), rgba(38, 208, 206, 0.05));
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.hero-text {
  flex: 1;
}

.hero-text h2 {
  font-size: 2rem;
  color: #1a2980;
  margin-bottom: 1rem;
}

.hero-text p {
  font-size: 1.1rem;
  color: #e5e7eb;
  line-height: 1.6;
}

.hero-image {
  flex: 0 0 400px;
}

.placeholder-image {
  width: 100%;
  height: 300px;
  background: linear-gradient(90deg, #1a2980, #26d0ce);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.5rem;
  font-weight: 500;
}

.features-section, .tech-section, .team-section, .contact-section {
  margin-bottom: 4rem;
}

.features-section h2, .tech-section h2, .team-section h2, .contact-section h2 {
  font-size: 2rem;
  text-align: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e5e7eb;
  /* 渐变文字效果 */
  background: linear-gradient(90deg, #1a2980, #26d0ce);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
}

/* 技术特点部分 - 2x2网格布局（移除背景效果） */
.tech-section {
  padding: 2rem;
  border-radius: 12px;
  margin-bottom: 4rem;
  background: linear-gradient(135deg, rgba(26, 41, 128, 0.02), rgba(38, 208, 206, 0.02));
  border: 1px solid rgba(26, 41, 128, 0.1);
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 2rem;
  max-width: 1000px;
  margin: 0 auto;
  width: 100%;
}

.tech-card {
  padding: 2rem 1.5rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(26, 41, 128, 0.1);
  transition: transform 0.3s, box-shadow 0.3s;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

.tech-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
  border-color: #1a2980;
}

.tech-icon {
  font-size: 2.8rem;
  margin-bottom: 1.5rem;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: white;
  background: linear-gradient(135deg, #1a2980, #26d0ce);
}

.tech-card:nth-child(1) .tech-icon {
  background: linear-gradient(135deg, #ff7e5f, #feb47b);
}

.tech-card:nth-child(2) .tech-icon {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
}

.tech-card:nth-child(3) .tech-icon {
  background: linear-gradient(135deg, #43e97b, #38f9d7);
}

.tech-card:nth-child(4) .tech-icon {
  background: linear-gradient(135deg, #fa709a, #fee140);
}

.tech-card h3 {
  font-size: 1.3rem;
  color: #1a2980;
  margin-bottom: 1rem;
  font-weight: 600;
}

.tech-card p {
  color: #4b5563;
  line-height: 1.6;
  font-size: 0.95rem;
  margin: 0;
  flex-grow: 1;
}

/* 核心功能部分 - 网格布局 */
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
}

.feature-card {
  padding: 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
  transition: transform 0.3s, box-shadow 0.3s;
  text-align: center;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  font-size: 3rem;
  margin-bottom: 1.5rem;
}

.feature-card h3 {
  font-size: 1.3rem;
  color: #1a2980;
  margin-bottom: 1rem;
}

.feature-card p {
  color: #4b5563;
  line-height: 1.6;
}

.team-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
}

.team-member {
  text-align: center;
  padding: 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
  transition: transform 0.3s;
}

.team-member:hover {
  transform: translateY(-5px);
}

.member-avatar {
  width: 80px;
  height: 80px;
  margin: 0 auto 1.5rem;
  background: linear-gradient(90deg, #1a2980, #26d0ce);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.8rem;
  font-weight: bold;
}

.team-member h3 {
  font-size: 1.3rem;
  color: #1a2980;
  margin-bottom: 0.5rem;
}

.team-member p {
  color: #6b7280;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.member-desc {
  color: #4b5563 !important;
  font-size: 0.9rem !important;
  line-height: 1.5;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.contact-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
}

.contact-item {
  padding: 1.5rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  transition: all 0.3s;
}

.contact-item:hover {
  border-color: #1a2980;
  box-shadow: 0 4px 8px rgba(26, 41, 128, 0.1);
}

.contact-item h3 {
  color: #1a2980;
  margin-bottom: 1rem;
  font-size: 1.2rem;
}

.contact-item p {
  color: #4b5563;
  margin-bottom: 0.5rem;
  line-height: 1.5;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .about-hero {
    flex-direction: column;
  }
  
  .hero-image {
    flex: none;
    width: 100%;
  }
  
  .placeholder-image {
    height: 200px;
  }
  
  .tech-grid {
    grid-template-columns: 1fr;
  }
  
  .features-grid,
  .team-grid,
  .contact-info {
    grid-template-columns: 1fr;
  }
}
</style>