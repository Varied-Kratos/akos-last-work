from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=3, max_length=128)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)

class MachineCreate(BaseModel):
    user_id: int
    type: str
    os_name: str
    cpu: int
    ram: int
    disk: int

class MachineResponse(BaseModel):
    id: int
    user_id: int
    name: str
    type: str
    os_name: str
    cpu: int
    ram: int
    disk: int
    status: str
    ssh_host: Optional[str]
    ssh_port: Optional[int]
    ssh_user: Optional[str]
    ssh_password: Optional[str]
    created_at: datetime
    stop_reason: Optional[str]

    model_config = ConfigDict(from_attributes=True)
