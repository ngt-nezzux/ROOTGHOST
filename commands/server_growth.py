import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands, tasks

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
GROWTH_FILE = DATA_DIR / "server_growth.json"


def load_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        return json.loads(GROWTH_FILE.read_text(encoding="utf-8")) if GROWTH_FILE.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_data(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    GROWTH_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


class ServerGrowth(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sample_growth.start()

    def cog_unload(self):
        self.sample_growth.cancel()

    @tasks.loop(hours=24)
    async def sample_growth(self):
        await self.bot.wait_until_ready()
        data = load_data()
        today = datetime.now(timezone.utc).date().isoformat()
        changed = False
        for guild in self.bot.guilds:
            records = data.setdefault(str(guild.id), [])
            if not records or records[-1].get("date") != today:
                records.append({"date": today, "members": guild.member_count or 0})
                data[str(guild.id)] = records[-180:]
                changed = True
        if changed:
            save_data(data)

    @sample_growth.before_loop
    async def before_sample_growth(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="server-growth", description="Consulta el historial de miembros registrado por ROOTGHOST.")
    @app_commands.guild_only()
    async def server_growth(self, interaction: discord.Interaction):
        records = load_data().get(str(interaction.guild_id), [])
        embed = discord.Embed(title="ROOTGHOST // SERVER GROWTH", color=0x5865F2)
        if len(records) < 2:
            embed.description = "Todavía no hay suficientes registros. ROOTGHOST necesita recopilar al menos dos muestras diarias."
        else:
            first, latest = records[0], records[-1]
            delta = int(latest["members"]) - int(first["members"])
            sign = "+" if delta > 0 else ""
            embed.add_field(name="Miembros actuales registrados", value=str(latest["members"]), inline=True)
            embed.add_field(name="Cambio desde el primer registro", value=f"{sign}{delta}", inline=True)
            embed.add_field(name="Período registrado", value=f"{first['date']} → {latest['date']}", inline=False)
            embed.add_field(name="Muestras", value=str(len(records)), inline=True)
        embed.set_footer(text="Los datos empiezan a recopilarse al instalar este módulo; no hay historial anterior.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ServerGrowth(bot))
