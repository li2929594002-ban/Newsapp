# AI 问答接口限流：Redis 固定窗口算法
# 每用户每窗口内限制调用次数，防止登录态刷量消耗 AI 服务额度
from fastapi import Depends, HTTPException
from fastapi import status

from config import cache_conf, ai_conf
from models.users import User
from utils.auth import get_current_user


async def ai_rate_limit(user: User = Depends(get_current_user)):
    """
    AI 问答接口限流依赖：按 user_id 维度固定窗口限流
    超限返回 429 Too Many Requests，带 Retry-After 告诉客户端等待秒数
    """
    key = f"ai_limit:{user.id}"

    # 原子递增：key 不存在时 INCR 返回 1
    count = await cache_conf.redis_client.incr(key)

    if count == 1:
        # 第一次调用，设置窗口过期时间
        await cache_conf.redis_client.expire(key, ai_conf.AI_RATE_WINDOW)

    if count > ai_conf.AI_RATE_LIMIT:
        # 超限：查剩余 TTL，返回给客户端
        ttl = await cache_conf.redis_client.ttl(key)
        # ttl 可能是 -1（无过期）或 -2（key 不存在），兜底用窗口值
        if ttl < 0:
            ttl = ai_conf.AI_RATE_WINDOW
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"AI 问答调用过于频繁，请 {ttl} 秒后再试",
            headers={"Retry-After": str(ttl)}
        )

    return None
