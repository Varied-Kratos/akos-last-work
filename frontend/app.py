import streamlit as st
from show import show_auth, show_dashboard

API_URL = "http://127.0.0.1:8000"


st.title("Аренда контейнеров и VM")
if "user" not in st.session_state:
    show_auth()
else:
    show_dashboard()

