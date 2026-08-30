from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from crud import history
from models.users import User
from schemas.history import HistoryAddRequest, HistoryListResponse, HistoryNewsItemResponse
from utils.auth import get_current_user
from utils.response import success_response

router = APIRouter(prefix = "/api/history", tags = ["history"])

# 添加浏览记录
@router.post("/add")
async def add_history(
        data: HistoryAddRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    result = await history.increase_history(news_id = data.news_id, user_id = user.id, db = db)
    return success_response(message = "添加浏览记录成功", data = result)


# 获取浏览记录列表
@router.get("/list")
async def get_history_list(
        page: int = Query(1, ge=1),
        page_size:int = Query(10, ge=1, le =100, alias="pageSize"),
        user:User = Depends(get_current_user),
        db:AsyncSession = Depends(get_db)
):
    history_list, total = await history.get_history_list(db, user.id, page, page_size)

    # ( 跳过的 + 当前列表里面的数量) <  总量
    has_more = page * page_size < total
    data = HistoryListResponse(list = [HistoryNewsItemResponse.model_validate(news) for news in history_list], total = total, hasMore = has_more)
    return success_response(message = "获取浏览记录列表成功", data = data)


# 删除单条浏览记录
@router.delete("/delete/{history_id}")
async def delete_history(
        history_id:int,
        user:User = Depends(get_current_user),
        db:AsyncSession = Depends(get_db)
):
    result = await history.remove_history(db, history_id, user.id)
    if not result:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "浏览记录不存在")
    return success_response(message = "删除成功")


# 清空浏览历史
@router.delete("/clear")
async def clear_history(
        user:User = Depends(get_current_user),
        db:AsyncSession = Depends(get_db)
):
    count = await history.remove_all_history(db, user.id)
    return success_response(message = f"成功删除{count}条历史记录")
