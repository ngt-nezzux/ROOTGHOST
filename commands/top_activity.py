import json
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ACTIVITY_FILE = DATA_DIR / "top_activity.json"


def load_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        return json.loads(ACTIVITY_FILE.read_text(encoding="utf-8")) if ACTIVITY_FILE.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_data(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ACTIVITY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


class TopActivity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return
        data = load_data()
        guild_data = data.setdefault(str(message.guild.id), {})
        key = str(message.author.id)
        guild_data[key] = int(guild_data.get(key, 0)) + 1
        save_data(data)

    @app_commands.command(name="top-activity", description="Muestra el ranking de mensajes registrados por ROOTGHOST.")
    @app_commands.guild_only()
    async def top_activity(self, interaction: discord.Interaction):
        data = load_data().get(str(interaction.guild_id), {})
        ranked = sorted(data.items(), key=lambda item: item[1], reverse=True)[:10]
        embed = discord.Embed(title="ROOTGHOST // TOP ACTIVITY", color=0x5865F2)
        if not ranked:
            embed.description = "Todavía no hay actividad registrada. El conteo comienza cuando se instala este módulo."
        else:
            lines = []
            for pos, (user_id, count) in enumerate(ranked, 1):
                member = interaction.guild.get_member(int(user_id))
                label = member.display_name if member else f"Usuario {user_id}"
                lines.append(f"**{pos}.** {discord.utils.escape_markdown(label)} — `{count}` mensajes")
            embed.description = "\n".join(lines)
        embed.set_footer(text="Solo cuenta mensajes desde que se instaló este módulo.")
        await interaction.response.send_message(embed=embed, ephemeral=False)

async def setup(bot):
    await bot.add_cog(TopActivity(bot))
