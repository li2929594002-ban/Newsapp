import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from config import ai_conf
from schemas.ai import AIChatRequest

# 创建 APIRouter 实例
router = APIRouter(prefix = "/api/ai", tags = ["ai"])

# 接口实现流程
# 1.前端把对话消息列表 POST 给后端 /api/ai/chat
# 2.后端携带环境变量中的 API Key 请求 DeepSeek（Key 不下发到前端）
# 3.把 DeepSeek 的 SSE 流式响应原样转发给前端


# AI 问答：后端代理转发，隐藏 API Key
@router.post("/chat")
async def ai_chat(chat_data:AIChatRequest):
    # 校验 Key 是否已配置
    if not ai_conf.AI_API_KEY:
        raise HTTPException(status_code=500, detail = "AI服务未配置，请联系管理员")

    # 组装转发给 DeepSeek 的请求体：模型 + 消息列表 + 流式
    payload = {
        "model": ai_conf.AI_MODEL,
        "messages": [message.model_dump() for message in chat_data.messages],
        "stream": True
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ai_conf.AI_API_KEY}"
    }

    # 发起请求：stream=True 只等响应头，响应体保持流式，后续逐块转发
    # （若用 client.post() 会把上游响应整体缓冲完，前端将失去打字机效果）
    client = httpx.AsyncClient(timeout = 60)
    try:
        req = client.build_request("POST", ai_conf.AI_API_URL, json = payload, headers = headers)
        res = await client.send(req, stream = True)
    except httpx.HTTPError:
        await client.aclose()
        raise HTTPException(status_code=502, detail = "AI服务连接失败，请稍后再试")

    # 上游报错（Key无效、余额不足等）→ 关闭连接并透传错误信息
    if res.status_code != 200:
        await res.aread()   # 错误响应体较小，读完整再解析
        try:
            detail = res.json().get("error", {}).get("message", "AI服务暂时不可用")
        except Exception:
            detail = "AI服务暂时不可用"
        await res.aclose()
        await client.aclose()
        raise HTTPException(status_code=502, detail = detail)

    # 逐块转发 SSE 数据给前端，结束后释放连接
    async def stream_generator():
        try:
            async for chunk in res.aiter_bytes():
                yield chunk
        finally:
            await res.aclose()
            await client.aclose()

    return StreamingResponse(stream_generator(), media_type = "text/event-stream")
