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
    ram = st.slider("RAM (GB)", 1, 4)
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
        
    st.subheader("Машины")

    res = requests.get(f"{API_URL}/machines", params={
        "user_id": user["id"]
    })

    machines = res.json()

    for m in machines:
        st.write(f"ID: {m['id']} | {m['type']} | {m['status']}")
        col1, col2, col3 = st.columns(3)

        if col1.button("Старт", key=f"start_{m['id']}"):
            requests.post(f"{API_URL}/machines/{m['id']}/start")
            st.rerun()

        if col2.button("Стоп", key=f"stop_{m['id']}"):
            requests.post(f"{API_URL}/machines/{m['id']}/stop")
            st.rerun()

        if col3.button("Удалить", key=f"delete_{m['id']}"):
            requests.delete(f"{API_URL}/machines/{m['id']}")
            st.rerun()

        st.code(f"ssh {m['ssh_user']}@{m['ssh_host']} -p {m['ssh_port']}")