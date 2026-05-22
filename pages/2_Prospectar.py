import asyncio
import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pyperclip
import streamlit as st
from scraper import LinkedInScraper, SESSION_FILE
from generator import generate_message
from database import init_db, save_prospect, update_status, update_messages, get_all_prospects, clear_all_prospects

init_db()

st.set_page_config(page_title="Prospectar", page_icon="🔍", layout="wide")

if not SESSION_FILE.exists():
    st.error("Conecte sua conta LinkedIn primeiro.")
    if st.button("Conectar →", type="primary"):
        st.switch_page("pages/1_Conectar_LinkedIn.py")
    st.stop()

# ── Sidebar ────────────────────────────────────────────────────────────────────
CARGOS_PRESET = ["CEO", "Founder", "Dono", "CTO", "COO", "Diretor", "Presidente"]
FORMACOES_PRESET = ["MBA", "PhD", "Mestrado", "Doutorado", "Pós-graduação", "Harvard", "FGV", "USP"]

# geoUrn IDs oficiais do LinkedIn por país
LOCALIZACOES = {
    "🇧🇷 Brasil":          "106057199",
    "🇺🇸 Estados Unidos":  "103644278",
    "🇬🇧 Reino Unido":     "101165590",
    "🇵🇹 Portugal":        "100364837",
    "🇦🇷 Argentina":       "100446943",
    "🇨🇴 Colômbia":        "100876405",
    "🇲🇽 México":          "103323778",
    "🇨🇱 Chile":           "104621616",
    "🇩🇪 Alemanha":        "101282230",
    "🇫🇷 França":          "105015875",
    "🇪🇸 Espanha":         "105646813",
    "🌍 Qualquer lugar":   "",
}

with st.sidebar:
    st.header("Busca")

    selecionados = st.multiselect(
        "Cargo",
        options=CARGOS_PRESET,
        default=["CEO", "Founder", "Dono"],
    )
    cargo_extra = st.text_input("Outro cargo", placeholder="Ex: VP, Partner...")

    st.divider()
    st.markdown("**Formação acadêmica** _(opcional)_")
    formacoes = st.multiselect(
        "Formação",
        options=FORMACOES_PRESET,
        default=[],
        label_visibility="collapsed",
    )
    formacao_extra = st.text_input("Outra formação", placeholder="Ex: Insper, Stanford...")

    # Monta a query: cargos + formações combinados
    termos_cargo = selecionados + ([cargo_extra.strip()] if cargo_extra.strip() else [])
    termos_formacao = formacoes + ([formacao_extra.strip()] if formacao_extra.strip() else [])

    cargo_query = " OR ".join(termos_cargo) if termos_cargo else "CEO"
    if termos_formacao:
        search_query = f"({cargo_query}) ({' OR '.join(termos_formacao)})"
    else:
        search_query = cargo_query

    st.caption(f"Buscando: `{search_query}`")

    st.divider()
    loc_label = st.selectbox("Localização", options=list(LOCALIZACOES.keys()), index=0)
    search_location = LOCALIZACOES[loc_label]
    max_results = st.slider("Máximo de perfis", 5, 50, 10)
    enrich = st.checkbox("Visitar cada perfil", value=False,
                         help="Extrai mais dados mas é mais lento")
    st.divider()
    st.header("Mensagem")
    tone = st.selectbox("Tom", ["direto", "formal", "consultivo"])
    run_btn = st.button("Buscar", type="primary", use_container_width=True)

# ── Busca ──────────────────────────────────────────────────────────────────────
st.title("Prospectar")

if run_btn:
    progress = st.progress(0, text="Iniciando...")
    log_box = st.empty()
    log_lines = []

    def log(msg):
        log_lines.append(msg)
        log_box.code("\n".join(log_lines[-10:]))

    async def run():
        scraper = LinkedInScraper(log=log)
        await scraper.start()
        progress.progress(20, text="Buscando perfis...")

        profiles = await scraper.search_profiles(
            keywords=search_query,
            location=search_location,
            max_results=max_results,
        )

        results = []
        for i, profile in enumerate(profiles):
            pct = 20 + int(75 * (i + 1) / max(len(profiles), 1))
            progress.progress(pct, text=f"Processando {profile.name}...")
            log(f"✓ {profile.name} — {profile.title} @ {profile.company}")

            if enrich:
                profile = await scraper.enrich_profile(profile)

            messages = generate_message(profile, tone=tone)
            save_prospect(profile, messages)
            results.append((profile, messages))

        await scraper.stop()
        return results

    results = asyncio.run(run())
    progress.progress(100, text="Pronto!")
    log_box.empty()

    if results:
        st.success(f"{len(results)} perfis encontrados!")
    else:
        st.warning("Nenhum perfil encontrado. Tente outros termos de busca.")

# ── Prospects ──────────────────────────────────────────────────────────────────
col_titulo, col_zerar = st.columns([4, 1])
col_titulo.subheader("Prospects salvos")

with col_zerar:
    if st.button("🗑️ Zerar", use_container_width=True):
        st.session_state["confirmar_zerar"] = True

if st.session_state.get("confirmar_zerar"):
    st.warning("Tem certeza? Isso apaga **todos** os prospects salvos.")
    c1, c2 = st.columns(2)
    if c1.button("Sim, apagar tudo", type="primary", use_container_width=True):
        clear_all_prospects()
        for key in list(st.session_state.keys()):
            if key.startswith(("short_", "long_", "loaded_")):
                del st.session_state[key]
        st.session_state["confirmar_zerar"] = False
        st.toast("Todos os prospects foram apagados.")
        st.rerun()
    if c2.button("Cancelar", use_container_width=True):
        st.session_state["confirmar_zerar"] = False
        st.rerun()

prospects = get_all_prospects()

if not prospects:
    st.info("Nenhum prospect ainda. Configure a busca e clique em 'Buscar'.")
else:
    STATUS = ["novo", "contatado", "respondeu", "reunião", "descartado"]
    BADGE = {"novo": "🔵", "contatado": "🟡", "respondeu": "🟢", "reunião": "🟣", "descartado": "⚫"}

    filtro = st.selectbox("Filtrar", ["todos"] + STATUS)
    lista = prospects if filtro == "todos" else [p for p in prospects if p["status"] == filtro]

    for p in lista:
        badge = BADGE.get(p["status"], "⚪")
        with st.expander(f"{badge} **{p['name']}** — {p['title']} @ {p['company']}"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Local:** {p['location']}")
                if p.get("about"):
                    st.markdown(f"**Sobre:** {p['about'][:200]}...")
                if p.get("profile_url"):
                    url = p["profile_url"]
                    if not url.startswith("http"):
                        url = f"https://www.linkedin.com{url}"
                    st.link_button("Ver no LinkedIn", url)

                novo_status = st.selectbox("Status", STATUS,
                    index=STATUS.index(p["status"]) if p["status"] in STATUS else 0,
                    key=f"s_{p['id']}")
                if novo_status != p["status"]:
                    update_status(p["profile_url"], novo_status)
                    st.rerun()

            with col2:
                sk = f"short_{p['id']}"
                lk = f"long_{p['id']}"

                # Só inicializa se ainda não existe OU se foi explicitamente
                # regenerado para este perfil (marcado em session_state)
                if f"loaded_{p['id']}" not in st.session_state:
                    st.session_state[sk] = p.get("short_message") or ""
                    st.session_state[lk] = p.get("long_message") or ""
                    st.session_state[f"loaded_{p['id']}"] = True

                # Regenerar — só para este perfil
                if st.button("🔄 Regenerar", key=f"regen_{p['id']}", use_container_width=True):
                    from scraper import LinkedInProfile
                    obj = LinkedInProfile(name=p["name"], title=p["title"],
                                         company=p["company"], location=p["location"],
                                         about=p.get("about") or "", profile_url=p["profile_url"])
                    msgs = generate_message(obj, tone=tone)
                    st.session_state[sk] = msgs["short_message"]
                    st.session_state[lk] = msgs["long_message"]
                    update_messages(p["profile_url"], msgs["short_message"], msgs["long_message"])
                    st.toast(f"Mensagem de {p['name'].split()[0]} regenerada!")

                # Mensagem curta
                chars = len(st.session_state.get(sk, ""))
                cor = "red" if chars > 300 else "green"
                st.markdown(f"**Mensagem de conexão** <span style='color:{cor}'>{chars}/300</span>",
                            unsafe_allow_html=True)
                st.text_area("", key=sk, height=90, label_visibility="collapsed")
                if st.button("📋 Copiar mensagem curta", key=f"copy_short_{p['id']}", use_container_width=True):
                    pyperclip.copy(st.session_state[sk])
                    st.toast("Copiado!")

                # Mensagem longa
                st.markdown("**Mensagem longa**")
                st.text_area("", key=lk, height=200, label_visibility="collapsed")
                if st.button("📋 Copiar mensagem longa", key=f"copy_long_{p['id']}", use_container_width=True):
                    pyperclip.copy(st.session_state[lk])
                    st.toast("Copiado!")
