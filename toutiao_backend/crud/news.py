from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from models.news import News


async def get_news_count(db:AsyncSession,category_id:int):
    # 查询的是指定分类下的新闻数量
    total_stmt = select(func.count(News.id)).where(News.category_id == category_id)
    total = await db.scalar(total_stmt)
    return total


async def increase_news_views(db:AsyncSession, news_id:int):
    stmt = update(News).where(News.id == news_id).values(views = News.views + 1)
    result = await db.execute(stmt)

    # 更新 -> 检查数据库是否真的命中了数据 -> 命中了返回True
    return result.rowcount > 0
