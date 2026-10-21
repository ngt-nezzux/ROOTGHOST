import json
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

DATA = Path(__file__).resolve().parent.parent / "data" / "suggestion_config.json"


def load_config():
    try:
        return json.loads(DATA.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_config(data):
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


class SuggestionConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="suggestion-config", description="Elegir el canal para publicar sugerencias")
    @app_commands.describe(canal="Canal donde se publicarán las sugerencias")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def suggestion_config(self, interaction: discord.Interaction, canal: discord.TextChannel):
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("Necesitás Administrar servidor.", ephemeral=True)
        data = load_config()
        data[str(interaction.guild_id)] = {"channel_id": canal.id}
        save_config(data)
        await interaction.response.send_message(
            f"Canal de sugerencias configurado: {canal.mention}. Esta configuración solo se aplicará a comandos de sugerencias que lean `data/suggestion_config.json`.",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(SuggestionConfig(bot))
