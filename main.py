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

import asyncio
import os
import logging
import sys

from aiohttp import ClientSession

from furina import FurinaBot
from settings import SKIP_LL, TOKEN


class LogFormatter(logging.Formatter):
    grey = '\x1b[38;21m'
    blue = '\x1b[38;5;39m'
    yellow = '\x1b[38;5;226m'
    red = '\x1b[38;5;196m'
    bold_red = '\x1b[31;1m'
    reset = '\x1b[0m'

    def __init__(self):
        super().__init__()
        self.FORMATS = {
            logging.DEBUG:    self.grey     + "%(asctime)s | %(levelname)8s" + self.reset + " | %(name)20s : %(message)s",
            logging.WARNING:  self.yellow   + "%(asctime)s | %(levelname)8s" + self.reset + " | %(name)20s : %(message)s",
            logging.ERROR:    self.red      + "%(asctime)s | %(levelname)8s" + self.reset + " | %(name)20s : %(message)s",
            logging.INFO:     self.blue     + "%(asctime)s | %(levelname)8s" + self.reset + " | %(name)20s : %(message)s",
            logging.CRITICAL: self.bold_red + "%(asctime)s | %(levelname)8s" + self.reset + " | %(name)20s : %(message)s"
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def handle_setup_logging() -> None:
    """Setup logging for the bot"""
    import logging.handlers
    file_handler = logging.handlers.RotatingFileHandler(
        filename="logs/furina.log",
        encoding="utf-8",
        maxBytes=32*1024*1024,
        backupCount=3
    )
    console_handler = logging.StreamHandler()
    file_handler.setFormatter(LogFormatter())
    console_handler.setFormatter(LogFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


async def main(skip_ll: bool) -> None:
    os.makedirs('logs', exist_ok=True)
    handle_setup_logging()
    async with ClientSession() as client_session:
        async with FurinaBot(client_session=client_session, skip_lavalink=skip_ll) as bot:
            await bot.start(TOKEN)


if __name__ == "__main__":
    skip_ll = True if ("--skip-ll" in sys.argv or SKIP_LL) else False
    asyncio.run(main(skip_ll))
