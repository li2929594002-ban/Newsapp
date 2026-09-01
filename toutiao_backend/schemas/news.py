from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from schemas.base import NewsItemBase


class NewsListData(BaseModel):
    # 列表响应使用轻量的 NewsItemBase，不带 content/created_at/updated_at 大字段
    list: list[NewsItemBase]
    total: int
    hasMore: bool

class NewsListResponse(BaseModel):
    code:int = 200
    message:str = "success"
    data:NewsListData


class RelatedNewsResponse(BaseModel):
    """
    相关新闻响应（简化版，只包含必要字段）
    """
    id: int
    title: str
    image: Optional[str] = None
    views: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class NewsDetailResponse(NewsItemBase):
    """
    新闻详情响应（继承自 NewsItemResponse，新增 content 和 related_news）
    """
    content: str  # 新增：新闻内容
    related_news: list[RelatedNewsResponse] = Field(default_factory=list, alias="relatedNews")  # 新增相关新闻：

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )


