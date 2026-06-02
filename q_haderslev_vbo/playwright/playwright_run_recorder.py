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
    debug: bool = False                            # bool (til/fra)
    base_dir: Path = Path("test_local_playwright") # Path (rodmappe)

    run_dir: Optional[Path] = None                 # Path (run-mappe)
    record_context: Optional[BrowserContext] = None# BrowserContext (optagelse)
    record_task: Optional[asyncio.Task] = None     # Task (timer)
    tracing_started: bool = False                  # bool (sikker stop)

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
    # Screenshot (drift + debug)
    # --------------------------------------------------
    async def screenshot(
        self,
        page: Page,
        name: str,
        full_page: bool = True
    ) -> Path:
        """
        Tager ét dokumentations-screenshot
        """

        target = self.run_dir or self.base_dir
        target.mkdir(exist_ok=True)

        safe = name.replace(" ", "_").replace("/", "_")
        path = target / f"{safe}_{self._ts()}.png"

        await page.screenshot(path=str(path), full_page=full_page)
        return path

    # --------------------------------------------------
    # Start optagelse (video + tracing)
    # --------------------------------------------------
    async def start_recording(
        self,
        browser: Browser,
        timeout_seconds: int = 10
    ) -> BrowserContext:
        """
        Starter midlertidig optagelse
        """

        target = self.run_dir or self.base_dir

        self.record_context = await browser.new_context(
            record_video_dir=str(target)
        )

        await self.record_context.tracing.start(
            screenshots=True,
            snapshots=True,
            sources=True
        )
        self.tracing_started = True

        self.record_task = asyncio.create_task(
            self._auto_stop_after(timeout_seconds)
        )

        return self.record_context

    # --------------------------------------------------
    # Stop optagelse (manuel / exception / auto)
    # --------------------------------------------------
    async def stop_recording(self, name: str):
        if not self.record_context:
            return

        if self.record_task and not self.record_task.done():
            self.record_task.cancel()

        if self.tracing_started:
            trace_path = (self.run_dir or self.base_dir) / f"{name}_trace.zip"
            await self.record_context.tracing.stop(path=str(trace_path))
            self.tracing_started = False

        await self.record_context.close()

        self.record_context = None
        self.record_task = None

    async def stop_recording_on_error(self, error: Exception):
        await self.stop_recording("exception")

    async def _auto_stop_after(self, seconds: int):
        try:
            await asyncio.sleep(seconds)
            await self.stop_recording("auto_timeout")
        except asyncio.CancelledError:
            pass