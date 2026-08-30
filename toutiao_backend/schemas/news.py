from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from schemas.base import NewsItemBase


class NewsItem(BaseModel):
    id: int
    publish_time: datetime
    created_at: datetime
    updated_at: datetime
    title: str
    description: str
    content: str
    image: Optional[str] = None
    author: Optional[str] = None
    category_id: int
    views:int

    # 开启ORM模式：支持直接接收SQLAlchemy对象自动转换
    model_config = ConfigDict(from_attributes = True)

class NewsListData(BaseModel):
    list:list[NewsItem]
    total:int
    hasMore:bool

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


