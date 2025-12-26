from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # 关闭SQL日志提升性能
    future=True,
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
    pool_pre_ping=True,  # 自动检测断开的连接
    pool_recycle=300,  # 5分钟回收连接
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


def create_thread_session_maker():
    """为后台线程创建独立的数据库引擎和会话工厂"""
    thread_engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=300,
    )
    return async_sessionmaker(
        thread_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    ), thread_engine


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
