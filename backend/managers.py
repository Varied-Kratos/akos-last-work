# managers.py
# Заглушки для docker и qemu

def create_container(os_name, cpu, ram, disk, time_limit):
    # Возвращаем тестовые SSH данные
    return {
        "ssh_host": "127.0.0.1",
        "ssh_port": 2222,
        "ssh_user": "user",
        "ssh_password": "pass",
        "status": "running"
    }

def create_vm(os_name, cpu, ram, disk, time_limit):
    # Возвращаем тестовые SSH данные
    return {
        "ssh_host": "127.0.0.1",
        "ssh_port": 2223,
        "ssh_user": "user",
        "ssh_password": "pass",
        "status": "running"
    }

def start_machine(machine):
    # Просто возвращаем статус
    return {"status": "running"}

def stop_machine(machine):
    # Просто возвращаем статус
    return {"status": "stopped", "stop_reason": "stopped by user"}

def delete_machine(machine):
    # Просто возвращаем статус
    return {"status": "deleted"}
