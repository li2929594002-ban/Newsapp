from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from crud import favorite
from models.users import User
from schemas.favorite import FavoriteCheckResponse, FavoriteAddRequest, FavoriteAddResponse, FavoriteListResponse, \
    FavoriteNewsItemResponse
from utils.auth import get_current_user
from utils.response import success_response

router = APIRouter(prefix = "/api/favorite", tags = ["favorite"])


@router.get("/check")
async def check_favorite(
        news_id: int = Query(..., alias = "newsId"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    is_favorited = await favorite.is_news_favorite(db, user.id, news_id)
    return success_response(message = "检查收藏状态成功", data = FavoriteCheckResponse(isFavorite = is_favorited))


@router.post("/add")
async def add_favorite(
        data: FavoriteAddRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    new_favorite = await favorite.add_news_favorite(db, user.id, data.news_id)
    return success_response(message = "添加收藏成功", data = FavoriteAddResponse.model_validate(new_favorite))


@router.delete("/remove")
async def remove_favorite(
        news_id: int = Query(..., alias = "newsId"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    result = await favorite.remove_news_favorite(db, news_id, user.id)
    if not result:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "收藏记录不存在")
    return success_response(message = "取消收藏成功")


@router.get("/list")
async def get_favorite_list(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le = 100,alias = "pageSize", description="每页条数"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    # # 写法1：
    # rows, total = await favorite.get_favorite_list(db, user.id, page, page_size)
    # favorite_list = [{
    #     **news.__dict__,
    #     "favorite_time": favorite_time,
    #     "favorite_id": favorite_id
    # } for news, favorite_time, favorite_id in rows]
    # has_more = page * page_size < total
    #
    # data = FavoriteListResponse(list = favorite_list, total = total, hasMore = has_more)
    # return success_response(message = "success", data = data)


    # 写法2：
    favorite_list, total= await favorite.get_favorite_list(db, user.id, page, page_size)

    # ( 跳过的 + 当前列表里面的数量) <  总量
    has_more = page * page_size < total
    favorite_list_data = FavoriteListResponse(list = [FavoriteNewsItemResponse.model_validate(news)
                                    for news in favorite_list], total = total, hasMore = has_more)

    return success_response(message = "success", data = favorite_list_data)


@router.delete("/clear")
async def clear_favorite(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    count = await favorite.remove_all_favorite(db, user.id)
    return success_response(message = f"成功删除{count}条收藏记录")

