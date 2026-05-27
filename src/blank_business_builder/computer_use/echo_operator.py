"""
Echo Operator
=============
Echo's full computer-use capability stack — the local equivalent of
OpenAI Operator + Claude Desktop Controller.

Capabilities:
  - Browser automation  (Playwright headless Chromium)
  - Desktop control     (PyAutoGUI + xdotool on Linux VPS)
  - Screen vision       (Qwen2.5-VL:3b via Ollama — reads screenshots)
  - Action loop         (screenshot → vision → decide → act → repeat)

Architecture mirrors Claude Computer Use:
    loop:
        screenshot  →  vision model sees it
        vision      →  action plan (click, type, scroll, navigate)
        action      →  executed via Playwright / PyAutoGUI
        result      →  fed back into next loop tick

Install on VPS:
    pip install playwright pyautogui pillow
    playwright install chromium
    ollama pull qwen2.5-vl:3b     # vision model

Usage:
    from blank_business_builder.computer_use.echo_operator import EchoOperator

    echo = EchoOperator()
    result = await echo.browse("Go to apollo.io and find 5 SaaS CEOs")
    result = await echo.execute_task("Fill out the contact form at example.com/contact")
"""
from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Action schema ────────────────────────────────────────────────────────────

@dataclass
class Action:
    type: str          # "click" | "type" | "navigate" | "scroll" | "screenshot" | "done"
    selector: str = ""
    text: str = ""
    url: str = ""
    x: int = 0
    y: int = 0
    scroll_y: int = 0
    reason: str = ""

@dataclass
class OperatorResult:
    task: str
    success: bool
    steps: List[str] = field(default_factory=list)
    extracted_data: List[Dict] = field(default_factory=list)
    error: Optional[str] = None
    duration_seconds: float = 0.0
    screenshots_taken: int = 0


# ── Vision helper ────────────────────────────────────────────────────────────

class ScreenVision:
    """
    Uses Qwen2.5-VL (or any Ollama vision model) to understand screenshots
    and decide what action to take next.
    """

    def __init__(
        self,
        vps_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self.vps_url = (vps_url or os.getenv("HERMES_VPS_URL", "http://localhost:11434")).rstrip("/")
        self.model = model or os.getenv("VISION_MODEL", "qwen2.5-vl:3b")

    def analyze(self, screenshot_bytes: bytes, task: str, history: List[str]) -> Action:
        """
        Send screenshot to vision model and get next action.
        Returns an Action dataclass.
        """
        import urllib.request

        img_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
        history_text = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(history[-5:]))

        prompt = (
            f"You are controlling a browser to complete this task:\n{task}\n\n"
            f"Steps taken so far:\n{history_text or '  (none yet)'}\n\n"
            f"Look at the screenshot and decide the NEXT single action.\n"
            f"Respond ONLY in this JSON format:\n"
            f'{{"type":"click|type|navigate|scroll|done","selector":"css-selector-or-empty",'
            f'"text":"text-to-type-or-empty","url":"url-if-navigating-or-empty",'
            f'"x":0,"y":0,"scroll_y":0,"reason":"why this action"}}'
        )

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                    ],
                }
            ],
            "max_tokens": 256,
            "stream": False,
        }

        try:
            req = urllib.request.Request(
                f"{self.vps_url}/v1/chat/completions",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
            raw = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
            clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            d = json.loads(clean)
            return Action(**{k: d.get(k, v) for k, v in Action.__dataclass_fields__.items()})
        except Exception as exc:
            logger.warning("Vision analysis failed: %s", exc)
            return Action(type="done", reason=f"Vision unavailable: {exc}")

    def extract_data(self, screenshot_bytes: bytes, instruction: str) -> str:
        """Extract specific data from a screenshot (names, emails, prices, etc.)"""
        import urllib.request

        img_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
        payload = {
            "model": self.model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Extract the following from this screenshot: {instruction}\nReturn JSON array."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                ],
            }],
            "max_tokens": 512,
            "stream": False,
        }
        try:
            req = urllib.request.Request(
                f"{self.vps_url}/v1/chat/completions",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
            return (data.get("choices") or [{}])[0].get("message", {}).get("content", "[]")
        except Exception as exc:
            return f"[]"


# ── Browser automation ────────────────────────────────────────────────────────

class BrowserAgent:
    """
    Headless Chromium browser controlled by Playwright.
    Handles navigation, clicking, typing, scrolling, and screenshots.
    """

    def __init__(self) -> None:
        self._playwright = None
        self._browser = None
        self._page = None

    async def start(self, headless: bool = True) -> None:
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=headless,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
            )
            self._page = await self._browser.new_page(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            logger.info("Browser started (headless=%s)", headless)
        except ImportError:
            raise RuntimeError("playwright not installed — run: pip install playwright && playwright install chromium")

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def screenshot(self) -> bytes:
        if not self._page:
            raise RuntimeError("Browser not started")
        return await self._page.screenshot(type="png", full_page=False)

    async def execute(self, action: Action) -> str:
        """Execute a single action and return status string."""
        if not self._page:
            return "browser not started"
        try:
            if action.type == "navigate":
                await self._page.goto(action.url, wait_until="domcontentloaded", timeout=15000)
                return f"navigated to {action.url}"
            elif action.type == "click":
                if action.selector:
                    await self._page.click(action.selector, timeout=5000)
                else:
                    await self._page.mouse.click(action.x, action.y)
                return f"clicked {action.selector or f'({action.x},{action.y})'}"
            elif action.type == "type":
                if action.selector:
                    await self._page.fill(action.selector, action.text)
                else:
                    await self._page.keyboard.type(action.text)
                return f"typed '{action.text[:40]}'"
            elif action.type == "scroll":
                await self._page.mouse.wheel(0, action.scroll_y)
                return f"scrolled {action.scroll_y}px"
            elif action.type == "screenshot":
                return "screenshot taken"
            elif action.type == "done":
                return f"done: {action.reason}"
            else:
                return f"unknown action: {action.type}"
        except Exception as exc:
            return f"action failed: {exc}"

    @property
    def current_url(self) -> str:
        return self._page.url if self._page else ""


# ── Desktop control ───────────────────────────────────────────────────────────

class DesktopAgent:
    """
    OS-level control via PyAutoGUI (cross-platform) + xdotool (Linux VPS).
    Used for native app automation beyond the browser.
    """

    def screenshot(self) -> bytes:
        try:
            import pyautogui
            img = pyautogui.screenshot()
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
        except Exception as exc:
            raise RuntimeError(f"Screenshot failed (is DISPLAY set?): {exc}")

    def click(self, x: int, y: int) -> str:
        try:
            import pyautogui
            pyautogui.click(x, y)
            return f"clicked ({x}, {y})"
        except Exception as exc:
            # Fall back to xdotool on Linux
            return self._xdotool(f"mousemove {x} {y} click 1")

    def type_text(self, text: str) -> str:
        try:
            import pyautogui
            pyautogui.typewrite(text, interval=0.03)
            return f"typed '{text[:40]}'"
        except Exception:
            return self._xdotool(f"type '{text}'")

    def _xdotool(self, cmd: str) -> str:
        import subprocess
        try:
            subprocess.run(["xdotool"] + cmd.split(), check=True, capture_output=True)
            return f"xdotool: {cmd}"
        except FileNotFoundError:
            return "xdotool not available — install with: apt install xdotool"
        except subprocess.CalledProcessError as exc:
            return f"xdotool failed: {exc}"


# ── Echo Operator (puts it all together) ─────────────────────────────────────

class EchoOperator:
    """
    The full Echo Operator — local equivalent of OpenAI Operator.

    Combines:
    - BrowserAgent   (Playwright headless Chromium)
    - DesktopAgent   (PyAutoGUI / xdotool)
    - ScreenVision   (Qwen2.5-VL vision model via Ollama)
    - Hermes brain   (decides what to do at each step)

    Example tasks:
        "Go to linkedin.com and collect 10 SaaS CEO profiles"
        "Sign up for a free trial at tool.com using email test@bbb.ai"
        "Find the pricing page of competitor.com and extract all plan prices"
        "Fill out the contact form at prospect.com and submit"
    """

    MAX_STEPS = 25  # safety limit per task

    def __init__(
        self,
        vision_model: Optional[str] = None,
        vps_url: Optional[str] = None,
    ) -> None:
        self.vision   = ScreenVision(vps_url=vps_url, model=vision_model)
        self.browser  = BrowserAgent()
        self.desktop  = DesktopAgent()
        self._started = False

    # ── browser tasks ────────────────────────────────────────────────────────

    async def browse(
        self,
        task: str,
        start_url: Optional[str] = None,
        extract: Optional[str] = None,
        max_steps: int = MAX_STEPS,
    ) -> OperatorResult:
        """
        Run a browser task using the vision→action loop.
        Optionally extract structured data (e.g. "company names and emails").
        """
        t0 = time.time()
        result = OperatorResult(task=task, success=False)

        await self._ensure_browser()

        # Start navigation
        if start_url:
            await self.browser.execute(Action(type="navigate", url=start_url, reason="initial navigation"))
            result.steps.append(f"Navigated to {start_url}")

        for step in range(max_steps):
            # Screenshot
            try:
                shot = await self.browser.screenshot()
                result.screenshots_taken += 1
            except Exception as exc:
                result.error = f"Screenshot failed: {exc}"
                break

            # Vision: what should we do next?
            action = self.vision.analyze(shot, task, result.steps)
            logger.info("Step %d: %s — %s", step + 1, action.type, action.reason[:60])

            if action.type == "done":
                result.success = True
                result.steps.append(f"Done: {action.reason}")
                # Extract data from final screenshot if requested
                if extract:
                    raw = self.vision.extract_data(shot, extract)
                    try:
                        result.extracted_data = json.loads(raw)
                    except Exception:
                        result.extracted_data = [{"raw": raw}]
                break

            # Execute action
            status = await self.browser.execute(action)
            result.steps.append(f"Step {step+1} [{action.type}]: {status}")
            await asyncio.sleep(0.8)  # brief pause for page loads

        result.duration_seconds = round(time.time() - t0, 2)
        return result

    async def execute_task(self, task: str, max_steps: int = MAX_STEPS) -> OperatorResult:
        """High-level task execution — vision loop with no pre-set URL."""
        return await self.browse(task, max_steps=max_steps)

    # ── desktop tasks ────────────────────────────────────────────────────────

    def desktop_task(self, task: str, max_steps: int = 10) -> OperatorResult:
        """
        Synchronous desktop control loop (OS-level, outside browser).
        Uses PyAutoGUI + xdotool for native app automation.
        """
        t0 = time.time()
        result = OperatorResult(task=task, success=False)

        for step in range(max_steps):
            try:
                shot = self.desktop.screenshot()
                result.screenshots_taken += 1
            except Exception as exc:
                result.error = str(exc)
                break

            action = self.vision.analyze(shot, task, result.steps)
            if action.type == "done":
                result.success = True
                result.steps.append(f"Done: {action.reason}")
                break

            if action.type == "click":
                status = self.desktop.click(action.x, action.y)
            elif action.type == "type":
                status = self.desktop.type_text(action.text)
            else:
                status = f"skipped {action.type} (desktop mode)"

            result.steps.append(f"Step {step+1}: {status}")
            time.sleep(0.5)

        result.duration_seconds = round(time.time() - t0, 2)
        return result

    # ── convenience wrappers ─────────────────────────────────────────────────

    async def find_leads(self, criteria: str, count: int = 5) -> List[Dict]:
        """
        Use the browser to find leads on LinkedIn / Crunchbase / Apollo.
        Returns list of extracted contact dicts.
        """
        task = (
            f"Search LinkedIn or Crunchbase for {count} people matching: {criteria}. "
            f"Collect their name, title, company, and LinkedIn URL."
        )
        result = await self.browse(
            task,
            start_url="https://www.linkedin.com/search/results/people/",
            extract="name, title, company, linkedin_url",
        )
        return result.extracted_data or []

    async def check_competitor(self, url: str) -> Dict:
        """Visit a competitor's site and extract pricing + key features."""
        result = await self.browse(
            f"Find the pricing page and extract all plan names, prices, and features.",
            start_url=url,
            extract="plan_name, price, features",
        )
        return {"url": url, "data": result.extracted_data, "steps": result.steps}

    async def submit_form(self, url: str, fields: Dict[str, str]) -> OperatorResult:
        """Navigate to a URL and fill + submit a form with given field values."""
        field_desc = ", ".join(f"{k}='{v}'" for k, v in fields.items())
        task = f"Fill and submit the form at {url}. Fields: {field_desc}"
        return await self.browse(task, start_url=url)

    # ── lifecycle ────────────────────────────────────────────────────────────

    async def _ensure_browser(self) -> None:
        if not self._started:
            await self.browser.start(headless=True)
            self._started = True

    async def close(self) -> None:
        if self._started:
            await self.browser.stop()
            self._started = False

    async def __aenter__(self):
        await self._ensure_browser()
        return self

    async def __aexit__(self, *_):
        await self.close()
