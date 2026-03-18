import streamlit as st
import requests
API_URL = "http://127.0.0.1:8000"

def show_auth():
    st.header("Вход / Регистрация")

    mode = st.radio("Выберите", ["Вход", "Регистрация"])

    username = st.text_input("Имя")
    password = st.text_input("Пароль", type="password")

    if st.button(mode):
        if mode == "Вход":
            res = requests.post(f"{API_URL}/login", json={
                "username": username,
                "password": password
            })
        else:
            res = requests.post(f"{API_URL}/register", json={
                "username": username,
                "password": password
            })

        if res.status_code == 200:
            st.session_state["user"] = res.json()
            st.success("Успешно")
            st.rerun()
        else:
            st.error(res.text)

def show_dashboard():
    user = st.session_state["user"]

    if st.button("Выход"):
        del st.session_state["user"]
        st.rerun()
    
    st.subheader("Создать VM или контейнер")

    machine_type = st.selectbox("Тип", ["container", "vm"])
    os_name = st.selectbox("ОС", ["alpine", "ubuntu", "debian"])
    cpu = st.slider("CPU", 1, 4)
    ram = st.slider("RAM (MB)", 512, 4096, step=512)
    disk = st.slider("Диск (GB)", 1, 20)
    time_limit = st.slider("Время (мин)", 1, 120)

    if st.button("Создать"):
        res = requests.post(f"{API_URL}/machines/create", json={
            "user_id": user["id"],
            "type": machine_type,
            "os_name": os_name,
            "cpu": cpu,
            "ram": ram,
            "disk": disk,
            "time_limit": time_limit
        })

        if res.status_code == 200:
            st.success("VM создана!")
            st.rerun()
        else:
            st.error(res.text)

    res = requests.get(f"{API_URL}/machines", params={
        "user_id": user["id"]
    })

    machines = res.json()
    containers = [c for c in machines if c["type"] == "container"]
    vms = [vm for vm in machines if vm["type"] == "vm"]

    st.subheader("VM")
    for vm in vms:
        st.write(f"ID: {vm['id']} | {vm['os_name']} | {vm['type']} | {vm['status']}")
        col1, col2, col3 = st.columns(3)

        if col1.button("Старт", key=f"start_{vm['id']}"):
            requests.post(f"{API_URL}/machines/{vm['id']}/start")
            st.rerun()

        if col2.button("Стоп", key=f"stop_{vm['id']}"):
            requests.post(f"{API_URL}/machines/{vm['id']}/stop")
            st.rerun()

        if col3.button("Удалить", key=f"delete_{vm['id']}"):
            requests.delete(f"{API_URL}/machines/{vm['id']}")
            st.rerun()

        st.code(f"ssh {vm['ssh_user']}@{vm['ssh_host']} -p {vm['ssh_port']}")


    st.subheader("Контейнеры")
    for c in containers:
        st.write(f"ID: {c['id']} | {c['os_name']} | {c['type']} | {c['status']}")
        col1, col2, col3 = st.columns(3)

        if col1.button("Старт", key=f"start_{c['id']}"):
            requests.post(f"{API_URL}/machines/{c['id']}/start")
            st.rerun()

        if col2.button("Стоп", key=f"stop_{c['id']}"):
            requests.post(f"{API_URL}/machines/{c['id']}/stop")
            st.rerun()

        if col3.button("Удалить", key=f"delete_{c['id']}"):
            requests.delete(f"{API_URL}/machines/{c['id']}")
            st.rerun()

        st.code(f"ssh {c['ssh_user']}@{c['ssh_host']} -p {c['ssh_port']}")