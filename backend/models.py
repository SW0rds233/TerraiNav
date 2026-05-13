"""
数据库模型定义
包含 users 和 history 两个表
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    usertype = Column(String(20), default="user")
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联历史记录
    histories = relationship("History", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "usertype": self.usertype,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    task_name = Column(String(200), nullable=False)
    description = Column(Text)
    input_image_url = Column(Text)
    heatmap_url = Column(Text)
    route_url = Column(Text)
    report_url = Column(Text)
    task_status = Column(String(50), default="completed")
    task_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联用户
    user = relationship("User", back_populates="histories")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "task_name": self.task_name,
            "description": self.description,
            "input_image_url": self.input_image_url,
            "heatmap_url": self.heatmap_url,
            "route_url": self.route_url,
            "report_url": self.report_url,
            "task_status": self.task_status,
            "task_time": self.task_time.isoformat() if self.task_time else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }