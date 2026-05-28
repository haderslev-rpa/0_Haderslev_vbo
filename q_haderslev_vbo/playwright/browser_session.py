# brug evt. Browser som output - så "Browser = BrowserSession"
# q_haderslev_vbo/playwright/browser_session.py
from playwright.async_api import async_playwright, Page, Error

class BrowserSession:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.pw = None
        self.browser = None
        self.context = None

    async def start(self):
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()

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

    async def close(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.pw:
            await self.pw.stop()
