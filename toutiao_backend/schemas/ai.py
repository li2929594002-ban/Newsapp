from typing import List
from pydantic import BaseModel, Field


# 对话消息：角色 + 内容
class ChatMessage(BaseModel):
    role:str = Field(..., description="角色：user / assistant")
    content:str = Field(..., description="消息内容")


# AI 问答请求体
class AIChatRequest(BaseModel):
    messages:List[ChatMessage] = Field(..., description="对话消息列表")
