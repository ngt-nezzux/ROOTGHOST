
import os
import logging
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
logging.basicConfig(level=logging.INFO)


class RootGhost(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()

        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):
        commands_dir = Path(__file__).parent / "commands"
        commands_dir.mkdir(exist_ok=True)

        for file in commands_dir.glob("*.py"):
            if file.name.startswith("_"):
                continue

            try:
                await self.load_extension(f"commands.{file.stem}")
                print(f"[ROOTGHOST] Cargado: {file.stem}")
            except Exception as error:
                print(f"[ROOTGHOST] Error en {file.stem}: {error}")

        synced = await self.tree.sync()
        print(f"[ROOTGHOST] {len(synced)} comandos sincronizados")

    async def on_ready(self):
        print(f"[ROOTGHOST] Conectado como {self.user}")


bot = RootGhost()


@bot.tree.command(
    name="hola",
    description="Saluda desde ROOTGHOST"
)
async def hola(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"ROOTGHOST está activo, {interaction.user.mention}."
    )


@bot.tree.command(
    name="ping",
    description="Comprueba la latencia"
)
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"ROOTGHOST | Latencia: {round(bot.latency * 1000)} ms"
    )


if not TOKEN:
    raise RuntimeError("Falta configurar DISCORD_TOKEN")


bot.run(TOKEN)
