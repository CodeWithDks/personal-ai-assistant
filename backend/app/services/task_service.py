from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.database.models import Task
from app.schemas.task_schema import TaskCreate, TaskUpdate


def create_task(db: Session, task: TaskCreate):
    new_task = Task(
        title=task.title,
        description=task.description
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task


def get_tasks(db: Session):
    return db.query(Task).all()


def get_task_by_id(db: Session, task_id: int):
    return db.query(Task).filter(Task.id == task_id).first()


def update_task(db: Session, task_id: int, task: TaskUpdate):
    db_task = get_task_by_id(db, task_id)

    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_task, key, value)

    db.commit()
    db.refresh(db_task)

    return db_task

def delete_task(db: Session, task_id: int):
    db_task = get_task_by_id(db, task_id)

    if db_task is None:
        raise HTTPException(status_code=404, detail='Task not found')
    
    db.delete(db_task)
    db.commit()

    return {"message": "Buy groceries' has been deleted successfully."}