"""修复卡住的数据集"""
import asyncio
from app.tasks.dataset_tasks import _parse_dataset
from app.db.session import async_session_maker
from sqlalchemy import select
from app.models.dataset import Dataset, DatasetStatus


async def fix_datasets():
    async with async_session_maker() as db:
        result = await db.execute(
            select(Dataset).where(Dataset.status != DatasetStatus.COMPLETED)
        )
        datasets = result.scalars().all()
        print(f"Found {len(datasets)} datasets to process")
        
        for d in datasets:
            print(f"Processing dataset {d.id} ({d.name})...")
            await _parse_dataset(str(d.id))
            print(f"  Done!")
        
        print("All datasets processed!")


if __name__ == "__main__":
    asyncio.run(fix_datasets())
