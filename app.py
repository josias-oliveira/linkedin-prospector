import streamlit as st
from pathlib import Path

st.set_page_config(page_title="LinkedIn Prospector", page_icon="🔍", layout="centered")
st.title("LinkedIn Prospector")

SESSION_FILE = Path(".session.json")

if SESSION_FILE.exists():
    st.success("Conta conectada.")
    st.page_link("pages/2_Prospectar.py", label="Ir para Prospectar →", icon="🔍")
else:
    st.warning("Nenhuma conta conectada.")
    st.page_link("pages/1_Conectar_LinkedIn.py", label="Conectar LinkedIn →", icon="🔗")
