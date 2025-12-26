"""添加iFlow相关数据库列"""
import asyncio
from sqlalchemy import text
import sys
sys.path.insert(0, '.')

from app.db.session import async_session_maker


async def add_columns():
    async with async_session_maker() as db:
        # 添加 iflow_api_key 列
        try:
            await db.execute(text('ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS iflow_api_key TEXT'))
            await db.commit()
            print('Added iflow_api_key column')
        except Exception as e:
            print(f'iflow_api_key: {e}')
            await db.rollback()
        
        # 添加 iflow_model 列
        try:
            await db.execute(text('ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS iflow_model VARCHAR(100)'))
            await db.commit()
            print('Added iflow_model column')
        except Exception as e:
            print(f'iflow_model: {e}')
            await db.rollback()
        
        # 设置默认值
        try:
            await db.execute(text("UPDATE user_settings SET iflow_model = 'kimi-k2-0905' WHERE iflow_model IS NULL"))
            await db.commit()
            print('Set default values')
        except Exception as e:
            print(f'Update: {e}')

        print('Migration completed!')


if __name__ == '__main__':
    asyncio.run(add_columns())
