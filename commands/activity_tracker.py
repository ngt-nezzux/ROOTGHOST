from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord.ext import commands

log = logging.getLogger("ROOTGHOST.activity")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ACTIVITY_FILE = DATA_DIR / "activity.json"


class ActivityTracker(commands.Cog):
    """Cuenta mensajes nuevos por servidor y usuario y los guarda en data/activity.json."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.lock = __import__("asyncio").Lock()

    def _read_data(self) -> dict:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not ACTIVITY_FILE.exists():
            return {}
        try:
            with ACTIVITY_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            log.exception("No se pudo leer %s", ACTIVITY_FILE)
            return {}

    def _write_data(self, data: dict) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        temp_file = ACTIVITY_FILE.with_suffix(".json.tmp")
        with temp_file.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        temp_file.replace(ACTIVITY_FILE)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # Solo mensajes normales de usuarios en servidores; ignora bots y DMs.
        if message.guild is None or message.author.bot or message.webhook_id is not None:
            return

        guild_id = str(message.guild.id)
        user_id = str(message.author.id)
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        day = datetime.now(timezone.utc).date().isoformat()

        async with self.lock:
            data = self._read_data()
            guild_data = data.setdefault(guild_id, {})
            user_data = guild_data.setdefault(
                user_id,
                {"messages": 0, "daily": {}, "last_message": None}
            )

            user_data["messages"] = int(user_data.get("messages", 0)) + 1
            daily = user_data.setdefault("daily", {})
            daily[day] = int(daily.get(day, 0)) + 1
            user_data["last_message"] = now

            try:
                self._write_data(data)
            except OSError:
                log.exception("No se pudo guardar la actividad en %s", ACTIVITY_FILE)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ActivityTracker(bot))
