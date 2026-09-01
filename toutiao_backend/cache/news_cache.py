# 新闻相关的缓存方法：新闻分类的读取和写入
# key - value
from typing import List, Dict, Any, Optional

from config.cache_conf import get_json_cache, set_cache

CATEGORIES_KEY = "news:categories"
NEWS_LIST_PREFIX = "news_list:"
NEWS_DETAIL_PREFIX = "news_detail:"
RELATED_NEWS_PREFIX = "related_news:"


# 获取新闻分类缓存
async def get_cached_categories():
    return await get_json_cache(CATEGORIES_KEY)


# 写入新闻分类缓存：缓存的数据，过期时间
# 分类: 7200; 列表: 1800; 详情: 300; 相关新闻: 1800     -- 数据越稳定，缓存越持久
# 避免所有的 key 同时过期，引起缓存雪崩
async def set_cache_categories(data: List[Dict[str, Any]], expire:int = 7200):
    return await set_cache(CATEGORIES_KEY, data, expire)


# 写入缓存 — 新闻列表   key = news_list:分类id:页码:每页数量
# value 同时包含 list 和 total：一次 Redis GET 搞定，避免 total 单独查库
async def set_cache_news_list(category_id:Optional[int], page:int, size:int, news_list:List[Dict[str, Any]], total:int, expire:int = 1800):
    # 调用封装的 Redis 的设置方法，存新闻列表到缓存
    category_part = category_id if category_id is not None else "all"
    key = f"{NEWS_LIST_PREFIX}{category_part}:{page}:{size}"
    # 包装 list 和 total 为一个 dict，保证 TTL 同步、一次 GET 拿到全部
    payload = {"list": news_list, "total": total}
    return await set_cache(key, payload, expire)


# 读取缓存 — 新闻列表
# 返回 {"list": [...], "total": N}，未命中返回 None
async def get_cache_news_list(category_id:Optional[int], page:int, size:int):
    category_part = category_id if category_id is not None else "all"
    key = f"{NEWS_LIST_PREFIX}{category_part}:{page}:{size}"
    return await get_json_cache(key)


# 写入缓存 — 新闻详情
async def cache_news_detail(news_id:int, news_detail:Dict[str, Any], expire:int = 300):
    key = f"{NEWS_DETAIL_PREFIX}{news_id}"
    return await set_cache(key, news_detail, expire)


# 读取缓存 — 新闻详情
async def get_cached_news_detail(news_id:int):
    key = f"{NEWS_DETAIL_PREFIX}{news_id}"
    return await get_json_cache(key)


# 写入缓存 - 相关新闻
async def cache_related_news(news_id:int, category_id:int, related_list:List[Dict[str, Any]], expire:int = 1800):
    key = f"{RELATED_NEWS_PREFIX}{news_id}:{category_id}"
    return await set_cache(key, related_list, expire)


# 读取缓存 - 相关新闻
async def get_cached_related_news(news_id:int, category_id:int):
    key = f"{RELATED_NEWS_PREFIX}{news_id}:{category_id}"
    return await get_json_cache(key)