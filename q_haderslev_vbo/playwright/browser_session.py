# brug evt. Browser som output - så "Browser = BrowserSession"
# q_haderslev_vbo/playwright/browser_session.py
from playwright.sync_api import sync_playwright, Page, Error

# starter Playwright infrastruktur, starter en browser proces, opretter en browser context

class BrowserSession:
    """
    Denne skal bruges således:
    browser = BrowserSession(headless=True)
    page = None
    """
    def __init__(self, headless: bool = True):
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(headless=headless)
        self.context = self.browser.new_context()

    # Opretter en ny browser fane. Deler cookies, login og session
    def new_page(self) -> Page:
        return self.context.new_page()

    # Sikrer at page stadig er brugbar – ellers oprettes en ny
    def ensure_page_alive(self, page: Page | None) -> Page:
        if page is None:
            return self.new_page()

        try:
            # Billig sanity-check: fejler hvis siden er lukket/crashet
            page.title()
            return page
        except Error:
            return self.new_page()

    # lukker alt i korrekt rækkefølge
    def close(self):
        self.context.close()
        self.browser.close()
        self.pw.stop()