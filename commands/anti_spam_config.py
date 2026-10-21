import asyncio
import json
from collections import defaultdict, deque
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CONFIG_FILE = DATA_DIR / "anti_spam.json"


def load_config():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8")) if CONFIG_FILE.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_config(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


class AntiSpamConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.messages = defaultdict(deque)
        self.warned = set()
        self.lock = asyncio.Lock()

    @app_commands.command(name="anti-spam-config", description="Configura la detección básica de spam.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(activado="Activar o desactivar el anti-spam", limite="Mensajes permitidos en la ventana", ventana_segundos="Duración de la ventana en segundos")
    async def anti_spam_config(self, interaction: discord.Interaction, activado: bool, limite: app_commands.Range[int, 3, 15] = 5, ventana_segundos: app_commands.Range[int, 3, 30] = 8):
        data = load_config()
        data[str(interaction.guild_id)] = {"enabled": activado, "limit": limite, "window": ventana_segundos}
        save_config(data)
        status = "activado" if activado else "desactivado"
        await interaction.response.send_message(
            f"ROOTGHOST // ANTI-SPAM\nEstado: **{status}**\nLímite: **{limite} mensajes** en **{ventana_segundos} segundos**.\n"
            "La detección elimina mensajes excedentes cuando tiene permisos; no aplica sanciones automáticas.",
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return
        config = load_config().get(str(message.guild.id), {})
        if not config.get("enabled"):
            return
        if message.author.guild_permissions.manage_messages:
            return
        key = (message.guild.id, message.author.id, message.channel.id)
        now = message.created_at.timestamp()
        queue = self.messages[key]
        window = int(config.get("window", 8))
        while queue and now - queue[0] > window:
            queue.popleft()
        queue.append(now)
        if len(queue) > int(config.get("limit", 5)):
            try:
                await message.delete()
            except (discord.Forbidden, discord.HTTPException):
                pass
            warning_key = (message.guild.id, message.author.id)
            if warning_key not in self.warned:
                self.warned.add(warning_key)
                try:
                    await message.channel.send(
                        f"{message.author.mention}, bajá la velocidad de los mensajes.",
                        delete_after=5,
                        allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False)
                    )
                except discord.HTTPException:
                    pass
            queue.clear()

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        # Las ediciones no se cuentan como mensajes nuevos.
        return


async def setup(bot):
    await bot.add_cog(AntiSpamConfig(bot))
