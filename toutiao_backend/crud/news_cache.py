from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from cache.news_cache import get_cached_categories, set_cache_categories, get_cache_news_list, set_cache_news_list, \
    get_cached_news_detail, cache_news_detail, get_cached_related_news, cache_related_news
from models.news import Category,News
from schemas.news import NewsDetailResponse, RelatedNewsResponse
from schemas.base import NewsItemBase


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
    # 先尝试从缓存中获取新闻列表 + total（一次 Redis GET 搞定）
    cached = await get_cache_news_list(category_id, page, page_size)
    if cached:
        # 缓存命中：直接返回 {"list": [...], "total": N}
        return cached

    # 查询的是指定分类下的所有新闻
    skip = (page-1) * page_size
    list_stmt = select(News).where(News.category_id == category_id).offset(skip).limit(page_size)
    result = await db.execute(list_stmt)
    news_list = result.scalars().all()

    # 计算总量（缓存未命中时才查一次库）
    total_stmt = select(func.count(News.id)).where(News.category_id == category_id)
    total = await db.scalar(total_stmt)

    # 写入缓存：list + total 一起存，保证 TTL 同步
    if news_list:
        # ORM 转成轻量 NewsItemBase（不带 content）再转字典：列表不需要全文，省带宽和 Redis 内存
        news_data = [NewsItemBase.model_validate(item).model_dump(mode="json", by_alias = False) for item in news_list]
        await set_cache_news_list(category_id, page, page_size, news_data, total)
    else:
        news_data = []

    return {"list": news_data, "total": total}


async def get_news_detail(db:AsyncSession, news_id:int):
    # 先尝试从缓存中获取新闻详情
    cached_detail = await get_cached_news_detail(news_id)
    if cached_detail:
        # 直接返回 dict，省去无谓的 News() 反序列化（ORM 对象 detached 后无实际用途）
        return cached_detail

    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    news = result.scalar_one_or_none()

    # 如果查询到数据，统一转为 dict 并写入缓存
    if news:
        # 构造新闻详情数据用于缓存（包含 content 字段）
        detail_dict = NewsDetailResponse.model_validate(news).model_dump(
            mode="json", by_alias = False,exclude ={'related_news'})
        await cache_news_detail(news_id, detail_dict)
        return detail_dict

    return None


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
    related_news = result.scalars().all()

    # 写入缓存
    # 转换为字典格式用于缓存和返回（不使用别名，保持数据库字段名）
    if related_news:
        related_data = [RelatedNewsResponse.model_validate(news).model_dump(mode="json", by_alias = False) for news in related_news]
        await cache_related_news(news_id, category_id, related_data)
        return related_data

    # 没有相关新闻，返回空列表
    return []
