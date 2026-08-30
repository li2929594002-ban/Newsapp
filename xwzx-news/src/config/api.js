/**
 * API配置文件
 * 包含API基础URL
 * AI问答的API Key已移至后端环境变量，前端通过 /api/ai/chat 代理访问
 */

// API基础URL配置
export const apiConfig = {
  // 后端API基础URL
  baseURL: import.meta.env.DEV ? 'http://127.0.0.1:8000' : '',
}
