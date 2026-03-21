from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class RoleEnum(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    member = "member"

class StatusEnum(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    review = "review"
    done = "done"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.member)
    created_at = Column(DateTime, default=datetime.utcnow)
    projects = relationship("ProjectMember", back_populates="user")

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    members = relationship("ProjectMember", back_populates="project")
    tasks = relationship("Task", back_populates="project")

class ProjectMember(Base):
    __tablename__ = "project_members"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    role = Column(Enum(RoleEnum), default=RoleEnum.member)
    user = relationship("User", back_populates="projects")
    project = relationship("Project", back_populates="members")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    duration = Column(Float, default=1.0)
    status = Column(Enum(StatusEnum), default=StatusEnum.open)
    progress = Column(Float, default=0.0)
    pos_x = Column(Float, default=0.0)
    pos_y = Column(Float, default=0.0)
    faz = Column(Float, default=0.0)
    fez = Column(Float, default=0.0)
    saz = Column(Float, default=0.0)
    sez = Column(Float, default=0.0)
    gp = Column(Float, default=0.0)
    fp = Column(Float, default=0.0)
    depth = Column(Integer, default=0)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    parent_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="tasks")
    subtasks = relationship("Task", back_populates="parent")
    parent = relationship("Task", back_populates="subtasks", remote_side="Task.id")
    predecessors = relationship("TaskDependency", foreign_keys="TaskDependency.task_id", back_populates="task")

class TaskDependency(Base):
    __tablename__ = "task_dependencies"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    predecessor_id = Column(Integer, ForeignKey("tasks.id"))
    task = relationship("Task", foreign_keys=[task_id], back_populates="predecessors")

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)