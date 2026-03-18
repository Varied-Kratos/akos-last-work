from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    machines = relationship("Machine", back_populates="user")

class Machine(Base):
    __tablename__ = "machines"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # container or vm
    os_name = Column(String, nullable=False)
    cpu = Column(Integer, nullable=False)
    ram = Column(Integer, nullable=False)
    disk = Column(Integer, nullable=False)
    status = Column(String, default="stopped")
    ssh_host = Column(String)
    ssh_port = Column(Integer)
    ssh_user = Column(String)
    ssh_password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    time_limit = Column(Integer)
    stop_reason = Column(String)
    user = relationship("User", back_populates="machines")
