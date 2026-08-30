from datetime import datetime
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models.history import History
from models.news import News


# 添加浏览记录
async def increase_history(
        news_id: int,
        user_id: int,
        db:AsyncSession
):
    query = select(History).where(History.user_id == user_id, History.news_id == news_id)
    result = await db.execute(query)
    existing_history = result.scalar_one_or_none()
    if existing_history:
        existing_history.view_time = datetime.now()
        await db.flush()
        await db.refresh(existing_history)
        return existing_history

    else:
        history = History(user_id = user_id, news_id = news_id)
        db.add(history)
        await db.flush()
        await db.refresh(history)
        return history


# 获取浏览记录列表
async def get_history_list(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 10
):
    # 总量 + 浏览记录列表

    count_query = select(func.count()).where(History.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    skip = (page - 1) * page_size
    stmt = (select(News, History.view_time.label("viewTime"), History.id.label("historyId"))
            .join(History, History.news_id == News.id)
            .where(History.user_id == user_id)
            .order_by(History.view_time.desc())
            .offset(skip)
            .limit(page_size)
            )

    result = await db.execute(stmt)
    history_list = []
    for news, view_time, history_id in result.all():
        news.view_time = view_time
        news.history_id = history_id
        history_list.append(news)

    return history_list, total


# 删除单条浏览记录
async def remove_history(db:AsyncSession, history_id:int, user_id:int):
    stmt = delete(History).where(History.user_id == user_id, History.id == history_id)
    result = await db.execute(stmt)
    return result.rowcount > 0


# 清空浏览历史
async def remove_all_history(db:AsyncSession, user_id:int):
    stmt = delete(History).where(History.user_id == user_id)
    result = await db.execute(stmt)

    # 返回一个删除的数量
    return result.rowcount or 0
