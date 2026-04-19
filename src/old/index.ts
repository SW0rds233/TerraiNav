import { createRouter, createWebHistory } from 'vue-router'

// 导入视图组件
import LoginView from '../views/LoginView.vue'  // 使用相对路径
import DashboardView from '../views/DashboardView.vue'  // 使用相对路径

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/', 
      redirect: '/login'
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView  // 直接使用导入的组件
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView  // 直接使用导入的组件
    }
  ]
})

export default router