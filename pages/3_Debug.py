import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from auth import session_exists, load_session
from playwright.async_api import async_playwright

st.set_page_config(page_title="Debug", page_icon="🔧", layout="wide")
st.title("🔧 Debug — Inspecionar página do LinkedIn")

if not session_exists():
    st.error("Conecte sua conta LinkedIn primeiro.")
    st.stop()

search_query = st.text_input("Termo de busca", value="CEO OR Founder")
col1, col2 = st.columns(2)
debug_btn = col1.button("Abrir browser e capturar página", type="primary")
stay_open = col2.checkbox("Manter browser aberto (30s)", value=True)

if debug_btn:
    session = load_session()
    screenshot_path = "/tmp/linkedin_debug.png"
    html_path = "/tmp/linkedin_debug.html"

    async def run_debug():
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 900},
            )
            await context.add_cookies(session["cookies"])
            page = await context.new_page()

            url = (
                "https://www.linkedin.com/search/results/people/"
                f"?keywords={search_query.replace(' ', '%20')}"
                "&origin=GLOBAL_SEARCH_HEADER"
            )
            await page.goto(url)
            await asyncio.sleep(4)
            await page.wait_for_load_state("networkidle", timeout=10000)

            # Screenshot
            await page.screenshot(path=screenshot_path, full_page=False)

            # HTML
            html = await page.content()
            with open(html_path, "w") as f:
                f.write(html)

            # Tenta extrair com o método atual
            extracted = await page.evaluate("""
                () => {
                    const results = [];
                    const containers = [
                        ...document.querySelectorAll('li.reusable-search__result-container'),
                        ...document.querySelectorAll('li.entity-result'),
                        ...document.querySelectorAll('[data-view-name="search-entity-result-universal-template"]'),
                    ];
                    for (const card of containers) {
                        const nameEl = (
                            card.querySelector('.entity-result__title-text a span[aria-hidden="true"]') ||
                            card.querySelector('a[href*="/in/"] span[aria-hidden]') ||
                            card.querySelector('.entity-result__title-text span[aria-hidden]')
                        );
                        results.push({
                            name: nameEl ? nameEl.innerText.trim() : '(sem nome)',
                            html_snippet: card.innerHTML.slice(0, 300),
                        });
                    }
                    return {
                        containers_found: containers.length,
                        results: results,
                        all_li: document.querySelectorAll('li').length,
                        page_url: window.location.href,
                    };
                }
            """)

            if stay_open:
                await asyncio.sleep(30)

            await browser.close()
            return extracted

    with st.spinner("Abrindo browser e capturando..."):
        data = asyncio.run(run_debug())

    # Resultados
    st.subheader("Resultado da extração")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Containers encontrados", data["containers_found"])
    col_b.metric("Total de <li> na página", data["all_li"])
    col_c.metric("Perfis com nome", sum(1 for r in data["results"] if r["name"] != "(sem nome)"))

    st.caption(f"URL: {data['page_url']}")

    # Screenshot
    st.subheader("Screenshot da página")
    st.image(screenshot_path)

    # Perfis extraídos
    if data["results"]:
        st.subheader("Perfis detectados")
        for r in data["results"]:
            st.markdown(f"- **{r['name']}**")
            with st.expander("HTML do card"):
                st.code(r["html_snippet"], language="html")
    else:
        st.warning("Nenhum container encontrado. Veja o screenshot e o HTML abaixo para entender a estrutura.")

    # HTML completo
    with st.expander("HTML completo da página (para debug)"):
        with open(html_path) as f:
            st.code(f.read()[:20000], language="html")
