/**
 * API配置文件
 * 包含API基础URL和AI问答功能所需的API参数
 */

// API基础URL配置
export const apiConfig = {
  // 后端API基础URL
  baseURL: import.meta.env.DEV ? 'http://127.0.0.1:8000' : '',
}

export const aiChatConfig = {
  // OpenAI API地址
  apiEndpoint: 'https://api.deepseek.com/v1/chat/completions',
  
  // API Key (由开发人员指定)
  apiKey: 'sk-X03NslR0Jj8BlDOYCdD86a97834d46E0A66204DcB1A9848d',
  
  // 使用的模型
  model: 'deepseek-v4-flash'
}
