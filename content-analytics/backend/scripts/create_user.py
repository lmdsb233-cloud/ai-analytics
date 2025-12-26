#!/usr/bin/env python
"""创建测试用户脚本"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.db.session import async_session_maker
from app.models.user import User
from app.core.security import get_password_hash


async def create_test_user():
    """创建测试用户"""
    async with async_session_maker() as db:
        user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            is_active=True
        )
        db.add(user)
        await db.commit()
        print(f"测试用户创建成功！")
        print(f"用户名: admin")
        print(f"密码: admin123")


if __name__ == "__main__":
    asyncio.run(create_test_user())
