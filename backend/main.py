from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from . import models, schemas, managers
from .database import SessionLocal, engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Hosting Provider API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserRegister, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = models.User(username=user.username, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=schemas.UserResponse)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username, models.User.password == user.password).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    return db_user

@app.post("/machines/create", response_model=schemas.MachineResponse)
def create_machine(machine: schemas.MachineCreate, db: Session = Depends(get_db)):
    if machine.type not in ["container", "vm"]:
        raise HTTPException(status_code=400, detail="type must be 'container' or 'vm'")
    if not db.query(models.User).filter(models.User.id == machine.user_id).first():
        raise HTTPException(status_code=404, detail="User not found")
    
    if machine.type == "container":
        result = managers.create_container(machine.os_name, machine.cpu, machine.ram, machine.disk)
    else:
        result = managers.create_vm(machine.os_name, machine.cpu, machine.ram, machine.disk)
    
    if result.get("status") in ["failed", "error"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to create machine"))
    
    instance_name = result.get("container_name") or result.get("vm_name")
    if not instance_name:
        raise HTTPException(status_code=500, detail="Failed to get instance name from manager")
    
    db_machine = models.Machine(
        user_id=machine.user_id,
        name=instance_name,
        type=machine.type,
        os_name=machine.os_name,
        cpu=machine.cpu,
        ram=machine.ram,
        disk=machine.disk,
        status=result.get("status", "unknown"),
        ssh_host=result.get("ssh_host"),
        ssh_port=result.get("ssh_port"),
        ssh_user=result.get("ssh_user"),
        ssh_password=result.get("ssh_password")
    )
    db.add(db_machine)
    db.commit()
    db.refresh(db_machine)
    return db_machine

@app.get("/machines", response_model=List[schemas.MachineResponse])
def list_machines(user_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.Machine)
    if user_id is not None:
        query = query.filter(models.Machine.user_id == user_id)
    return query.all()

@app.get("/machines/{machine_id}", response_model=schemas.MachineResponse)
def get_machine(machine_id: int, db: Session = Depends(get_db)):
    machine = db.query(models.Machine).filter(models.Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine

@app.post("/machines/{machine_id}/start", response_model=schemas.MachineResponse)
def start_machine(machine_id: int, db: Session = Depends(get_db)):
    machine = db.query(models.Machine).filter(models.Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    result = managers.start_machine(machine)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to start machine"))
    machine.status = result.get("status", "running")
    db.commit()
    db.refresh(machine)
    return machine

@app.post("/machines/{machine_id}/stop", response_model=schemas.MachineResponse)
def stop_machine(machine_id: int, db: Session = Depends(get_db)):
    machine = db.query(models.Machine).filter(models.Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    result = managers.stop_machine(machine)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to stop machine"))
    machine.status = result.get("status", "stopped")
    machine.stop_reason = result.get("stop_reason")
    db.commit()
    db.refresh(machine)
    return machine

@app.delete("/machines/{machine_id}")
def delete_machine(machine_id: int, db: Session = Depends(get_db)):
    machine = db.query(models.Machine).filter(models.Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    result = managers.delete_machine(machine)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to delete machine"))
    db.delete(machine)
    db.commit()
    return {"detail": "Machine deleted"}
