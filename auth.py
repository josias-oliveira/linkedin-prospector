import json
import os
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

SESSION_FILE = Path(".linkedin_session.json")


def session_exists() -> bool:
    return SESSION_FILE.exists() and SESSION_FILE.stat().st_size > 0


def clear_session():
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()


def load_session() -> dict:
    if session_exists():
        with open(SESSION_FILE) as f:
            return json.load(f)
    return {}


def save_session(cookies: list, storage: dict = None):
    data = {"cookies": cookies, "storage": storage or {}}
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f)


async def login_with_credentials(email: str, password: str) -> tuple[bool, str]:
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
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()

        try:
            await page.goto("https://www.linkedin.com/login", timeout=15000)
            await page.wait_for_load_state("networkidle", timeout=10000)

            await page.fill("#username", email)
            await asyncio.sleep(0.8)
            await page.fill("#password", password)
            await asyncio.sleep(0.6)
            await page.click('[type="submit"]')
            await asyncio.sleep(4)

            current_url = page.url

            # Verificação de CAPTCHA ou challenge
            if "checkpoint" in current_url or "challenge" in current_url:
                # Aguarda o usuário resolver manualmente
                await page.wait_for_url(
                    lambda u: "feed" in u or "mynetwork" in u,
                    timeout=120000,
                )

            if "feed" in page.url or "mynetwork" in page.url or "jobs" in page.url:
                cookies = await context.cookies()
                storage = await page.evaluate("() => JSON.stringify(window.localStorage)")
                save_session(cookies, {"localStorage": storage})
                await browser.close()
                return True, "ok"
            else:
                await browser.close()
                return False, page.url

        except Exception as e:
            await browser.close()
            return False, str(e)


async def login_manual() -> tuple[bool, str]:
    """Abre o browser para o usuário logar manualmente e salva a sessão."""
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
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()

        try:
            await page.goto("https://www.linkedin.com/login")
            # Aguarda até o feed aparecer (usuário loga manualmente)
            await page.wait_for_url(
                lambda u: "feed" in u or "mynetwork" in u or "jobs" in u,
                timeout=180000,  # 3 minutos
            )
            cookies = await context.cookies()
            storage = await page.evaluate("() => JSON.stringify(window.localStorage)")
            save_session(cookies, {"localStorage": storage})
            await browser.close()
            return True, "ok"

        except Exception as e:
            await browser.close()
            return False, str(e)


async def validate_session() -> tuple[bool, str]:
    """Verifica se a sessão salva ainda é válida."""
    if not session_exists():
        return False, "Sem sessão salva"

    session = load_session()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        await context.add_cookies(session["cookies"])
        page = await context.new_page()

        try:
            await page.goto("https://www.linkedin.com/feed/", timeout=15000)
            await asyncio.sleep(2)

            if "feed" in page.url or "mynetwork" in page.url:
                # Pega o nome do usuário logado
                name_el = await page.query_selector(".feed-identity-module__actor-meta .t-bold")
                name = (await name_el.inner_text()).strip() if name_el else "Usuário"
                await browser.close()
                return True, name
            else:
                await browser.close()
                return False, "Sessão expirada"

        except Exception as e:
            await browser.close()
            return False, str(e)
