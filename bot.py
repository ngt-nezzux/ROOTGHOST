import os
import discord
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")



class RootGhost(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        synced = await self.tree.sync()
        print(f"[ROOTGHOST] {len(synced)} comandos sincronizados")

    async def on_ready(self):
        print(f"[ROOTGHOST] Conectado como {self.user}")


bot = RootGhost()


@bot.tree.command(name="hola", description="Saluda desde ROOTGHOST")
async def hola(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"ROOTGHOST está activo, {interaction.user.mention}."
    )


@bot.tree.command(name="ping", description="Comprueba la latencia")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"ROOTGHOST | Latencia: {round(bot.latency * 1000)} ms"
    )


if not TOKEN:
    raise RuntimeError("Falta configurar DISCORD_TOKEN")

bot.run(TOKEN)
