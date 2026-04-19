// src/env.d.ts
/// <reference types="vite/client" />

// 扩展 ImportMeta 接口
interface ImportMeta {
  readonly env: ImportMetaEnv
}