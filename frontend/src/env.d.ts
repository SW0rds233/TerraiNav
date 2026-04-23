// src/env.d.ts
/// <reference types="vite/client" />

// Vue 单文件组件模块声明
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// 扩展 ImportMetaEnv 接口
interface ImportMetaEnv {
  readonly VITE_APP_VERSION: string
  readonly VITE_APP_TITLE: string
  readonly VITE_API_URL: string
  readonly MODE: string
  readonly DEV: boolean
  readonly PROD: boolean
  readonly SSR: boolean
  
  // 兼容旧的 Vue CLI 环境变量
  readonly NODE_ENV?: string
  readonly VUE_APP_VERSION?: string
}

// 扩展 ImportMeta 接口
interface ImportMeta {
  readonly env: ImportMetaEnv
}

// 声明 CSS 模块
declare module '*.module.css' {
  const classes: { [key: string]: string }
  export default classes
}

declare module '*.module.scss' {
  const classes: { [key: string]: string }
  export default classes
}

declare module '*.module.sass' {
  const classes: { [key: string]: string }
  export default classes
}

declare module '*.module.less' {
  const classes: { [key: string]: string }
  export default classes
}

// 声明 CSS 文件
declare module '*.css' {
  const css: any
  export default css
}

declare module '*.scss' {
  const scss: any
  export default scss
}

declare module '*.sass' {
  const sass: any
  export default sass
}

declare module '*.less' {
  const less: any
  export default less
}

// 声明图片和字体文件
declare module '*.png' {
  const src: string
  export default src
}

declare module '*.jpg' {
  const src: string
  export default src
}

declare module '*.jpeg' {
  const src: string
  export default src
}

declare module '*.gif' {
  const src: string
  export default src
}

declare module '*.svg' {
  const src: string
  export default src
  export const ReactComponent: any
}

declare module '*.ico' {
  const src: string
  export default src
}

declare module '*.webp' {
  const src: string
  export default src
}

declare module '*.avif' {
  const src: string
  export default src
}

declare module '*.woff' {
  const src: string
  export default src
}

declare module '*.woff2' {
  const src: string
  export default src
}

declare module '*.eot' {
  const src: string
  export default src
}

declare module '*.ttf' {
  const src: string
  export default src
}

declare module '*.otf' {
  const src: string
  export default src
}