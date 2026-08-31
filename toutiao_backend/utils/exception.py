import os
import traceback
from pathlib import Path

from dotenv import load_dotenv
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette import status

# 加载项目根目录下的 .env（与 db_conf 保持一致，模块自包含）
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# 调试开关：开启时错误响应附带 traceback 等内部信息，仅限本地开发使用
# 默认关闭，生产环境必须保持关闭，防止内部实现细节泄露给客户端
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    处理 HTTPException 异常
    """
    # HTTPException 通常是业务逻辑主动抛出的，data 保持 None
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None
        }
    )


# 唯一约束名 → 用户提示 映射表：新增表/约束时在此登记即可
# MySQL 报错格式：Duplicate entry 'xxx' for key '库名.表名.约束名'，用约束名做子串匹配
UNIQUE_CONSTRAINT_MESSAGES = {
    "username_UNIQUE": "用户名已存在",
    "phone_UNIQUE": "该手机号已被绑定",
    "token_UNIQUE": "令牌冲突，请重试",
    "user_news_unique": "该新闻已收藏，请勿重复操作",
}


async def integrity_error_handler(request: Request, exc: IntegrityError):
    """
    处理数据库完整性约束错误
    """
    error_msg = str(exc.orig)

    # 优先按唯一约束名精确映射，避免把手机号/收藏等冲突误判为"用户名已存在"
    detail = None
    for constraint_name, message in UNIQUE_CONSTRAINT_MESSAGES.items():
        if constraint_name in error_msg:
            detail = message
            break

    # 未登记的约束走兜底分支
    if detail is None:
        if "FOREIGN KEY" in error_msg:
            detail = "关联数据不存在"
        elif "Duplicate entry" in error_msg:
            detail = "数据已存在，请勿重复提交"
        else:
            detail = "数据约束冲突，请检查输入"

    # 开发模式下返回详细错误信息
    error_data = None
    if DEBUG_MODE:
        error_data = {
            "error_type": "IntegrityError",
            "error_detail": error_msg,
            "path": str(request.url)
        }

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "code": 400,
            "message": detail,
            "data": error_data
        }
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """
    处理 SQLAlchemy 数据库错误
    """
    # 开发模式下返回详细错误信息
    error_data = None
    if DEBUG_MODE:
        error_data = {
            "error_type": type(exc).__name__,
            "error_detail": str(exc),
            # 格式化异常信息为字符串，方便日志记录和调试
            "traceback": traceback.format_exc(),
            "path": str(request.url)
        }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "数据库操作失败，请稍后重试",
            "data": error_data
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    处理所有未捕获的异常
    """
    # 开发模式下返回详细错误信息
    error_data = None
    if DEBUG_MODE:
        error_data = {
            "error_type": type(exc).__name__,
            "error_detail": str(exc),
            # 格式化异常信息为字符串，方便日志记录和调试
            "traceback": traceback.format_exc(),
            "path": str(request.url)
        }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": error_data
        }
    )


