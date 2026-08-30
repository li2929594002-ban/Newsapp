from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from cache.news_cache import get_cached_categories, set_cache_categories, get_cache_news_list, set_cache_news_list, \
    get_cached_news_detail, cache_news_detail, get_cached_related_news, cache_related_news
from models.news import Category,News
from schemas.news import NewsItem, NewsDetailResponse, RelatedNewsResponse


async def get_categories(db:AsyncSession, skip:int = 0, limit:int = 100):
    # 先尝试从缓存中获取数据
    cached_categories = await get_cached_categories()
    if cached_categories:
        return cached_categories

    # 没有缓存，则从数据库中获取
    stmt = select(Category).offset(skip).limit(limit)
    result = await db.execute(stmt)
    categories = result.scalars().all()     # ORM 列表

    # 写入缓存
    if categories:
        categories = jsonable_encoder(categories)
        await set_cache_categories(categories)

    # 返回数据
    return categories

async def get_news_list(db:AsyncSession,category_id:int,page:int = 1, page_size:int = 10):
    # 先尝试从缓存中获取新闻列表
    cached_list = await get_cache_news_list(category_id, page, page_size)    # 缓存数据 json
    if cached_list:
        # return cached_list  # 要的是 ORM
        return [News(**item) for item in cached_list]

    # 查询的是指定分类下的所有新闻
    skip = (page-1) * page_size
    list_stmt = select(News).where(News.category_id == category_id).offset(skip).limit(page_size)
    result = await db.execute(list_stmt)
    news_list = result.scalars().all()

    # 写入缓存
    if news_list:
        # 先把 ORM 数据 转换 字典 才能写入缓存
        # ORM 转成 Pydantic，再转为字典
        # by_alias = False 不使用别名，保存Python风格，因为 Redis 数据是给后端用的
        news_data = [NewsItem.model_validate(item).model_dump(mode="json", by_alias = False) for item in news_list]
        await set_cache_news_list(category_id, page, page_size, news_data)

    return news_list


async def get_news_count(db:AsyncSession,category_id:int):
    # 查询的是指定分类下的新闻数量
    total_stmt = select(func.count(News.id)).where(News.category_id == category_id)
    total = await db.scalar(total_stmt)
    return total


async def get_news_detail(db:AsyncSession, news_id:int):
    # 先尝试从缓存中获取新闻详情
    cached_detail = await get_cached_news_detail(news_id)
    if cached_detail:
        # 缓存数据可能包含 related_news，需要过滤掉（News 模型没有这个字段）
        # filtered_detail = {k:v for k,v in cached_detail.items() if k != "related_news"}
        # return News(**filtered_detail)
        return News(**cached_detail)

    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    news = result.scalar_one_or_none()

    # 如果查询到数据，存入缓存（不使用别名，保持数据库字段名）
    if news:
        # 构造新闻详情数据用于缓存（包含 content 字段）
        # news_dict = {k:v for k,v in news.__dict__.items() if not k.startswith("_")}
        news_dict = NewsDetailResponse.model_validate(news).model_dump(
            mode="json", by_alias = False,exclude ={'related_news'})
        await cache_news_detail(news_id, news_dict)
    return news


async def increase_news_views(db:AsyncSession, news_id:int):
    stmt = update(News).where(News.id == news_id).values(views = News.views + 1)
    result = await db.execute(stmt)

    # 更新 -> 检查数据库是否真的命中了数据 -> 命中了返回True
    return result.rowcount > 0


async def get_related_news(db:AsyncSession, news_id:int, category_id:int, limit:int = 5):
    # 先尝试从缓存中获取相关新闻
    cached_related = await get_cached_related_news(news_id, category_id)
    if cached_related:
        # 缓存数据是字典列表，直接返回
        return cached_related

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

    # 写入缓存
    # 转换为字典格式用于缓存和返回（不使用别名，保持数据库字段名）
    if related_news:
        related_data = [RelatedNewsResponse.model_validate(news).model_dump(mode="json", by_alias = False) for news in related_news]
        await cache_related_news(news_id, category_id, related_data)
        return related_data

    # 没有相关新闻，返回空列表
    return []


    # 列表推导式 推导出新闻的核心数据，然后再 return
    # return [{
    #     "id": news.id,
    #     "title": news.title,
    #     "content": news.content,
    #     "image": news.image,
    #     "author": news.author,
    #     "publishTime": news.publish_time,
    #     "categoryId": news.category_id,
    #     "views": news.views
    # } for news in related_news]
