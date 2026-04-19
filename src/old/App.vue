<template>
  <div id="app">
    <!-- 顶部导航栏 -->
    <header class="app-header">
      <!-- 左侧：Logo 和 系统名称 -->
      <div class="header-left">
        <div class="logo-container">
          <!-- 透明背景的 Logo 图片 -->
          <img src="/pictures/LOGO.png" alt="TerraiNav Logo" class="logo-img" />
        </div>
      </div>

      <!-- 中部：导航链接和搜索框 -->
      <div class="header-center">
        <!-- 导航链接 -->
        <nav class="main-nav">
          <router-link to="/about" class="nav-link">关于</router-link>
          <router-link to="/help" class="nav-link">帮助</router-link>
        </nav>

        <!-- 搜索框 -->
        <div class="search-container">
          <input
            type="text"
            v-model="searchQuery"
            placeholder="搜索功能和帮助..."
            class="search-input"
            @keyup.enter="performSearch"
          />
          <button class="search-btn" @click="performSearch">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
          </button>
        </div>
      </div>

      <!-- 右侧：用户账户状态 -->
      <div class="header-right" v-if="isLoggedIn">
        <div class="user-info">
          <span class="username">欢迎，{{ username }}</span>
          <button class="logout-btn" @click="logout">退出登录</button>
        </div>
      </div>
    </header>

    <main class="app-main">
      <!-- 路由视图区域：LoginView 或 DashboardView 将在这里显示 -->
      <router-view />
    </main>

    <!-- 全局加载状态 -->
    <div v-if="loading" class="global-loading">
      处理中，请稍候...
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('管理员')
const loading = ref(false)
const searchQuery = ref('')

// 计算属性：检查是否已登录（这里简单实现，实际应从Pinia状态中读取）
const isLoggedIn = computed(() => router.currentRoute.value.path !== '/login')

// 退出登录
const logout = () => {
  router.push('/login')
}

// 执行搜索
const performSearch = () => {
  if (searchQuery.value.trim()) {
    alert(`搜索: ${searchQuery.value}`)
    // 这里可以添加实际搜索逻辑
    searchQuery.value = ''
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

/* 顶部导航栏 */
.app-header {
  background: linear-gradient(90deg, #1a2980, #26d0ce);
  color: white;
  padding: 0.8rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  height: 70px;
}

/* 左侧：Logo 和 系统名称 */
.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
  min-width: 200px;
}

.logo-container {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 300px;
  height: 120px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0);
  padding: 6px;
  transition: background 0.3s;
}

.logo-container:hover {
  background: rgba(255, 255, 255, 0.2);
}

.logo-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  filter: brightness(0) invert(1); /* 使Logo变成白色 */
}

.app-name {
  font-size: 1.6rem;
  font-weight: 700;
  color: white;
  letter-spacing: 0.5px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* 中部：导航链接和搜索框 */
.header-center {
  display: flex;
  align-items: center;
  gap: 2rem;
  flex: 1;
  justify-content: center;
  margin: 0 2rem;
}

/* 导航链接 */
.main-nav {
  display: flex;
  gap: 2.5rem;
  align-items: center;
}

.nav-link {
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  font-size: 1.1rem;
  font-weight: 500;
  padding: 0.5rem 0.8rem;
  border-radius: 6px;
  transition: all 0.3s;
  position: relative;
  white-space: nowrap;
}

.nav-link:hover {
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

.nav-link.router-link-active {
  color: white;
  font-weight: 600;
}

.nav-link.router-link-active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0.8rem;
  right: 0.8rem;
  height: 3px;
  background: white;
  border-radius: 2px;
}

/* 搜索框 */
.search-container {
  position: relative;
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 25px;
  padding: 0.3rem 0.5rem;
  transition: background 0.3s;
  min-width: 280px;
  max-width: 400px;
  width: 100%;
}

.search-container:focus-within {
  background: rgba(255, 255, 255, 0.25);
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.3);
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  color: white;
  padding: 0.5rem 0.8rem;
  font-size: 1rem;
  outline: none;
  width: 100%;
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.7);
}

.search-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  color: white;
  margin-left: 0.3rem;
}

.search-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.05);
}

.search-btn svg {
  width: 18px;
  height: 18px;
}

/* 右侧：用户账户状态 */
.header-right {
  min-width: 200px;
  display: flex;
  justify-content: flex-end;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1.2rem;
  background: rgba(255, 255, 255, 0.1);
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  transition: background 0.3s;
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.15);
}

.username {
  font-weight: 500;
  color: white;
  font-size: 1rem;
}

.logout-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 0.9rem;
  padding: 0.4rem 0.8rem;
  white-space: nowrap;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

/* 主要内容区域 */
.app-main {
  padding: 2rem;
  max-width: 1600px;
  margin: 0 auto;
  width: 100%;
  min-height: calc(100vh - 70px);
}

/* 全局加载状态 */
.global-loading {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  color: white;
  font-size: 1.5rem;
  z-index: 9999;
  backdrop-filter: blur(4px);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .app-header {
    padding: 0.8rem 1.5rem;
  }
  
  .header-center {
    margin: 0 1rem;
  }
  
  .main-nav {
    gap: 1.5rem;
  }
  
  .search-container {
    min-width: 200px;
  }
}

@media (max-width: 992px) {
  .app-header {
    flex-wrap: wrap;
    height: auto;
    padding: 0.8rem 1rem;
  }
  
  .header-left {
    min-width: auto;
  }
  
  .app-name {
    font-size: 1.4rem;
  }
  
  .header-center {
    order: 3;
    width: 100%;
    margin: 1rem 0 0 0;
    justify-content: flex-start;
  }
  
  .main-nav {
    gap: 1rem;
  }
  
  .search-container {
    min-width: 250px;
  }
  
  .header-right {
    min-width: auto;
  }
}

@media (max-width: 768px) {
  .app-header {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }
  
  .header-left {
    justify-content: center;
    text-align: center;
  }
  
  .app-name {
    font-size: 1.3rem;
  }
  
  .header-center {
    flex-direction: column;
    gap: 1rem;
    margin: 0;
  }
  
  .main-nav {
    justify-content: center;
  }
  
  .nav-link {
    font-size: 1rem;
    padding: 0.4rem 0.6rem;
  }
  
  .search-container {
    min-width: 100%;
  }
  
  .header-right {
    justify-content: center;
  }
  
  .user-info {
    padding: 0.5rem 1rem;
  }
  
  .app-main {
    padding: 1.5rem 1rem;
  }
}
</style>