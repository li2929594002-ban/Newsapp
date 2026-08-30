from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from schemas.base import NewsItemBase


class FavoriteCheckResponse(BaseModel):
    is_favorite:bool = Field(..., alias = "isFavorite")


class FavoriteAddRequest(BaseModel):
    news_id:int = Field(..., alias = "newsId")


class FavoriteAddResponse(BaseModel):
    id:int = Field(..., alias = "id")
    user_id:int = Field(..., alias = "userId")
    news_id:int = Field(..., alias = "newsId")
    created_at:datetime = Field(..., alias = "createTime")

    model_config = ConfigDict(
        from_attributes = True,
        populate_by_name = True
    )


# 规划两个类: 一个是新闻模型类 + 收藏的模型类
class FavoriteNewsItemResponse(NewsItemBase):
    favorite_id: int = Field(alias = "favoriteId")
    favorite_time: datetime = Field(alias = "favoriteTime")

    model_config = ConfigDict(
        from_attributes = True,
        populate_by_name = True
    )

# 收藏列表接口响应模型类
class FavoriteListResponse(BaseModel):
    list: list[FavoriteNewsItemResponse]
    total: int
    has_more: bool = Field(alias = "hasMore")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
