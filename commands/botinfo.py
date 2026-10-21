import platform
import time

import discord
from discord import app_commands
from discord.ext import commands


class BotInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.started_at = time.time()

    @app_commands.command(name="botinfo", description="Ver información técnica de ROOTGHOST")
    async def botinfo(self, interaction: discord.Interaction):
        latency_ms = round(self.bot.latency * 1000) if self.bot.latency is not None else 0
        uptime = max(0, int(time.time() - self.started_at))
        days, rem = divmod(uptime, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        embed = discord.Embed(title="ROOTGHOST // SYSTEM INFORMATION", color=0x5865F2)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url if self.bot.user else discord.Embed.Empty)
        embed.add_field(name="Versión de discord.py", value=discord.__version__, inline=True)
        embed.add_field(name="Python", value=platform.python_version(), inline=True)
        embed.add_field(name="Latencia", value=f"{latency_ms} ms", inline=True)
        embed.add_field(name="Tiempo activo", value=f"{days}d {hours}h {minutes}m {seconds}s", inline=True)
        embed.add_field(name="Servidores", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Comandos slash", value=str(len(self.bot.tree.get_commands())), inline=True)
        embed.set_footer(text="ROOTGHOST SYSTEMS")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(BotInfo(bot))
