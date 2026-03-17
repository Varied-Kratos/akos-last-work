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

@app.post("/register", response_model=schemas.UserRegister)
def register(user: schemas.UserRegister, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = models.User(username=user.username, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return user

@app.post("/login", response_model=schemas.UserRegister)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username, models.User.password == user.password).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    return schemas.UserRegister(username=db_user.username, password=db_user.password)

@app.post("/machines/create", response_model=schemas.MachineResponse)
def create_machine(machine: schemas.MachineCreate, db: Session = Depends(get_db)):
    if machine.type not in ["container", "vm"]:
        raise HTTPException(status_code=400, detail="type must be 'container' or 'vm'")
    if not db.query(models.User).filter(models.User.id == machine.user_id).first():
        raise HTTPException(status_code=404, detail="User not found")
    if machine.type == "container":
        result = managers.create_container(machine.os_name, machine.cpu, machine.ram, machine.disk, machine.time_limit)
    else:
        result = managers.create_vm(machine.os_name, machine.cpu, machine.ram, machine.disk, machine.time_limit)
    db_machine = models.Machine(
        user_id=machine.user_id,
        type=machine.type,
        os_name=machine.os_name,
        cpu=machine.cpu,
        ram=machine.ram,
        disk=machine.disk,
        status=result["status"],
        ssh_host=result["ssh_host"],
        ssh_port=result["ssh_port"],
        ssh_user=result["ssh_user"],
        ssh_password=result["ssh_password"],
        time_limit=machine.time_limit
    )
    db.add(db_machine)
    db.commit()
    db.refresh(db_machine)
    return db_machine

@app.get("/machines", response_model=List[schemas.MachineResponse])
def list_machines(user_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.Machine)
    if user_id:
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
    machine.status = result["status"]
    db.commit()
    db.refresh(machine)
    return machine

@app.post("/machines/{machine_id}/stop", response_model=schemas.MachineResponse)
def stop_machine(machine_id: int, db: Session = Depends(get_db)):
    machine = db.query(models.Machine).filter(models.Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    result = managers.stop_machine(machine)
    machine.status = result["status"]
    machine.stop_reason = result.get("stop_reason")
    db.commit()
    db.refresh(machine)
    return machine

@app.delete("/machines/{machine_id}")
def delete_machine(machine_id: int, db: Session = Depends(get_db)):
    machine = db.query(models.Machine).filter(models.Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    managers.delete_machine(machine)
    db.delete(machine)
    db.commit()
    return {"detail": "Machine deleted"}
