from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Project, ProjectMember, RoleEnum
from routers.users import get_current_user
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/projects", tags=["projects"])

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: int

    class Config:
        from_attributes = True

@router.post("/", response_model=ProjectOut)
def create_project(data: ProjectCreate, token: str, db: Session = Depends(get_db)):
    current_user = get_current_user(token, db)
    project = Project(
        name=data.name,
        description=data.description,
        owner_id=current_user.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    member = ProjectMember(
        user_id=current_user.id,
        project_id=project.id,
        role=RoleEnum.admin
    )
    db.add(member)
    db.commit()
    return project

@router.get("/", response_model=list[ProjectOut])
def get_projects(token: str, db: Session = Depends(get_db)):
    current_user = get_current_user(token, db)
    memberships = db.query(ProjectMember).filter(
        ProjectMember.user_id == current_user.id
    ).all()
    project_ids = [m.project_id for m in memberships]
    return db.query(Project).filter(Project.id.in_(project_ids)).all()

@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, token: str, db: Session = Depends(get_db)):
    current_user = get_current_user(token, db)
    membership = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Keine Berechtigung")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    return project

@router.put("/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, data: ProjectCreate, token: str, db: Session = Depends(get_db)):
    current_user = get_current_user(token, db)
    membership = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    if not membership or membership.role not in [RoleEnum.admin, RoleEnum.manager]:
        raise HTTPException(status_code=403, detail="Keine Berechtigung")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    project.name = data.name
    project.description = data.description
    db.commit()
    db.refresh(project)
    return project

@router.delete("/{project_id}")
def delete_project(project_id: int, token: str, db: Session = Depends(get_db)):
    current_user = get_current_user(token, db)
    membership = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    if not membership or membership.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Keine Berechtigung")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    db.delete(project)
    db.commit()
    return {"detail": "Projekt gelöscht"}

@router.post("/{project_id}/members")
def add_member(project_id: int, user_id: int, role: RoleEnum, token: str, db: Session = Depends(get_db)):
    current_user = get_current_user(token, db)
    membership = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    if not membership or membership.role not in [RoleEnum.admin, RoleEnum.manager]:
        raise HTTPException(status_code=403, detail="Keine Berechtigung")
    new_member = ProjectMember(user_id=user_id, project_id=project_id, role=role)
    db.add(new_member)
    db.commit()
    return {"detail": "Mitglied hinzugefügt"}