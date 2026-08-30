# 导包
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker,AsyncSession
import os

# 加载项目根目录下的 .env（真实密码不入库，模板见 .env.example；Docker 部署时由 compose 直接注入 DATABASE_URL）
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# 数据库URL（默认值不含密码，密码一律来自环境变量）
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("MYSQL_DATABASE", "news_app")
ASYNC_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+aiomysql://root:{os.getenv('MYSQL_ROOT_PASSWORD', '')}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

# 创建异步引擎
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo = True,       # 可选，输出 SQL 日志
    pool_size = 10,    # 设置连接池中保持的持久连接数
    max_overflow = 20  # 设置连接池允许创建的额外连接数
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind = async_engine,        # 绑定数据库引擎
    class_ = AsyncSession,      # 指定会话类
    expire_on_commit = False    # 提交后会话不过期，不会重新查询数据库
)

# 依赖项，用于获取数据库会话
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session               # 返回数据库会话给路由处理函数
            await session.commit()      # 提交事务
        except Exception:
            await session.rollback()    # 有异常，回滚
            raise