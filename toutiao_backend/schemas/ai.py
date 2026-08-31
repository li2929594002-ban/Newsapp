from typing import List, Literal

from pydantic import BaseModel, Field


# 对话消息：角色 + 内容
# role 限制为 user/assistant：system 提示词由后端统一注入，防止客户端伪造 system 消息注入提示词
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"] = Field(..., description="角色：user / assistant")
    content: str = Field(..., min_length=1, max_length=4000, description="消息内容")


# AI 问答请求体
# 对话轮数限制上限，防止超大上下文透传给模型服务消耗额度
class AIChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., min_length=1, max_length=20, description="对话消息列表")
