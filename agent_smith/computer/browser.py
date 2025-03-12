import asyncio
import base64
from typing import List, Dict, Literal
from playwright.async_api import async_playwright
from agents import ComputerTool, AsyncComputer

# Optional: key mapping if your model uses "CUA" style keys
CUA_KEY_TO_PLAYWRIGHT_KEY = {
    "/": "Divide",
    "\\": "Backslash",
    "alt": "Alt",
    "arrowdown": "ArrowDown",
    "arrowleft": "ArrowLeft",
    "arrowright": "ArrowRight",
    "arrowup": "ArrowUp",
    "backspace": "Backspace",
    "capslock": "CapsLock",
    "cmd": "Meta",
    "ctrl": "ControlOrMeta",
    "delete": "Delete",
    "end": "End",
    "enter": "Enter",
    "esc": "Escape",
    "home": "Home",
    "insert": "Insert",
    "option": "Alt",
    "pagedown": "PageDown",
    "pageup": "PageUp",
    "shift": "Shift",
    "space": " ",
    "super": "Meta",
    "tab": "Tab",
    "win": "Meta",
}


class HeadlessChromeBrowser(AsyncComputer):
    """
    A class for creating and managing a headless or headed Chrome browser using Playwright.
    This class provides functionality to create a Chrome browser instance with configurable
    headless mode. It inherits from BasePlaywrightComputer and overrides methods to customize
    browser behavior.

    Notes
    -----
    - The browser is launched with specific window dimensions defined in the parent class
    - Extensions and file system access are disabled for security
    """

    environment: Literal["browser"] = "browser"
    dimensions = (1024, 768)

    # def __init__(self):
    #     # self._playwright = async_playwright().start()
    #     # width, height = self.dimensions
    #     # launch_args = [
    #     #     f"--window-size={width},{height}",
    #     #     "--disable-extensions",
    #     #     "--disable-file-system",
    #     # ]
    #     # self._browser = self._playwright.chromium.launch(
    #     #     chromium_sandbox=True, headless=True, args=launch_args, env={}
    #     # )
    #     # self._page = self._browser.new_page()
    #     # self._page.set_viewport_size({"width": width, "height": height})
    #     # self._page.goto("about:blank")
    #     ...

    async def __aenter__(self):
        # Start Playwright and call the subclass hook for getting browser/page
        playwright_ctx = async_playwright()
        self._playwright = await playwright_ctx.start()
        width, height = self.dimensions
        launch_args = [
            f"--window-size={width},{height}",
            "--disable-extensions",
            "--disable-file-system",
        ]
        self._browser = await self._playwright.chromium.launch(
            chromium_sandbox=True, headless=True, args=launch_args, env={}
        )
        self._page = await self._browser.new_page()
        await self._page.set_viewport_size({"width": width, "height": height})
        await self._page.goto("https://google.com")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    def get_current_url(self) -> str:
        return self._page.url

    # --- Common "Computer" actions ---
    async def screenshot(self) -> str:
        """Capture only the viewport (not full_page)."""
        png_bytes = await self._page.screenshot(full_page=False)
        return base64.b64encode(png_bytes).decode("utf-8")

    async def click(self, x: int, y: int, button: str = "left") -> None:
        match button:
            case "back":
                await self.back()
            case "forward":
                await self.forward()
            case "wheel":
                await self._page.mouse.wheel(x, y)
            case _:
                button_mapping = {"left": "left", "right": "right"}
                button_type = button_mapping.get(button, "left")
                await self._page.mouse.click(x, y, button=button_type)

    async def double_click(self, x: int, y: int) -> None:
        await self._page.mouse.dblclick(x, y)

    async def scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        await self._page.mouse.move(x, y)
        await self._page.evaluate(f"window.scrollBy({scroll_x}, {scroll_y})")

    async def type(self, text: str) -> None:
        await self._page.keyboard.type(text)

    async def wait(self, ms: int = 1000) -> None:
        await asyncio.sleep(ms / 1000)

    async def move(self, x: int, y: int) -> None:
        await self._page.mouse.move(x, y)

    async def keypress(self, keys: List[str]) -> None:
        modifier_keys = []
        regular_keys = []

        for key in keys:
            mapped_key = CUA_KEY_TO_PLAYWRIGHT_KEY.get(key.lower(), key)
            if mapped_key in ["Control", "Alt", "Shift", "Meta", "ControlOrMeta"]:
                modifier_keys.append(mapped_key)
            else:
                regular_keys.append(mapped_key)

        # Press down all modifier keys first
        for modifier in modifier_keys:
            await self._page.keyboard.down(modifier)

        # Press and release regular keys
        for key in regular_keys:
            await self._page.keyboard.press(key)

        # Release all modifier keys
        for modifier in reversed(modifier_keys):
            await self._page.keyboard.up(modifier)

    async def drag(self, path: List[Dict[str, int]]) -> None:
        if not path:
            return
        await self._page.mouse.move(path[0]["x"], path[0]["y"])
        await self._page.mouse.down()
        for point in path[1:]:
            await self._page.mouse.move(point["x"], point["y"])
        await self._page.mouse.up()

    # --- Extra browser-oriented actions ---
    async def goto(self, url: str) -> None:
        try:
            await self._page.goto(url)
        except Exception as e:
            print(f"Error navigating to {url}: {e}")

    async def back(self) -> None:
        await self._page.go_back()

    async def forward(self) -> None:
        await self._page.go_forward()

    def as_tool(self):
        """
        Returns a ComputerTool instance for this browser.
        This method is used to create a tool that can be used in the agent's workflow.
        """
        return ComputerTool(computer=self)
