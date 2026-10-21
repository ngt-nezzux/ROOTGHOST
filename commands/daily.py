import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

DATA = Path(__file__).resolve().parent.parent / "data" / "daily.json"
REWARD = 100


def load_data():
    try:
        return json.loads(DATA.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_data(data):
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    @app_commands.command(name="daily", description="Reclamar una recompensa virtual diaria")
    @app_commands.guild_only()
    async def daily(self, interaction: discord.Interaction):
        guild_data = self.data.setdefault(str(interaction.guild_id), {})
        profile = guild_data.setdefault(str(interaction.user.id), {"coins": 0, "last_claim": None})
        now = datetime.now(timezone.utc)
        last = datetime.fromisoformat(profile["last_claim"]) if profile["last_claim"] else None
        if last and now < last + timedelta(hours=24):
            remaining = last + timedelta(hours=24) - now
            hours, rem = divmod(int(remaining.total_seconds()), 3600)
            minutes = rem // 60
            return await interaction.response.send_message(
                f"Ya reclamaste tu recompensa. Volvé en **{hours} h {minutes} min**.", ephemeral=True
            )
        profile["coins"] += REWARD
        profile["last_claim"] = now.isoformat()
        save_data(self.data)
        embed = discord.Embed(title="ROOTGHOST // DAILY REWARD", description=f"Recibiste **{REWARD} RG Coins**.", color=0x5865F2)
        embed.add_field(name="Saldo de este sistema", value=f"{profile['coins']} RG Coins")
        embed.set_footer(text="Esta economía es independiente de otros sistemas del bot.")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Daily(bot))
