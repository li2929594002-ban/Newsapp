from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class UserRequest(BaseModel):
    # 长度约束与 DB 字段一致：username String(50)；密码与改密接口统一 min_length=6
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=64, description="密码")


# user_info 对应的类: 基础类 + Info类(id、用户名)
class UserInfoBase(BaseModel):
    """
    用户信息基础数据模型
    """
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    bio: Optional[str] = Field (None, max_length=500, description="个人简介")


# user_info 对应的类
class UserInfoResponse(UserInfoBase):
    id:int
    username:str
    # 模型类配置
    model_config = ConfigDict(
        from_attributes=True  # 允许从 ORM 对象中取值
    )


# data 数据类型
class UserAuthResponse(BaseModel):
    token: str
    user_info: UserInfoResponse = Field(...,alias = "userInfo")

    # 模型类配置
    model_config = ConfigDict(
        populate_by_name=True,  # alias / 字段名兼容
        from_attributes=True    # 允许从 ORM 对象中取值
    )


# 更新用户信息的模型类
# 长度约束与 DB 字段一致（String(50)/String(255)/String(500)/String(20)），超长在参数校验层返回422而非数据库500
# gender 与 DB Enum('male','female','unknown') 对齐，非法值同样在参数校验层拦截
class UserUpdateRequest(BaseModel):
    nickname: Optional[str] = Field(None, min_length=1, max_length=50, description="昵称")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    gender: Optional[Literal['male', 'female', 'unknown']] = Field(None, description="性别")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    phone: Optional[str] = Field(None, min_length=1, max_length=20, description="手机号")


class UserChangePasswordRequest(BaseModel):
    old_password:str = Field(..., alias="oldPassword", description="旧密码")
    new_password:str = Field(..., min_length=6, alias="newPassword", description="新密码")


