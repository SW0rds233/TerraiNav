<template>
  <div id="app" :class="{ 'app-bg': !isLoginPage }">
    <!-- 顶部导航栏 - 只在非登录页面显示 -->
    <header v-if="!isLoginPage" class="app-header">
      <!-- 左侧：Logo 和 系统名称 -->
      <div class="header-left">
        <div class="logo-container">
          <!-- 透明背景的 Logo 图片 -->
          <img src="/pictures/LOGO.png" alt="TerraiNav Logo" class="logo-img" />
        </div>
      </div>

      <!-- 右侧：导航链接和用户信息 -->
      <div class="header-right">
        <!-- 导航链接 - 现在移到右侧 -->
        <nav class="main-nav">
          <!-- 新增：主界面链接 -->
          <router-link to="/dashboard/map-analysis" class="nav-link">主界面</router-link>
          <router-link to="/about" class="nav-link">关于</router-link>
          <router-link to="/help" class="nav-link">帮助</router-link>
        </nav>

        <!-- 用户账户状态 -->
        <div class="user-info" v-if="isLoggedIn">
          <span class="username">欢迎，{{ userStore.user.name }}</span>
          <button class="logout-btn" @click="logout">退出登录</button>
        </div>
      </div>
    </header>

    <main class="app-main" :class="{ 'login-page': isLoginPage }">
      <!-- 路由视图区域：LoginView 或 DashboardView 将在这里显示 -->
      <router-view />
    </main>

    <!-- 全局加载状态 -->
    <div v-if="loading" class="global-loading">
      处理中，请稍候...
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from './stores/userStore'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const loading = ref(false)

// 计算属性：检查是否在登录页面
const isLoginPage = computed(() => {
  return route.path === '/login'
})

// 计算属性：检查是否已登录
const isLoggedIn = computed(() => {
  return userStore.isAuthenticated
})

// 退出登录
const logout = () => {
  // 调用 userStore 的 logout 方法清除认证状态
  userStore.logout()

  // 在组件中处理路由跳转
  router.push('/login')
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
  /* 默认不设置背景，由动态类控制 */
}

/* 为非登录页面（如仪表板、关于、帮助等）设置背景图片 */
#app.app-bg {
  /* 设置背景图片 */
  background: url("/pictures/background1.jpg") no-repeat center center fixed;
  background-size: cover; /* 使背景图覆盖整个区域 */
  min-height: 100vh; /* 确保至少占满视口高度 */
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
  position: relative;
  z-index: 1000;
}

/* 左侧：Logo 和 系统名称 */
.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 0 0 auto;
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

/* 右侧：导航链接和用户信息 - 修改为右侧对齐 */
.header-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex: 1 1 auto;
  gap: 3rem; /* 增加间距，使元素更分散 */
}

/* 导航链接 - 现在在右侧 */
.main-nav {
  display: flex;
  gap: 2.5rem;
  align-items: center;
  margin-right: 1.5rem; /* 增加右侧边距 */
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

/* 用户账户状态 */
.user-info {
  display: flex;
  align-items: center;
  gap: 1.2rem;
  background: rgba(255, 255, 255, 0.1);
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  transition: background 0.3s;
  flex-shrink: 0; /* 防止在空间不足时缩小 */
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.15);
}

.username {
  font-weight: 500;
  color: white;
  font-size: 1rem;
  white-space: nowrap;
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

/* 登录页面样式 - 确保其不受 .app-bg 影响，使用自己的背景 */
.app-main.login-page {
  padding: 0;
  max-width: 100%;
  margin: 0;
  min-height: 100vh;
  width: 100%;
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

  .main-nav {
    gap: 1.5rem;
  }

  .header-right {
    gap: 2rem;
  }
}

@media (max-width: 992px) {
  .app-header {
    flex-wrap: nowrap;
    height: auto;
    padding: 0.8rem 1rem;
  }

  .logo-container {
    width: 250px;
    height: 100px;
  }

  .header-right {
    gap: 1.5rem;
  }

  .main-nav {
    gap: 1rem;
    margin-right: 1rem;
  }

  .nav-link {
    font-size: 1rem;
    padding: 0.4rem 0.6rem;
  }

  .user-info {
    padding: 0.5rem 1rem;
  }
}

@media (max-width: 768px) {
  .app-header {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
    height: auto;
    padding: 1rem;
  }

  .header-left {
    justify-content: center;
    text-align: center;
  }

  .logo-container {
    width: 200px;
    height: 80px;
  }

  .header-right {
    flex-direction: column;
    gap: 1rem;
    align-items: center;
  }

  .main-nav {
    margin-right: 0;
    gap: 1.5rem;
  }

  .nav-link {
    font-size: 1rem;
    padding: 0.4rem 0.6rem;
  }

  .user-info {
    padding: 0.5rem 1rem;
  }

  .app-main {
    padding: 1.5rem 1rem;
  }

  .app-main.login-page {
    padding: 0;
  }
}

@media (max-width: 480px) {
  .app-header {
    padding: 0.8rem;
  }

  .logo-container {
    width: 180px;
    height: 70px;
  }

  .main-nav {
    flex-direction: column;
    gap: 0.8rem;
  }

  .nav-link {
    font-size: 0.95rem;
  }

  .user-info {
    flex-direction: column;
    gap: 0.8rem;
    text-align: center;
  }
}
</style>
