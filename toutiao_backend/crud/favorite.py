from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.favorite import Favorite
from models.news import News


# 检查收藏状态:当前用户 是否 收藏了这一条新闻
async def is_news_favorite(
    db: AsyncSession,
    user_id:int,
    news_id:int
):
    query = select(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    result = await db.execute(query)
    # 是否有收藏记录
    return result.scalar_one_or_none() is not None


# 添加收藏
async def add_news_favorite(
    db: AsyncSession,
    user_id:int,
    news_id:int
):

    favorite = Favorite(user_id = user_id, news_id = news_id)
    db.add(favorite)

    await db.flush()
    await db.refresh(favorite)
    return favorite


# 取消收藏
async def remove_news_favorite(
    db:AsyncSession,
    news_id:int,
    user_id:int
):
    stmt = delete(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    result = await db.execute(stmt)
    return result.rowcount > 0


# 获取收藏列表: 获取的是某个用户的收藏列表 +分页功能
async def get_favorite_list(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 10
):

    # 总量 + 收藏的新闻列表
    count_query = select(func.count()).where(Favorite.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()


    # 获取收藏列表 - 联表查询 join() + 收藏时间排序 + 分页
    # select(查询主体模型类, 字段别名).join(联合查询的模型类，联合查询的条件).where().order_by().offset().limit()
    # 别名：Favorite.created_at.label("favorite_time")
    skip = (page - 1) * page_size


    # # 写法1：
    # stmt = (select(News, Favorite.created_at.label("favorite_time"), Favorite.id.label("favorite_id"))
    #         .join(Favorite, Favorite.news_id == News.id)
    #         .where(Favorite.user_id == user_id)
    #         .order_by(Favorite.created_at.desc())
    #         .offset(skip)
    #         .limit(page_size))
    # result = await db.execute(stmt)
    # rows = result.all()
    # return rows, total


    # 写法2：
    stmt = (select(News, Favorite.created_at.label("favorite_time"), Favorite.id.label("favorite_id"))
            .join(Favorite,Favorite.news_id == News.id)
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.created_at.desc())
            .offset(skip)
            .limit(page_size))

    result = await db.execute(stmt)
    # 处理结果：给新闻对象动态挂载 favorite_time 属性
    favorite_list = []

    for news, favorite_time,favorite_id in result.all():
        news.favorite_time = favorite_time
        news.favorite_id = favorite_id
        favorite_list.append(news)
    return favorite_list, total


# 清空收藏列表：当前用户的收藏列表
async def remove_all_favorite(
        db: AsyncSession,
        user_id: int
):
    stmt = delete(Favorite).where(Favorite.user_id == user_id)
    result = await db.execute(stmt)

    # 返回一个删除的数量
    return result.rowcount or 0

