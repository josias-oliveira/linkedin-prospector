import asyncio
import sys
import os
import json
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from playwright.async_api import async_playwright

SESSION_FILE = Path(__file__).parent.parent / ".session.json"

st.set_page_config(page_title="Conectar LinkedIn", page_icon="🔗", layout="centered")
st.title("🔗 Conectar LinkedIn")

# ── Status ────────────────────────────────────────────────────────────────────
if SESSION_FILE.exists():
    st.success("Conta conectada! Vá para **Prospectar** no menu ao lado.")
    if st.button("Desconectar"):
        SESSION_FILE.unlink()
        st.rerun()
    st.stop()

# ── Formulário de login ───────────────────────────────────────────────────────
st.markdown("Entre com sua conta do LinkedIn:")

email = st.text_input("Email")
senha = st.text_input("Senha", type="password")
entrar = st.button("Entrar", type="primary", use_container_width=True)

if entrar:
    if not email or not senha:
        st.error("Preencha email e senha.")
        st.stop()

    st.info("O browser vai abrir. Se aparecer verificação em duas etapas, resolva lá e aguarde.")

    async def fazer_login():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()

            await page.goto("https://www.linkedin.com/login")
            await asyncio.sleep(2)

            url_atual = page.url

            # Já estava logado — redirecionou direto pro feed
            if "feed" in url_atual or "mynetwork" in url_atual:
                cookies = await page.context.cookies()
                SESSION_FILE.write_text(json.dumps(cookies))
                await browser.close()
                return True

            # Preenche login normalmente
            await page.fill("#username", email)
            await page.fill("#password", senha)
            await page.click('[type="submit"]')

            # Aguarda feed (até 2 minutos, tempo para resolver 2FA)
            try:
                await page.wait_for_url(
                    lambda u: "feed" in u or "mynetwork" in u,
                    timeout=120_000,
                )
            except Exception:
                await browser.close()
                return False

            cookies = await page.context.cookies()
            SESSION_FILE.write_text(json.dumps(cookies))
            await browser.close()
            return True

    with st.spinner("Fazendo login..."):
        ok = asyncio.run(fazer_login())

    if ok:
        st.success("Conectado com sucesso!")
        st.rerun()
    else:
        st.error("Não conseguiu conectar. Tente de novo.")
