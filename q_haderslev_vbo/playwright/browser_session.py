from playwright.async_api import async_playwright, Page, Error
from datetime import datetime
import os
import subprocess


class BrowserSession:
    """
    BrowserSession (klasse – skabelon for objekt)
    Ansvar:
    - Starte Playwright
    - Starte browser og context
    - Finde run-navn og metadata
    - Ingen mapper, ingen filer
    """

    def __init__(self, headless: bool = True):
        self.headless = headless

        # Playwright objekter
        self.pw = None
        self.browser = None
        self.context = None

        # Run-metadata (i hukommelsen)
        self.github_repo_name: str | None = None
        self.session_id: str | None = None
        self.run_name: str | None = None
        self.run_timestamp: str | None = None

    # --------------------------------------------------
    # Start browser-session
    # --------------------------------------------------
    async def start(self):
        """
        Starter Playwright og browser
        Finder run-metadata
        """

        # Start Playwright
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()

        # Find metadata
        self.github_repo_name = self._find_github_repo_name()
        self.session_id = self._find_session_id()
        self.run_timestamp = self._generate_timestamp()
        self.run_name = self._generate_run_name()

    # --------------------------------------------------
    # Page-håndtering
    # --------------------------------------------------
    async def new_page(self) -> Page:
        return await self.context.new_page()

    async def ensure_page_alive(self, page: Page | None) -> Page:
        if page is None:
            return await self.new_page()

        try:
            await page.title()
            return page
        except Error:
            return await self.new_page()

    # --------------------------------------------------
    # Stop browser-session
    # --------------------------------------------------
    async def close(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.pw:
            await self.pw.stop()

    # ==================================================
    # METADATA (INTERNE HJÆLPERE)
    # ==================================================

    def _generate_timestamp(self) -> str:
        """
        Dansk dato + tid (lokal tid)
        Format: DD-MM-YYYY HH-MM
        """
        return datetime.now().strftime("%d-%m-%Y %H-%M")

    def _generate_run_name(self) -> str:
        """
        Sammensætter run-navn
        """
        if self.session_id:
            return f"{self.run_timestamp} (session {self.session_id})"
        return self.run_timestamp

    def _find_session_id(self) -> str | None:
        """
        Finder session-id fra Automation Server (env)
        """
        return os.getenv("AUTOMATION_SESSION_ID")

    def _find_github_repo_name(self) -> str:
        """
        Finder GitHub repo-navn
        Prioritet:
        1) ENV: GITHUB_REPO_NAME
        2) git config
        3) fallback
        """

        # 1. Environment variable
        env_name = os.getenv("GITHUB_REPO_NAME")
        if env_name:
            return env_name

        # 2. Git config
        try:
            result = subprocess.check_output(
                ["git", "config", "--get", "remote.origin.url"],
                stderr=subprocess.DEVNULL
            ).decode().strip()

            # Udtræk repo-navn
            repo = result.split("/")[-1].replace(".git", "")
            return repo
        except Exception:
            pass

        # 3. Fallback
        return "local-debug"