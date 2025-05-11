"""
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import annotations

import logging
import pathlib
import shutil
import subprocess  # noqa: S404
from contextlib import contextmanager
from typing import Any, Generator

import requests


class Lavalink:
    """A minimal lavalink wrapper

    Minimal lavalink wrapper with context manager support.
    Auto check for and download newest lavalink jar.
    Will require you to have Java JDK v17+ installed (as of Lavalink v4).
    Since everything happens before bot is starting, every function is synchronous.

    Usage
    -----
    .. code-block:: python
        async with FurinaBot(...) as bot:
            with Lavalink().start():
                await bot.start(TOKEN)
    """
    def _get_release_info(self) -> dict[Any, Any]:
        response = requests.get(
            "https://api.github.com/repos/lavalink-devs/Lavalink/releases/latest",
            timeout=30
        )
        return response.json()

    @property
    def version(self) -> str | None:
        return self.release_info["tag_name"] or None

    @property
    def download_url(self) -> str | None:
        jar_info = next(
                (asset for asset in self.release_info["assets"] if asset["name"] == "Lavalink.jar"),
                None
            )
        return jar_info["browser_download_url"] if jar_info else None

    def check_for_update(self) -> None:
        lavalink = pathlib.Path(f"Lavalink-{self.version}.jar")
        if lavalink.exists():
            logging.info("Lavalink.jar is up-to-date (v%s). Skipping download...", self.version)
            return
        try:
            lavalink.unlink()
        except IndexError:
            pass
        logging.info("Deleted outdated Lavalink.jar file. Downloading new version...")
        response = requests.get(self.download_url, timeout=30)
        pathlib.Path(f"Lavalink-{self.version}.jar").write_bytes(response.content)
        logging.info("Successfully downloaded Lavalink.jar (v%s)", self.version)

    @contextmanager
    def start(self) -> Generator[None, Any, None]:
        self.release_info = self._get_release_info()
        if self.version is not None:
            self.check_for_update()
        logging.info("Starting Lavalink...")
        jar_path = pathlib.Path() / f'Lavalink-{self.version}.jar'
        java_path = shutil.which('java')
        if not java_path:
            raise FileNotFoundError(
                "Java executable not found in PATH." 
                "Please ensure Java is installed and added to PATH."
                "Or set SKIP_LL to True in settings.py"
            )
        # No security issue since everything is handled by the code itself
        process = subprocess.Popen([java_path, '-jar', str(jar_path)])  # noqa: S603
        try:
            yield
        finally:
            logging.info("Stopping Lavalink...")
            process.terminate()
            process.wait()