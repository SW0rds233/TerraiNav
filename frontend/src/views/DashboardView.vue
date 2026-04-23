<template>
  <div class="dashboard-layout">
    <!-- 侧边栏导航 -->
    <aside class="dashboard-sidebar">
      <div class="sidebar-logo">
        <span class="app-name">TerraiNav</span>
        <span class="app-subtitle">地图适应无人机巡逻系统</span>
      </div>
      
      <nav class="sidebar-nav">
        <router-link 
          to="/dashboard/map-analysis" 
          class="nav-item"
          :class="{ active: $route.name === 'map-analysis' }"
        >
          <svg class="nav-icon" viewBox="0 0 24 24">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
          </svg>
          <span>地图分析</span>
        </router-link>
        
        <router-link 
          to="/dashboard/history" 
          class="nav-item"
          :class="{ active: $route.name === 'history' }"
        >
          <svg class="nav-icon" viewBox="0 0 24 24">
            <path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/>
          </svg>
          <span>历史记录</span>
        </router-link>
        
        <router-link 
          to="/dashboard/settings" 
          class="nav-item"
          :class="{ active: $route.name === 'settings' }"
        >
          <svg class="nav-icon" viewBox="0 0 24 24">
            <path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/>
          </svg>
          <span>系统设置</span>
        </router-link>
        
        <router-link 
          to="/dashboard/tutorial" 
          class="nav-item"
          :class="{ active: $route.name === 'tutorial' }"
        >
          <svg class="nav-icon" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
          </svg>
          <span>使用教程</span>
        </router-link>
      </nav>
      
      <div class="sidebar-footer">
        <div class="user-info">
          <span class="username">{{ userStore.user.name }}</span>
        </div>
      </div>
    </aside>
    
    <!-- 主要内容区域 -->
    <main class="dashboard-main">
      <div class="main-header">
        <h1>{{ currentTitle }}</h1>
        <!-- 已删除"帮助"和"退出"按钮 -->
      </div>
      
      <div class="main-content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 计算当前页面标题
const currentTitle = computed(() => {
  return route.meta?.title || 'TerraiNav'
})

// 退出登录功能已删除
</script>

<style scoped>
.dashboard-layout {
  display: flex;
  min-height: calc(100vh - 70px);
  background: #f8fafc;
}

/* 侧边栏样式 */
.dashboard-sidebar {
  width: 240px;
  background: white;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  padding: 1.5rem 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  z-index: 10;
}

.sidebar-logo {
  padding: 0 1.5rem 2rem;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 1.5rem;
  text-align: center; /* 居中对齐 */
}

.app-name {
  font-size: 2.0rem;
  font-weight: 600;
  color: #1a2980;
  background: linear-gradient(90deg, #1a2980, #26d0ce);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  display: block; /* 块级元素，换行显示 */
  margin-bottom: 5px; /* 增加下边距 */
  letter-spacing: 1px; /* 增加字间距 */
}

.app-subtitle {
  font-size: 0.9rem;
  color: #6b7280;
  display: block; 
  line-height: 1.4; 
  font-weight: 400; 
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0 0.5rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 0.8rem 1rem;
  color: #6b7280;
  text-decoration: none;
  border-radius: 8px;
  transition: all 0.3s;
  position: relative;
}

.nav-item:hover {
  background: #f3f4f6;
  color: #1a2980;
}

.nav-item.active {
  background: linear-gradient(90deg, rgba(26, 41, 128, 0.1), rgba(38, 208, 206, 0.1));
  color: #1a2980;
  font-weight: 500;
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, #1a2980, #26d0ce);
  border-radius: 0 4px 4px 0;
}

.nav-icon {
  width: 20px;
  height: 20px;
  fill: currentColor;
}

.sidebar-footer {
  padding: 1rem 1.5rem 0;
  border-top: 1px solid #e5e7eb;
  margin-top: 1.5rem;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 0.5rem;
  border-radius: 8px;
  background: #f9fafb;
}

.username {
  font-weight: 500;
  color: #4b5563;
  font-size: 0.9rem;
}

/* 主要内容区域 */
.dashboard-main {
  flex: 1;
  padding: 1.5rem;
  overflow: auto;
  background: #f8fafc;
}

.main-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.main-header h1 {
  font-size: 1.8rem;
  color: #1a2980;
  font-weight: 600;
  margin: 0;
  width: 100%; /* 标题占满整个宽度 */
  text-align: center; /* 标题居中 */
}

/* 删除header-actions相关样式 */
/* .header-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  background: #f3f4f6;
  color: #6b7280;
  border: 1px solid #d1d5db;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
  text-decoration: none;
}

.action-btn:hover {
  background: #e5e7eb;
  color: #374151;
} */

.main-content {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
  min-height: calc(100vh - 180px);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .dashboard-sidebar {
    width: 200px;
  }
}

@media (max-width: 768px) {
  .dashboard-layout {
    flex-direction: column;
  }
  
  .dashboard-sidebar {
    width: 100%;
    flex-direction: row;
    padding: 0.5rem;
    border-right: none;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .sidebar-logo {
    padding: 0.5rem;
    border-bottom: none;
    margin-bottom: 0;
    text-align: left; /* 左对齐 */
  }
  
  .app-name {
    font-size: 1.2rem;
  }
  
  .app-subtitle {
    display: none; /* 在小屏幕上隐藏副标题 */
  }
  
  .sidebar-nav {
    flex-direction: row;
    flex: 1;
    justify-content: center;
    gap: 0.5rem;
  }
  
  .nav-item {
    padding: 0.5rem;
  }
  
  .nav-item span {
    display: none;
  }
  
  .sidebar-footer {
    display: none;
  }
}
</style>