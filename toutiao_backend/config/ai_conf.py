# AI 问答相关配置：API 地址、密钥、模型
# 密钥只保存在后端环境变量（.env / compose 注入），不经过前端代码
import os

# DeepSeek 接口地址
AI_API_URL = os.getenv("AI_API_URL", "https://api.deepseek.com/v1/chat/completions")

# API 密钥
AI_API_KEY = os.getenv("AI_API_KEY", "")

# 使用的模型
AI_MODEL = os.getenv("AI_MODEL", "deepseek-chat")
