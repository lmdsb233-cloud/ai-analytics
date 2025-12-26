#!/usr/bin/env python
"""初始化数据库脚本"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from app.db.session import engine
from app.db.base import Base
from app.models import *  # noqa


async def init_db():
    """初始化数据库表"""
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
        print("数据库表创建成功！")


async def drop_db():
    """删除所有表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("数据库表已删除！")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        asyncio.run(drop_db())
    else:
        asyncio.run(init_db())
