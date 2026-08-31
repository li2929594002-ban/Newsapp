import uuid
from datetime import timedelta, datetime

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.users import User, UserToken
from schemas.users import UserRequest, UserUpdateRequest
from utils import security



# 根据用户名查询数据库
async def get_user_by_username(db:AsyncSession, username:str):
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalar_one_or_none()


# 创建用户
async def create_user(db:AsyncSession,user_data: UserRequest):
    # 先密码加密处理 → add
    hashed_password = security.get_hash_password(user_data.password)
    user = User(username = user_data.username, password = hashed_password)
    db.add(user)


    # await db.refresh(user)  # 从数据库读回最新的 user,自动执行flush并查询user

    # 刷入数据库：触发自增ID、默认字段回填，不提交事务
    await db.flush()
    return user


# 生成 Token
async def create_token(db:AsyncSession,user_id:int):
    # 生成 Token + 设置过期时间 → 查询数据库当前用户是否有 Token → 有：更新；没有：添加
    token = str(uuid.uuid4())
    # timedelta(days=7, hours=2, minutes=30, seconds=10)
    expires_at = datetime.now() + timedelta(days=7)

    query = select(UserToken).where(UserToken.user_id == user_id)
    result = await db.execute(query)
    user_token = result.scalar_one_or_none()

    if user_token:
        user_token.token = token
        user_token.expires_at = expires_at
    else:
        user_token = UserToken(user_id=user_id, token=token, expires_at=expires_at)
        db.add(user_token)
        # # await db.commit()
        # await db.flush()

    return token


async def authenticate_user(db:AsyncSession,username:str,password:str):
    user = await get_user_by_username(db,username)
    if not user:
        return None
    if not security.verify_password(password,user.password):
        return None

    return user


# 根据 Token 查询用户:验证 Token → 查询用户
async def get_user_by_token(db:AsyncSession,token:str):
    # 一次 join 完成 Token 有效性校验与用户查询，减少一次数据库往返
    # 过期判断下推到 SQL：expires_at 早于当前时间的记录直接不匹配
    query = (
        select(User)
        .join(UserToken, UserToken.user_id == User.id)
        .where(
            UserToken.token == token,
            UserToken.expires_at > datetime.now()
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


# 更新用户信息：update更新 → 检查是否命中 → 获取更新后的用户返回
async def update_user(db:AsyncSession, user:User, user_data:UserUpdateRequest):
    # update(User).where(User.id == user.id).values(字段=值, 字段=值)
    # user_data 是一个 Pydantic类型，得到字典 → **解包      user_data.model_dump()可以把Pydantic类型转换成字典
    # 没有设置值的不更新
    query = update(User).where(User.id == user.id).values(**user_data.model_dump(
        exclude_unset = True,   # 字典里剔除值为 None 的字段
        exclude_none = True     # 只保留用户显式赋值的字段；自动剔除仅使用模型默认值、从未手动设置过的字段
    ))

    result = await db.execute(query)

    # 检查更新
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail = "用户不存在")

    # 获取一下更新后的用户
    updated_user = await get_user_by_username(db, user.username)
    return updated_user


# 修改密码：验证旧密码 → 新密码加密 → 修改密码 → 轮换Token
async def change_password(db:AsyncSession, user:User, old_password:str, new_password:str):
    if not security.verify_password(old_password,user.password):
        return None

    hasher_new_pwd = security.get_hash_password(new_password)
    user.password = hasher_new_pwd


    await db.flush()

    #（可选）若需要拿到 update_time 等库端生成值，再 refresh
    # await db.refresh(user)

    # 改密成功后轮换 Token：旧 Token 立即失效，防止已泄露的旧凭证继续使用
    new_token = await create_token(db, user.id)
    return new_token
