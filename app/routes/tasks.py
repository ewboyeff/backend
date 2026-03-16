from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services import task_service

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_new_task(
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await task_service.create_task(db, task_in, current_user.id)

@router.get("", response_model=list[TaskResponse])
async def read_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await task_service.get_user_tasks(db, current_user.id)

@router.get("/{task_id}", response_model=TaskResponse)
async def read_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await task_service.get_task_by_id(db, task_id, current_user.id)

@router.put("/{task_id}", response_model=TaskResponse)
async def update_existing_task(
    task_id: int,
    task_in: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await task_service.update_task(db, task_id, task_in, current_user.id)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await task_service.delete_task(db, task_id, current_user.id)
