import docker
import time
import random
from datetime import datetime
import subprocess
import os
import signal
import platform

class DockerManager:
    def __init__(self):
        self.client = docker.from_env()

    def create_container(self, os_name, cpu, ram, disk):
        images = {
            "ubuntu":"ubuntu-ssh:latest",
            "debian":"debian-ssh:latest", 
            "alpine":"alpine-ssh:latest",
        }
        image = images.get(os_name.lower())
        timestamp = int(time.time())
        random_num = random.randint(1000, 9999)
        container_name = f"{os_name}_{timestamp}_{random_num}"
        try:
            container = self.client.containers.run(
                image=image,
                name=container_name,
                detach=True,
                nano_cpus=cpu*(10**9),
                mem_limit=f"{ram}m",
                ports={'22/tcp': None},
            )
            container.reload()
            ports = container.ports['22/tcp'][0]['HostPort']
            return {
                'container_id':container.id,
                'container_name':container_name,
                'ssh_host':'localhost',
                'ssh_port':ports,
                'ssh_user':'root',
                'ssh_password':'password',
                'status':'running',
                'os_name':os_name,
                'cpu':cpu,
                'ram':ram,
                'disk':disk,
                'created_at':datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def stop_container_by_name(self, name):
        try:
            container = self.client.containers.get(name)
            container.stop()
            return True
        except:
            return False
        
    def start_container_by_name(self, name):
        try:
            container = self.client.containers.get(name)
            container.start()
            return True
        except:
            return False
    
    def delete_container_by_name(self, name):
        try:
            container = self.client.containers.get(name)
            container.remove()
            return True
        except:
            return False
        
    def list_containers(self):
        containers = self.client.containers.list(all=True)
        result = []
        for container in containers:
            try:
                container.reload()
                ports = container.ports['22/tcp'][0]['HostPort']
                result.append({
                    'id': container.id,
                    'name': container.name,
                    'status': container.status,
                    'ssh_port': ports,
                    'created': container.attrs['Created'][:10]
                })
            except Exception as e:
                print(f"Error parsing container {container.id}: {e}")
                continue
        return result
    

class QemuManager:
    def __init__(self, base_dir: str = "./vms"):
        self.base_dir = os.path.abspath(base_dir)
        self.images_dir = f"{self.base_dir}/images"
        self.disks_dir = f"{self.base_dir}/disks"
        self.running_dir = f"{self.base_dir}/running"
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.disks_dir, exist_ok=True)
        os.makedirs(self.running_dir, exist_ok=True)
        self.system = platform.system()
        self.arch = platform.machine()
        self.ssh_creds = {
            "ubuntu": {"user": "ubuntu", "password": "ubuntu"},
            "debian": {"user": "debian", "password": "debian"},
            "alpine": {"user": "root", "password": "root"}
        }

    def _get_qemu_command(self, vm_name, disk_path, ssh_port, cpu, ram):
        base_cmd = [
            '-m', str(ram),
            '-smp', str(cpu),
            '-drive', f'file={disk_path},format=qcow2',
            '-netdev', f'user,id=net0,hostfwd=tcp::{ssh_port}-:22',
            '-device', 'virtio-net-pci,netdev=net0',
            '-pidfile', f'{self.running_dir}/{vm_name}.pid',
            '-daemonize',
            '-display', 'none',
        ]
        if self.system == "Darwin" and self.arch == "arm64":
            return ['qemu-system-aarch64', '-machine', 'virt', '-accel', 'hvf'] + base_cmd
        elif self.system == "Linux" and self.arch == "x86_64":
            return ['qemu-system-x86_64', '-enable-kvm'] + base_cmd
        elif self.system == "Linux" and self.arch == "aarch64":
            return ['qemu-system-aarch64', '-machine', 'virt', '-accel', 'kvm'] + base_cmd
        else:
            return ['qemu-system-x86_64'] + base_cmd

    def create_vm(self, os_name, cpu, ram, disk):
        base_image_path = f"{self.images_dir}/{os_name}.qcow2"
        if not os.path.exists(base_image_path):
            return {
                'status': 'failed',
                'error': f"Образ {os_name}.qcow2 не найден в {self.images_dir}"
            }
        timestamp = int(time.time())
        random_num = random.randint(1000, 9999)
        vm_name = f"{os_name}_{timestamp}_{random_num}"
        disk_path = f"{self.disks_dir}/{vm_name}.qcow2"
        ssh_port = random.randint(20000, 30000)
        try:
            subprocess.run([
                'qemu-img', 'create', '-f', 'qcow2',
                '-b', base_image_path,
                '-F', 'qcow2',
                disk_path
            ], check=True, capture_output=True)
            cmd = self._get_qemu_command(vm_name, disk_path, ssh_port, cpu, ram)
            subprocess.run(cmd, check=True)
            pid = None
            pid_file = f"{self.running_dir}/{vm_name}.pid"
            if os.path.exists(pid_file):
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
            creds = self.ssh_creds.get(os_name, {"user": "root", "password": ""})
            return {
                'vm_id': vm_name,
                'vm_name': vm_name,
                'ssh_host': 'localhost',
                'ssh_port': ssh_port,
                'ssh_user': creds["user"],      
                'ssh_password': creds["password"],       
                'status': 'running',
                'pid': pid,
                'os_name': os_name,
                'cpu': cpu,
                'ram': ram,
                'disk': disk,
                'disk_path': disk_path,
                'created_at': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def stop_vm(self, vm_name):
        pid_file = f"{self.running_dir}/{vm_name}.pid"
        if not os.path.exists(pid_file):
            return False
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGKILL)
            os.remove(pid_file)
            return True
        except Exception as e:
            return False
    
    def start_vm(self, vm_name):
        disk_path = f"{self.disks_dir}/{vm_name}.qcow2"
        if not os.path.exists(disk_path):
            return False
        parts = vm_name.split('_')
        os_name = parts[0] if parts else "unknown"
        try:
            ssh_port = random.randint(20000, 30000)
            cmd = self._get_qemu_command(vm_name, disk_path, ssh_port, 1, 512)
            subprocess.run(cmd, check=True)
            return True
        except Exception as e:
            return False
    
    def delete_vm(self, vm_name):
        self.stop_vm(vm_name)
        disk_path = f"{self.disks_dir}/{vm_name}.qcow2"
        if os.path.exists(disk_path):
            os.remove(disk_path)
        pid_file = f"{self.running_dir}/{vm_name}.pid"
        if os.path.exists(pid_file):
            os.remove(pid_file)
        return True
    
    def list_vms(self):
        vms = []
        for file in os.listdir(self.disks_dir):
            if file.endswith('.qcow2'):
                vm_name = file.replace('.qcow2', '')
                vms.append(vm_name)
        return vms
    
    def get_vm_info(self, vm_name):
        curr_vms = self.list_vms()
        for vm in curr_vms:
            if vm == vm_name:
                return vm
        return None
