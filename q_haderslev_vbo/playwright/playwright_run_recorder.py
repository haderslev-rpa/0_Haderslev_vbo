from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
import asyncio

from playwright.async_api import Page, Browser, BrowserContext


@dataclass
class PlaywrightRunRecorder:
    debug: bool = False
    base_dir: Path = Path("test_local_playwright")

    run_dir: Optional[Path] = None
    record_context: Optional[BrowserContext] = None
    record_task: Optional[asyncio.Task] = None
    tracing_started: bool = False

    def __post_init__(self):
        self.base_dir.mkdir(exist_ok=True)
        if self.debug:
            self.run_dir = self._next_run_dir()
            self.run_dir.mkdir()

    def _next_run_dir(self) -> Path:
        runs = [p for p in self.base_dir.iterdir() if p.is_dir() and p.name.startswith("run_")]
        nums = []
        for r in runs:
            try:
                nums.append(int(r.name.replace("run_", "")))
            except ValueError:
                pass
        return self.base_dir / f"run_{max(nums, default=0)+1}"

    def _ts(self) -> str:
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    async def screenshot(self, page: Page, name: str) -> Path:
        target = self.run_dir or self.base_dir
        target.mkdir(exist_ok=True)
        path = target / f"{name}_{self._ts()}.png"
        await page.screenshot(path=str(path), full_page=True)
        return path

    async def start_recording(self, browser: Browser, timeout_seconds: int = 10) -> BrowserContext:
        target = self.run_dir or self.base_dir

        self.record_context = await browser.new_context(
            record_video_dir=str(target)
        )

        # Tracing er sekundært
        await self.record_context.tracing.start(
            screenshots=True,
            snapshots=True,
            sources=True
        )
        self.tracing_started = True

        self.record_task = asyncio.create_task(
            self._auto_stop(timeout_seconds)
        )

        return self.record_context

    async def stop_recording_clean(self, name: str):
        """Bruges kun når alt gik godt"""
        if not self.record_context:
            return

        if self.record_task and not self.record_task.done():
            self.record_task.cancel()

        if self.tracing_started:
            try:
                trace_path = (self.run_dir or self.base_dir) / f"{name}_trace.zip"
                await self.record_context.tracing.stop(path=str(trace_path))
            except Exception:
                pass

        await self.record_context.close()
        self.record_context = None

    async def stop_recording_on_error(self):
        """Bruges ved exception – VIDEO er vigtigst"""
        if not self.record_context:
            return

        # ❗ VIGTIGT: Ingen tracing.stop her
        await self.record_context.close()
        self.record_context = None

    async def _auto_stop(self, seconds: int):
        try:
            await asyncio.sleep(seconds)
            await self.stop_recording_clean("auto_timeout")
        except asyncio.CancelledError:
            pass