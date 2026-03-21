from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Task, TaskDependency, ProjectMember, RoleEnum, StatusEnum, Comment
from routers.users import get_current_user
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/tasks", tags=["tasks"])

class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    duration: float = 1.0
    project_id: Optional[int] = None
    parent_id: Optional[int] = None
    assignee_id: Optional[int] = None
    predecessor_ids: Optional[list[int]] = []

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[float] = None
    status: Optional[StatusEnum] = None
    pos_x: Optional[float] = None
    pos_y: Optional[float] = None
    assignee_id: Optional[int] = None
    faz: Optional[float] = None
    fez: Optional[float] = None
    saz: Optional[float] = None
    sez: Optional[float] = None
    gp: Optional[float] = None
    fp: Optional[float] = None

class TaskOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    duration: float
    status: StatusEnum
    progress: float
    pos_x: float
    pos_y: float
    faz: float
    fez: float
    saz: float
    sez: float
    gp: float
    fp: float
    depth: int
    project_id: Optional[int]
    parent_id: Optional[int]
    assignee_id: Optional[int]
    predecessors: list[dict] = []

    class Config:
        from_attributes = True

class CommentCreate(BaseModel):
    content: str

def get_predecessors(task_id: int, db: Session) -> list[dict]:
    deps = db.query(TaskDependency).filter(TaskDependency.task_id == task_id).all()
    return [{"predecessor_id": d.predecessor_id} for d in deps]

def task_to_dict(task: Task, db: Session) -> dict:
    return {
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "duration": task.duration,
        "status": task.status,
        "progress": task.progress,
        "pos_x": task.pos_x,
        "pos_y": task.pos_y,
        "faz": task.faz,
        "fez": task.fez,
        "saz": task.saz,
        "sez": task.sez,
        "gp": task.gp,
        "fp": task.fp,
        "depth": task.depth,
        "project_id": task.project_id,
        "parent_id": task.parent_id,
        "assignee_id": task.assignee_id,
        "predecessors": get_predecessors(task.id, db)
    }

def calculate_cpm(tasks: list[Task], dependencies: list[TaskDependency]):
    task_map = {t.id: t for t in tasks}
    dep_map = {}
    for d in dependencies:
        if d.task_id not in dep_map:
            dep_map[d.task_id] = []
        dep_map[d.task_id].append(d.predecessor_id)

    for task in tasks:
        preds = dep_map.get(task.id, [])
        if not preds:
            task.faz = 0.0
        else:
            task.faz = max(task_map[p].fez for p in preds if p in task_map)
        task.fez = task.faz + task.duration

    max_fez = max((t.fez for t in tasks), default=0.0)
    for task in reversed(tasks):
        successors = [t for t in tasks if task.id in dep_map.get(t.id, [])]
        if not successors:
            task.sez = max_fez
        else:
            task.sez = min(s.saz for s in successors)
        task.saz = task.sez - task.duration
        task.gp = task.saz - task.faz
        task.fp = min(
            (task_map[s_id].faz for t in tasks for s_id in dep_map.get(t.id, []) if s_id == task.id),
            default=task.fez
        ) - task.fez

    return tasks

def update_progress(task: Task, db: Session):
    subtasks = db.query(Task).filter(Task.parent_id == task.id).all()
    if not subtasks:
        return
    done_count = sum(1 for t in subtasks if t.status == StatusEnum.done)
    task.progress = round((done_count / len(subtasks)) * 100, 1)
    if done_count == len(subtasks):
        task.status = StatusEnum.done
    db.commit()

@router.post("/", response_model=dict)
def create_task(data: TaskCreate, token: str, db: Session = Depends(get_db)):
    current_user = get_current_user(token, db)
    depth = 0
    if data.parent_id:
        parent = db.query(Task).filter(Task.id == data.parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Elternaufgabe nicht gefunden")
        depth = parent.depth + 1
    task = Task(
        name=data.name,
        description=data.description,
        duration=data.duration,
        project_id=data.project_id,
        parent_id=data.parent_id,
        assignee_id=data.assignee_id,
        depth=depth
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    for pred_id in data.predecessor_ids:
        dep = TaskDependency(task_id=task.id, predecessor_id=pred_id)
        db.add(dep)
    db.commit()
    return task_to_dict(task, db)

@router.get("/project/{project_id}")
def get_tasks_by_project(project_id: int, token: str, db: Session = Depends(get_db)):
    current_user = get_current_user(token, db)
    membership = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Keine Berechtigung")
    tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.parent_id == None
    ).all()
    dependencies = db.query(TaskDependency).all()
    tasks = calculate_cpm(tasks, dependencies)
    db.commit()
    return [task_to_dict(t, db) for t in tasks]

@router.get("/{task_id}/subtasks")
def get_subtasks(task_id: int, token: str, db: Session = Depends(get_db)):
    current_user = get_current_user(token, db)
    subtasks = db.query(Task).filter(Task.parent_id == task_id).all()
    dependencies = db.query(TaskDependency).all()
    subtasks = calculate_cpm(subtasks, dependencies)
    db.commit()
    return [task_to_dict(t, db) for t in subtasks]

@router.get("/{task_id}")
def get_task(task_id: int, token: str, db: Session = Depends(get_db)):
    current_user = get_current_user(token, db)
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")
    return task_to_dict(task, db)

@router.put("/{task_id}")
def update_task(task_id: int, data: TaskUpdate, token: str, db: Session = Depends(get_db)):
    current_user = get_current_user(token, db)
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")
    if data.name is not None:
        task.name = data.name
    if data.description is not None:
        task.description = data.description
    if data.duration is not None:
        task.duration = data.duration
    if data.status is not None:
        task.status = data.status
        if data.status == StatusEnum.open:
            task.progress = 0.0
    if data.pos_x is not None:
        task.pos_x = data.pos_x
    if data.pos_y is not None:
        task.pos_y = data.pos_y
    if data.assignee_id is not None:
        task.assignee_id = data.assignee_id
    if data.faz is not None:
        task.faz = data.faz
    if data.fez is not None:
        task.fez = data.fez
    if data.saz is not None:
        task.saz = data.saz
    if data.sez is not None:
        task.sez = data.sez
    if data.gp is not None:
        task.gp = data.gp
    if data.fp is not None:
        task.fp = data.fp
    db.commit()
    db.refresh(task)
    if task.parent_id:
        parent = db.query(Task).filter(Task.id == task.parent_id).first()
        if parent:
            update_progress(parent, db)
    return task_to_dict(task, db)

@router.delete("/{task_id}")
def delete_task(task_id: int, token: str, db: Session = Depends(get_db)):
    current_user = get_current_user(token, db)
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")
    db.delete(task)
    db.commit()
    return {"detail": "Aufgabe gelöscht"}

@router.post("/{task_id}/comments")
def add_comment(task_id: int, data: CommentCreate, token: str, db: Session = Depends(get_db)):
    current_user = get_current_user(token, db)
    comment = Comment(
        content=data.content,
        task_id=task_id,
        user_id=current_user.id
    )
    db.add(comment)
    db.commit()
    return {"detail": "Kommentar hinzugefügt"}

@router.get("/{task_id}/comments")
def get_comments(task_id: int, token: str, db: Session = Depends(get_db)):
    current_user = get_current_user(token, db)
    comments = db.query(Comment).filter(Comment.task_id == task_id).all()
    return [{"id": c.id, "content": c.content, "user_id": c.user_id, "created_at": c.created_at} for c in comments]