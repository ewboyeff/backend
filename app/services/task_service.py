from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate

async def create_task(db: AsyncSession, task_in: TaskCreate, user_id: int) -> Task:
    task = Task(**task_in.model_dump(), owner_id=user_id)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task

async def get_user_tasks(db: AsyncSession, user_id: int) -> list[Task]:
    result = await db.execute(select(Task).where(Task.owner_id == user_id).order_by(Task.created_at.desc()))
    return list(result.scalars().all())

async def get_task_by_id(db: AsyncSession, task_id: int, user_id: int) -> Task:
    result = await db.execute(select(Task).where(Task.id == task_id, Task.owner_id == user_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task

async def update_task(db: AsyncSession, task_id: int, task_in: TaskUpdate, user_id: int) -> Task:
    task = await get_task_by_id(db, task_id, user_id)
    update_data = task_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(task, field, value)
        
    await db.commit()
    await db.refresh(task)
    return task

async def delete_task(db: AsyncSession, task_id: int, user_id: int):
    task = await get_task_by_id(db, task_id, user_id)
    await db.delete(task)
    await db.commit()
