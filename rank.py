import json
import time
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

DATA = Path(__file__).resolve().parent.parent / "data" / "rank.json"
COOLDOWN = 60


def load_data():
    try:
        return json.loads(DATA.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_data(data):
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(data, indent=2), encoding="utf-8")


class Rank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.last_xp = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild or not message.content.strip():
            return
        key = f"{message.guild.id}:{message.author.id}"
        now = time.time()
        if now - self.last_xp.get(key, 0) < COOLDOWN:
            return
        self.last_xp[key] = now
        profile = self.data.setdefault(str(message.guild.id), {}).setdefault(
            str(message.author.id), {"xp": 0, "messages": 0}
        )
        profile["xp"] += 5
        profile["messages"] += 1
        save_data(self.data)

    @app_commands.command(name="rank", description="Ver el nivel y la experiencia de un miembro")
    @app_commands.describe(miembro="Miembro a consultar (opcional)")
    @app_commands.guild_only()
    async def rank(self, interaction: discord.Interaction, miembro: discord.Member = None):
        member = miembro or interaction.user
        profile = self.data.get(str(interaction.guild_id), {}).get(str(member.id), {"xp": 0, "messages": 0})
        xp = int(profile["xp"])
        level = int((xp / 100) ** 0.5)
        current_level_xp = level * level * 100
        next_level_xp = (level + 1) ** 2 * 100
        embed = discord.Embed(title="ROOTGHOST // USER RANK", color=0x5865F2)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Miembro", value=member.mention, inline=False)
        embed.add_field(name="Nivel", value=str(level), inline=True)
        embed.add_field(name="XP", value=f"{xp:,}", inline=True)
        embed.add_field(name="Mensajes contabilizados", value=f"{profile['messages']:,}", inline=True)
        embed.add_field(name="Progreso", value=f"{xp - current_level_xp}/{next_level_xp - current_level_xp} XP para el siguiente nivel", inline=False)
        embed.set_footer(text="ROOTGHOST COMMUNITY SYSTEM")
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        # La persistencia se guarda tras cada mensaje que da XP.
        pass


async def setup(bot):
    await bot.add_cog(Rank(bot))
