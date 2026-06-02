from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
import asyncio  # async styring (vent / tasks)

from playwright.async_api import Page, Browser, BrowserContext


# ==================================================
# PLAYWRIGHT RUN RECORDER
# ==================================================
@dataclass
class PlaywrightRunRecorder:
    debug: bool = False                              # bool (til/fra)
    base_dir: Path = Path("test_local_playwright")   # Path (rodmappe)

    run_dir: Optional[Path] = None                   # Path (run-mappe)
    record_context: Optional[BrowserContext] = None  # BrowserContext (optagelse)
    record_task: Optional[asyncio.Task] = None       # Task (baggrunds-timer)

    # --------------------------------------------------
    # Init (kører ved oprettelse)
    # --------------------------------------------------
    def __post_init__(self):
        self.base_dir.mkdir(exist_ok=True)

        if self.debug:
            self.run_dir = self._next_run_dir()
            self.run_dir.mkdir()

    # --------------------------------------------------
    # Interne hjælpefunktioner
    # --------------------------------------------------
    def _next_run_dir(self) -> Path:
        existing = [
            p for p in self.base_dir.iterdir()
            if p.is_dir() and p.name.startswith("run_")
        ]

        numbers = []
        for folder in existing:
            try:
                numbers.append(int(folder.name.replace("run_", "")))
            except ValueError:
                pass

        next_number = max(numbers, default=0) + 1
        return self.base_dir / f"run_{next_number}"

    def _ts(self) -> str:
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # --------------------------------------------------
    # Screenshot (bruges i drift OG debug)
    # --------------------------------------------------
    async def screenshot(
        self,
        page: Page,
        name: str,
        full_page: bool = True
    ) -> Path:
        """
        Tager et enkelt screenshot (dokumentation)
        """

        target_dir = self.run_dir or self.base_dir
        target_dir.mkdir(exist_ok=True)

        safe = name.replace(" ", "_").replace("/", "_")
        path = target_dir / f"{safe}_{self._ts()}.png"

        await page.screenshot(path=str(path), full_page=full_page)
        return path

    # --------------------------------------------------
    # START OPTAGELSE (video + tracing)
    # --------------------------------------------------
    async def start_recording(
        self,
        browser: Browser,
        timeout_seconds: int = 10
    ) -> BrowserContext:
        """
        Starter en midlertidig optagelse (video + tracing)
        """

        target_dir = self.run_dir or self.base_dir
        video_dir = target_dir / "video"
        video_dir.mkdir(exist_ok=True)

        # Opret separat context (browser-miljø)
        self.record_context = await browser.new_context(
            record_video_dir=str(video_dir)
        )

        # Start tracing (Playwright standard)
        await self.record_context.tracing.start(
            screenshots=True,
            snapshots=True,
            sources=True
        )

        # Start automatisk stop-timer
        self.record_task = asyncio.create_task(
            self._auto_stop_after(timeout_seconds)
        )

        return self.record_context

    # --------------------------------------------------
    # STOP OPTAGELSE (manuel)
    # --------------------------------------------------
    async def stop_recording(self, name: str = "recording"):
        """
        Stopper optagelse manuelt og gemmer video + trace
        """

        if not self.record_context:
            return

        # Stop timer-task hvis den kører
        if self.record_task and not self.record_task.done():
            self.record_task.cancel()

        # Stop tracing
        trace_path = (self.run_dir or self.base_dir) / f"{name}_trace.zip"
        await self.record_context.tracing.stop(path=str(trace_path))

        # Luk context → video gemmes automatisk
        await self.record_context.close()

        self.record_context = None
        self.record_task = None

    # --------------------------------------------------
    # Automatisk stop efter timeout
    # --------------------------------------------------
    async def _auto_stop_after(self, seconds: int):
        """
        Stopper optagelse automatisk efter X sekunder
        """
        try:
            await asyncio.sleep(seconds)
            await self.stop_recording(name="auto_timeout")
        except asyncio.CancelledError:
            pass

    # --------------------------------------------------
    # Bruges i exception-handling
    # --------------------------------------------------
    async def stop_recording_on_error(self, error: Exception):
        """
        Stopper optagelse hvis der sker en fejl
        """
        await self.stop_recording(name="exception")