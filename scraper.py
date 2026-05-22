import asyncio
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from playwright.async_api import async_playwright

SESSION_FILE = Path(__file__).parent / ".session.json"


@dataclass
class LinkedInProfile:
    name: str
    title: str
    company: str
    location: str
    about: str
    profile_url: str
    recent_post: str = ""


async def human_delay(min_s=1.5, max_s=3.5):
    await asyncio.sleep(random.uniform(min_s, max_s))


class LinkedInScraper:
    def __init__(self, log: Callable[[str], None] = print):
        self.log = log
        self._playwright = None
        self.browser = None
        self.page = None

    async def start(self):
        cookies = json.loads(SESSION_FILE.read_text())
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(headless=False)
        context = await self.browser.new_context()
        await context.add_cookies(cookies)
        self.page = await context.new_page()
        self.log("Browser iniciado.")

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def search_profiles(
        self,
        keywords: str,
        location: str = "",
        max_results: int = 20,
    ) -> list[LinkedInProfile]:
        profiles = []

        from urllib.parse import quote
        url = (
            "https://www.linkedin.com/search/results/people/"
            f"?keywords={quote(keywords)}"
            "&origin=GLOBAL_SEARCH_HEADER"
        )
        if location:
            geo_param = '["' + location + '"]'
            url += f"&geoUrn={quote(geo_param)}"

        self.log(f"URL: {url}")
        await self.page.goto(url)
        await asyncio.sleep(4)  # aguarda a página renderizar

        page_num = 1
        while len(profiles) < max_results:
            self.log(f"Lendo página {page_num}...")
            await asyncio.sleep(2)  # aguarda conteúdo dinâmico

            extracted = await self.page.evaluate("""
                () => {
                    const results = [];
                    const seen = new Set();

                    // Pega todos os links de perfil da página
                    const links = [...document.querySelectorAll('a[href*="/in/"]')];

                    for (const link of links) {
                        const href = link.getAttribute('href') || '';
                        const full = href.split('?')[0];
                        const profileUrl = full.replace('https://www.linkedin.com', '');

                        // Ignora links sem /in/ válido ou já vistos
                        if (!profileUrl || profileUrl === '/in/' || seen.has(profileUrl)) continue;

                        // Nome: innerText do link, remove grau de conexão e pega só 1ª linha
                        let name = (link.innerText || '')
                            .replace(/[•·]\s*(1st|2nd|3rd\+?)/gi, '')
                            .split('\\n')[0]
                            .trim();
                        if (!name || name.length < 2) continue;
                        seen.add(profileUrl);

                        // Sobe até o <li> pai para pegar cargo e localização
                        let li = link.parentElement;
                        while (li && li.tagName !== 'LI') li = li.parentElement;
                        if (!li) { results.push({name, profileUrl, title:'', company:'', location:''}); continue; }

                        // Pega linhas de texto do card (exclui o nome e textos muito curtos)
                        const lines = li.innerText
                            .split('\\n')
                            .map(l => l.trim())
                            .filter(l => l.length > 2 && l !== name && !l.includes('Connect') && !l.includes('Follow') && !l.includes('connections') && !l.includes('followers') && !l.includes('mutual'));

                        const title    = lines[0] || '';
                        const location = lines[1] || '';
                        // Empresa aparece em "Current: X at Company" ou "Past: X at Company"
                        const companyLine = lines.find(l => l.startsWith('Current:') || l.startsWith('Past:')) || '';
                        const company = companyLine.replace(/^(Current|Past):\s*/, '').replace(/^.+ at /, '') || '';

                        results.push({ name, profileUrl, title, company, location });
                    }
                    return results;
                }
            """)

            self.log(f"  → {len(extracted)} perfis encontrados")

            for item in extracted:
                if len(profiles) >= max_results:
                    break
                if item["name"]:
                    profiles.append(LinkedInProfile(
                        name=item["name"],
                        title=item["title"],
                        company=item["company"],
                        location=item["location"],
                        about="",
                        profile_url=item["profileUrl"],
                    ))

            if len(profiles) >= max_results:
                break

            next_btn = await self.page.query_selector(
                'button[aria-label="Avançar"], button[aria-label="Next"]'
            )
            if not next_btn:
                self.log("Sem mais páginas.")
                break

            await next_btn.click()
            await asyncio.sleep(3)
            page_num += 1

        self.log(f"Total: {len(profiles)} perfis.")
        return profiles

    async def enrich_profile(self, profile: LinkedInProfile) -> LinkedInProfile:
        if not profile.profile_url:
            return profile

        url = profile.profile_url
        if not url.startswith("http"):
            url = f"https://www.linkedin.com{url}"

        await self.page.goto(url)
        await asyncio.sleep(3)

        about = await self.page.evaluate("""
            () => {
                const el = document.querySelector('#about ~ .pvs-list__outer-container .visually-hidden')
                    || document.querySelector('section[data-section="summary"] span');
                return el ? el.innerText.trim().slice(0, 500) : '';
            }
        """)
        if about:
            profile.about = about

        return profile
