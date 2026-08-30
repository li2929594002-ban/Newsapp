from fastapi import FastAPI
from routers import news, users, favorite, history
from fastapi.middleware.cors import CORSMiddleware
from utils.exception_handlers import register_exception_handlers
import os

app = FastAPI()

# 注册异常处理器
register_exception_handlers(app)

# CORS 白名单：默认放行本地开发前端；生产环境通过环境变量 CORS_ORIGINS 配置（逗号分隔）
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins = cors_origins,   # 来源白名单，allow_credentials=True 时不能使用 "*"
    allow_credentials = True,       # 允许携带Cookie
    allow_methods = ["*"],          # 允许的请求方法
    allow_headers = ["*"]           # 允许的请求头
)


# 挂载路由/注册路由
app.include_router(news.router)
app.include_router(users.router)
app.include_router(favorite.router)
app.include_router(history.router)