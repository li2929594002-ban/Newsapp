# NewsApp · 新闻资讯 + AI 问答全栈应用

一套基于 Vue3 + FastAPI + MySQL + Redis 的前后端分离新闻资讯应用，内置新闻分类浏览、收藏/历史、用户体系与凭证化鉴权，并接入大模型实现 AI 智能问答（SSE 流式输出，打字机效果）。Docker Compose 可一键完整启动。

---

## 技术栈

### 前端
| 分类 | 选型 |
|---|---|
| 框架 | Vue 3 (`<script setup>` Composition API) |
| 构建工具 | Vite 7 |
| 路由 | Vue Router 4 |
| 状态管理 | Pinia 3 + `pinia-plugin-persistedstate` 持久化 |
| UI 组件库 | Vant 4（移动端友好） |
| HTTP 客户端 | Axios |
| Markdown 渲染 | marked + DOMPurify（AI 问答富文本安全渲染） |
| 国际化 | Vue I18n 9（zh-CN / en-US） |

### 后端
| 分类 | 选型 |
|---|---|
| Web 框架 | FastAPI 0.139（全异步） + Uvicorn 0.20 |
| 数据库 ORM | SQLAlchemy 2.0（`AsyncSession` / asyncio 风格） + aiomysql 异步驱动 |
| 参数校验/响应序列化 | Pydantic v2（全中文 Field description、length/enum 严格校验） |
| 密码哈希 | bcrypt + passlib |
| 认证 | 自研 Token + `Authorization: Bearer <token>`（RFC 6750，大小写不敏感） |
| 配置加载 | python-dotenv + 环境变量（敏感信息一律仅由后端读取） |
| AI 流式问答 | httpx.AsyncClient 转发 DeepSeek `/v1/chat/completions` + FastAPI `StreamingResponse`（SSE） |
| 限流 | Redis `INCR + EXPIRE` 固定窗口每用户限流（默认 5 次 / 60s，超限 429 带 `Retry-After`） |

### 中间件 / 基础设施
| 组件 | 版本 | 用途 |
|---|---|---|
| MySQL | 8.0 | 持久化存储（用户、令牌、新闻、分类、收藏、历史） |
| Redis | 7 Alpine | 分级缓存（分类 7200s / 列表 1800s / 详情 300s / 相关新闻 1800s） + AI 限流计数 |
| Nginx | Alpine | 前端静态资源托管 + `/api/` 反代后端 + `/api/ai/` `proxy_buffering off` 保证 SSE 流式 |

---

## 核心功能

1. **用户体系（鉴权）**
   - 注册/登录/登出、个人资料维护（昵称/头像/性别/简介/手机号，Pydantic 字段级约束）
   - Bearer Token 登录态；修改密码后 Token 自动轮换（旧令牌立即失效），新 Token 返回给前端继续使用
   - 全局 `IntegrityError` 异常处理器：按唯一约束名（用户名/手机号/Token/重复收藏）返回不同的中文业务语义 `detail`，杜绝"操作失败 500"

2. **新闻浏览**
   - 首页信息流（分页 page/page_size，最小 1 页，每页 1-100）
   - 按分类浏览 + 分类列表接口（skip/limit 分页范围校验）
   - 新闻详情：浏览量 UPDATE 后立即 SELECT 最新值返回，避免显示滞后
   - 相关新闻推荐

3. **收藏 / 历史记录**
   - 详情页一键收藏/取消收藏；写库前预检查避免重复，返回"该新闻已收藏"
   - 浏览详情自动写入阅读历史（可按用户分页查询 / 删除）
   - 列表响应统一使用轻量 `NewsItemBase` Schema（剔除 content / created_at / updated_at 大字段减少带宽和缓存体积）

4. **Redis 分级缓存**
   - 分类：TTL 7200s
   - 列表：TTL 1800s，缓存值结构 `{"list":[…], "total": N}`（一次 Redis GET 替代以前"list + count"两次请求）；对历史纯 list 格式缓存具备透明兼容与格式升级
   - 详情：TTL 300s
   - 相关新闻：TTL 1800s
   - CRUD 层统一返回 `dict`（不做无意义的 SQLAlchemy ORM 反序列化），减少 Pydantic/序列化开销

5. **AI 智能问答**
   - 后端代理端点 `/api/ai/chat`，必须登录（`Depends(get_current_user)`）才能调用；API Key 仅后端持有，前端零接触
   - 请求参数严格校验：`messages` 长度 1-20 条，`role ∈ {user, assistant}`，`content` 长度 1-4000
   - SSE 流式转发：Nginx `/api/ai/` 显式关闭 `proxy_buffering`，保证前端打字机效果
   - Redis 固定窗口按用户限流（默认 5 次/60s），超限返回 HTTP 429 与 `Retry-After` 头，防止额度被刷

6. **工程化 & 安全基线**
   - CORS：白名单 + `allow_credentials=True`（**永远不使用 `*`**），生产通过 `CORS_ORIGINS` 环境变量配置
   - DEBUG：由 `DEBUG` 环境变量控制，默认 off；`DEBUG=false` 时屏蔽 docs/redoc/openapi、SQL echo 以及 traceback 泄露
   - `compose.yaml` backend 注入 `DATABASE_URL`/`REDIS_HOST`/`AI_API_KEY`/`AI_MODEL`/`DEBUG`，不写死密码
   - `.env` 被 `.gitignore` 严格忽略，新用户通过 `.env.example` 拷贝配置

---

## 本地启动步骤（开发模式，前后端分离独立运行）

> 本地开发需要本机已安装 Python 3.11+、Node.js 20+、MySQL 8.0、Redis 7。如果你更想一键跑起来，建议直接看下面的 [Docker Compose 一键启动](#docker-compose-一键启动方式)章节。

### 1. 初始化数据库
```bash
# 在本机 MySQL 执行根目录下的初始化 SQL
mysql -uroot -p < database.sql
```
脚本会自动创建 `news_app` 数据库，建好 `user / user_token / news / category / favorite / history` 六张表并填充新闻种子数据。

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env，至少填入：
#   MYSQL_ROOT_PASSWORD=你的MySQL root密码
#   MYSQL_DATABASE=news_app
#   AI_API_KEY=sk-xxxxxxxxxxxxxxxx （向 DeepSeek 控制台申请）
#   DEBUG=true  （本地开发可以开，生产务必 false）
```
> 后端通过项目根目录下 `.env` 加载；另外也支持单独设置 `DB_HOST / DB_PORT / REDIS_HOST / REDIS_PORT / AI_RATE_LIMIT / AI_RATE_WINDOW / CORS_ORIGINS` 等覆盖默认值。

### 3. 启动后端（终端 1）
```bash
cd toutiao_backend
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS / Linux
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
启动成功后可在浏览器验证健康检查：<http://127.0.0.1:8000/health/ready>

### 4. 启动前端（终端 2）
```bash
cd xwzx-news
npm install
npm run dev
```
Vite 默认运行在 <http://127.0.0.1:5173/>，已被后端 CORS 默认白名单放行。

---

## Docker Compose 一键启动方式

```bash
# 1. 生成环境变量文件（首次运行必须）
cp .env.example .env
# 然后编辑 .env，至少填好 MYSQL_ROOT_PASSWORD 与 AI_API_KEY

# 2. 构建镜像并启动四个服务（MySQL / Redis / Backend / Nginx+前端）
docker compose up -d --build

# 3. 第一次启动需要初始化数据库（容器都起来后执行一次即可）
docker compose exec -T mysql \
  sh -c "exec mysql -uroot -p\"\$MYSQL_ROOT_PASSWORD\"" < database.sql

# 4. 查看各容器健康状态
docker compose ps

# 5. 停止与数据清理
docker compose down               # 保留 MySQL 卷
docker compose down -v            # 连 MySQL 数据卷一起清（⚠️ 重置数据库）
```

### 容器端口映射

| 服务 | 容器内端口 | 宿主机端口 | 备注 |
|---|---|---|---|
| Nginx + 前端静态 | 80 | 80 | 访问网站首页 |
| Backend (Uvicorn) | 8000 | 8000 | 直连 API / Swagger 文档 |
| MySQL | 3306 | 不映射 | 仅 appnet 内部可达 |
| Redis | 6379 | 不映射 | 仅 appnet 内部可达 |

所有敏感凭据通过 `.env` → `compose.yaml` `environment` 注入，镜像内**不打包**任何真实密码或 AI Key。

---

## 接口文档访问地址

| 文档 | URL（本地开发） | URL（Docker 部署后） | 前提条件 |
|---|---|---|---|
| Swagger UI（可直接调试） | <http://127.0.0.1:8000/docs> | <http://服务器IP/docs> | `DEBUG=true` 时才暴露 |
| ReDoc（排版更整洁） | <http://127.0.0.1:8000/redoc> | <http://服务器IP/redoc> | `DEBUG=true` 时才暴露 |
| OpenAPI JSON 规范 | <http://127.0.0.1:8000/openapi.json> | <http://服务器IP/openapi.json> | `DEBUG=true` 时才暴露 |
| 健康检查 · 存活探针 | <http://127.0.0.1:8000/health/live> | <http://服务器IP/health/live> | 任何环境都可用 |
| 健康检查 · 就绪探针（DB + Redis 验活） | <http://127.0.0.1:8000/health/ready> | <http://服务器IP/health/ready> | 任何环境都可用 |

> 生产部署（`DEBUG=false`）时文档路由会被 FastAPI 关闭，避免接口 Schema 泄露。真要调试可以再开 DEBUG 临时启动一份或由运维在内网部署调试实例。

后端路由前缀统一为：
- 新闻：`/api/news/*`
- 用户：`/api/users/*`
- 收藏：`/api/favorite/*`
- 历史：`/api/history/*`
- AI 问答：`/api/ai/*`（Nginx 针对该前缀关闭 `proxy_buffering`，保证 SSE 流式）

前端通过同源 Nginx 的 `/api/*` 反代到后端，生产环境不存在跨域问题。

---

## 目录结构

```
newsapp/
├── toutiao_backend/          # FastAPI 后端
│   ├── cache/                # Redis 缓存写入层（TTL 配置集中在这里）
│   ├── config/               # db_conf / ai_conf / cache_conf  + dotenv 加载
│   ├── crud/                 # 纯 CRUD 实现（返回 dict，不返回 ORM 对象）
│   ├── models/               # SQLAlchemy 2.0 异步 ORM 模型
│   ├── routers/              # news / users / favorite / history / ai 五个路由模块
│   ├── schemas/              # Pydantic v2 请求/响应 Schema（字段全中文描述）
│   ├── utils/                # auth / security / rate_limit / exception + 全局异常注册
│   ├── main.py               # FastAPI 入口：CORS 白名单、路由挂载、异常注册、健康检查、探针
│   ├── Dockerfile
│   ├── requirements.txt
│   └── API接口规范文档.md
├── xwzx-news/                # Vue3 前端
│   ├── src/
│   │   ├── views/            # Login/Home/NewsDetail/Category/Favorite/History/AIChat 等 10 个页面
│   │   ├── store/modules/    # Pinia：user / news / favorite / history（已持久化）
│   │   ├── config/api.js     # Axios 实例 + baseURL 配置
│   │   └── router/index.js   # 路由守卫（未登录跳登录页）
│   ├── nginx.conf            # 前端静态 + /api 反代 + /api/ai SSE 不缓冲
│   ├── Dockerfile            # node:20-alpine 构建 → nginx:alpine 分发（多阶段）
│   └── vite.config.js
├── compose.yaml              # 4 服务编排：mysql / redis / backend / frontend-nginx
├── database.sql              # MySQL 建库建表 + 新闻种子数据（UTF8MB4）
├── .env.example              # 环境变量模板（密码 / AI Key / 限流 / DEBUG）
└── README.md                 # 本文件
```
