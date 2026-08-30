from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from models.news import Category,News


async def get_categories(db:AsyncSession, skip:int = 0, limit:int = 100):
    stmt = select(Category).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_news_lists(db:AsyncSession,category_id:int,page:int = 1, pageSize:int = 10):

    # 查询的是指定分类下的所有新闻
    skip = (page-1) * pageSize
    list_stmt = select(News).where(News.category_id == category_id).offset(skip).limit(pageSize)
    result = await db.execute(list_stmt)
    news_list = result.scalars().all()

    return news_list


async def get_news_count(db:AsyncSession,category_id:int):
    # 查询的是指定分类下的新闻数量
    total_stmt = select(func.count(News.id)).where(News.category_id == category_id)
    total = await db.scalar(total_stmt)
    return total


async def get_news_detail(db:AsyncSession, news_id:int):
    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def increase_news_views(db:AsyncSession, news_id:int):
    stmt = update(News).where(News.id == news_id).values(views = News.views + 1)
    result = await db.execute(stmt)

    # 更新 -> 检查数据库是否真的命中了数据 -> 命中了返回True
    return result.rowcount > 0


async def get_related_news(db:AsyncSession, news_id:int, category_id:int, limit:int = 5):
    # order_by 排序 -> 浏览量和发布时间
    stmt = (select(News).where(
        News.category_id == category_id,
        News.id != news_id
    ).order_by(
        News.views.desc(),  # 默认是升序，desc表示降序
        News.publish_time.desc()
    ).limit(limit))
    result = await db.execute(stmt)
    # return result.scalars().all()
    related_news = result.scalars().all()
    return [{
        "id": news.id,
        "title": news.title,
        "content": news.content,
        "image": news.image,
        "author": news.author,
        "publishTime": news.publish_time,
        "categoryId": news.category_id,
        "views": news.views
    } for news in related_news]
