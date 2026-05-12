<template>
  <div class="login-container">
    <!-- 左上角LOGO - 简化版 -->
    <div class="top-left-logo">
      <img src="/pictures/LOGO1.png" alt="TerraiNav Logo" class="logo-img" />
    </div>

    <div class="container" :class="{ 'right-panel-active': showRegister }">
      <!-- 注册表单 -->
      <div class="container__form container--signup">
        <form class="form" id="form1" @submit.prevent="handleRegister">
          <h2 class="form__title">用户注册</h2>
          <input
            v-model="registerUsername"
            type="text"
            placeholder="用户名"
            class="input"
            required
          />
          <input
            v-model="registerEmail"
            type="email"
            placeholder="邮箱"
            class="input"
            required
          />
          <input
            v-model="registerPassword"
            type="password"
            placeholder="密码"
            class="input"
            required
          />
          <button class="btn" type="submit" :disabled="registering">
            <span v-if="!registering">注册</span>
            <span v-else>注册中...</span>
          </button>
        </form>
      </div>

      <!-- 登录表单 -->
      <div class="container__form container--signin">
        <form class="form" id="form2" @submit.prevent="handleLogin">
          <h2 class="form__title">用户登录</h2>
          <input
            v-model="loginUsername"
            type="text"
            placeholder="用户名"
            class="input"
            required
          />
          <input
            v-model="loginPassword"
            type="password"
            placeholder="密码"
            class="input"
            required
          />
          <a href="#" class="link">忘记密码？</a>
          <button class="btn" type="submit" :disabled="loggingIn">
            <span v-if="!loggingIn">登录</span>
            <span v-else>登录中...</span>
          </button>
        </form>
      </div>

      <!-- 覆盖层 -->
      <div class="container__overlay">
        <div class="overlay">
          <div class="overlay__panel overlay--left">
            <button class="btn" @click="toggleToLogin">已有账户？登录</button>
          </div>
          <div class="overlay__panel overlay--right">
            <button class="btn" @click="toggleToRegister">没有账户？注册</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 左下角版权信息 -->
    <div class="bottom-left-info">
      <div class="copyright-info">
        © 2026 TerraiNav 地形适应无人机巡逻系统设计团队. 版权所有.
      </div>
      <div class="contact-info">
        联系邮箱: 2698889584@qq.com
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'

const router = useRouter()
const userStore = useUserStore()

const loginUsername = ref('')
const loginPassword = ref('')

const registerUsername = ref('')
const registerEmail = ref('')
const registerPassword = ref('')

const showRegister = ref(false)

const loggingIn = ref(false)
const registering = ref(false)

const toggleToLogin = () => {
  showRegister.value = false
}

const toggleToRegister = () => {
  showRegister.value = true
}

const handleLogin = async () => {
  console.log('登录信息:', {
    username: loginUsername.value,
    password: loginPassword.value
  })

  if (loginUsername.value && loginPassword.value) {
    loggingIn.value = true

    try {
      await userStore.login(loginUsername.value, loginPassword.value)

      console.log('登录成功，跳转到仪表板')
      router.push('/dashboard/map-analysis')

    } catch (error) {
      console.error('登录失败:', error)
      const errMsg = (error as Error).message || '请检查用户名和密码'
      alert('登录失败: ' + errMsg)
    } finally {
      loggingIn.value = false
    }
  } else {
    alert('请输入用户名和密码')
  }
}

const handleRegister = async () => {
  console.log('注册信息:', {
    username: registerUsername.value,
    email: registerEmail.value,
    password: registerPassword.value
  })

  if (registerUsername.value && registerEmail.value && registerPassword.value) {
    registering.value = true

    try {
      await userStore.register(
        registerUsername.value,
        registerEmail.value,
        registerPassword.value
      )

      alert('注册成功，请登录')
      showRegister.value = false

      registerUsername.value = ''
      registerEmail.value = ''
      registerPassword.value = ''

    } catch (error) {
      console.error('注册失败:', error)
      const errMsg = (error as Error).message || '请稍后重试'
      alert('注册失败: ' + errMsg)
    } finally {
      registering.value = false
    }
  } else {
    alert('请填写完整的注册信息')
  }
}
</script>

<style>
/* 全局CSS变量 */
:root {
  /* COLORS */
  --white: #e9e9e9;
  --gray: #333;
  --blue: #0367a6;
  --lightblue: #008997;

  /* RADII */
  --button-radius: 0.7rem;

  /* SIZES */
  --max-width: 758px;
  --max-height: 420px;

  font-size: 16px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
    Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
}

/* 登录容器样式 */
.login-container {
  align-items: center;
  background-color: var(--white);
  background: url("/pictures/background1.jpg");
  background-attachment: fixed;
  background-position: center;
  background-repeat: no-repeat;
  background-size: cover;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  width: 100%;
  margin: 0;
  padding: 0;
  position: fixed;
  top: 0;
  left: 0;
  overflow: hidden;
}

/* 左上角LOGO样式 - 简化版，只显示透明LOGO */
.top-left-logo {
  position: absolute;
  top: 0px;
  left: 20px;
  z-index: 1000;
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 0;
  border-radius: 0;
  transition: none;
}

.top-left-logo:hover {
  /* 移除所有悬停效果 */
  background: transparent;
  box-shadow: none;
  transform: none;
}

.logo-img {
  width: 360px;
  height: 200px;
  object-fit: contain;
  background: transparent;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

/* 容器 */
.container {
  background-color: var(--white);
  border-radius: var(--button-radius);
  box-shadow: 0 0.9rem 1.7rem rgba(0, 0, 0, 0.25),
    0 0.7rem 0.7rem rgba(0, 0, 0, 0.22);
  height: var(--max-height);
  max-width: var(--max-width);
  overflow: hidden;
  position: relative;
  width: 100%;
  margin: 0 20px;
}

/* 表单容器 */
.container__form {
  height: 100%;
  position: absolute;
  top: 0;
  transition: all 0.6s ease-in-out;
}

/* 登录表单 */
.container--signin {
  left: 0;
  width: 50%;
  z-index: 2;
}

.container.right-panel-active .container--signin {
  transform: translateX(100%);
}

/* 注册表单 */
.container--signup {
  left: 0;
  opacity: 0;
  width: 50%;
  z-index: 1;
}

.container.right-panel-active .container--signup {
  animation: show 0.6s;
  opacity: 1;
  transform: translateX(100%);
  z-index: 5;
}

/* 覆盖层容器 */
.container__overlay {
  height: 100%;
  left: 50%;
  overflow: hidden;
  position: absolute;
  top: 0;
  transition: transform 0.6s ease-in-out;
  width: 51%;
  z-index: 100;
}

.container.right-panel-active .container__overlay {
  transform: translateX(-100%);
}

/* 覆盖层 */
.overlay {
  background-color: var(--lightblue);
  background: url("/pictures/background1.jpg");
  background-attachment: fixed;
  background-position: center;
  background-repeat: no-repeat;
  background-size: cover;
  height: 100%;
  left: -100%;
  position: relative;
  transform: translateX(0);
  transition: transform 0.6s ease-in-out;
  width: 200%;
}

.container.right-panel-active .overlay {
  transform: translateX(50%);
}

/* 覆盖面板 */
.overlay__panel {
  align-items: center;
  display: flex;
  flex-direction: column;
  height: 100%;
  justify-content: center;
  position: absolute;
  text-align: center;
  top: 0;
  transform: translateX(0);
  transition: transform 0.6s ease-in-out;
  width: 50%;
}

/* 左侧面板 */
.overlay--left {
  transform: translateX(-20%);
}

.container.right-panel-active .overlay--left {
  transform: translateX(0);
}

/* 右侧面板 */
.overlay--right {
  right: 0;
  transform: translateX(0);
}

.container.right-panel-active .overlay--right {
  transform: translateX(20%);
}

/* 表单标题 */
.form__title {
  font-weight: 300;
  margin: 0;
  margin-bottom: 1.25rem;
  color: var(--gray);
}

/* 链接 */
.link {
  color: var(--gray);
  font-size: 0.9rem;
  margin: 1.5rem 0;
  text-decoration: none;
  cursor: pointer;
  transition: color 0.3s;
}

.link:hover {
  color: var(--blue);
  text-decoration: underline;
}

/* 按钮 */
.btn {
  background-color: var(--blue);
  background-image: linear-gradient(90deg, var(--blue) 0%, var(--lightblue) 74%);
  border-radius: 20px;
  border: 1px solid var(--blue);
  color: var(--white);
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: bold;
  letter-spacing: 0.1rem;
  padding: 0.9rem 4rem;
  text-transform: uppercase;
  transition: transform 80ms ease-in;
  outline: none;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn:active:not(:disabled) {
  transform: scale(0.95);
}

.btn:focus {
  outline: none;
}

.btn:hover:not(:disabled) {
  opacity: 0.9;
}

.form > .btn {
  margin-top: 1.5rem;
}

/* 表单 */
.form {
  background-color: var(--white);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  padding: 0 3rem;
  height: 100%;
  text-align: center;
}

/* 输入框 */
.input {
  background-color: #fff;
  border: none;
  padding: 0.9rem 0.9rem;
  margin: 0.5rem 0;
  width: 100%;
  box-sizing: border-box;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  transition: border-color 0.3s;
}

.input:focus {
  outline: none;
  border-color: var(--blue);
  box-shadow: 0 0 5px rgba(3, 103, 166, 0.3);
}

.input::placeholder {
  color: #888;
}

/* 左下角版权信息 */
.bottom-left-info {
  position: absolute;
  left: 20px;
  bottom: 20px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.85rem;
  z-index: 1;
  text-align: left;
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(3px);
  -webkit-backdrop-filter: blur(3px);
  border-radius: 6px;
  padding: 12px 20px;
  max-width: 500px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-left: 3px solid rgba(255, 255, 255, 0.3);
}

.copyright-info {
  font-weight: 500;
  margin-bottom: 4px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.9rem;
}

.contact-info {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.4;
}

/* 悬停效果 */
.bottom-left-info:hover {
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
  border-left: 3px solid rgba(255, 255, 255, 0.5);
  transition: all 0.3s ease;
}

/* 动画 */
@keyframes show {
  0%, 49.99% {
    opacity: 0;
    z-index: 1;
  }

  50%, 100% {
    opacity: 1;
    z-index: 5;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .container {
    max-width: 90%;
  }

  .btn {
    padding: 0.9rem 2rem;
  }

  .form {
    padding: 0 2rem;
  }

  /* 响应式调整LOGO大小 */
  .top-left-logo {
    top: 15px;
    left: 15px;
  }

  .logo-img {
    width: 50px;
    height: 50px;
  }

  .bottom-left-info {
    left: 10px;
    bottom: 10px;
    right: 10px;
    max-width: calc(100% - 20px);
    padding: 10px 15px;
  }

  .copyright-info {
    font-size: 0.8rem;
  }

  .contact-info {
    font-size: 0.75rem;
  }
}

@media (max-width: 480px) {
  .container {
    height: 500px;
  }

  .btn {
    padding: 0.9rem 1.5rem;
  }

  /* 响应式调整LOGO大小 */
  .top-left-logo {
    top: 10px;
    left: 10px;
  }

  .logo-img {
    width: 40px;
    height: 40px;
  }

  .bottom-left-info {
    left: 5px;
    bottom: 5px;
    right: 5px;
    padding: 8px 12px;
  }
}
</style>
