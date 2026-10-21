from __future__ import annotations

import json
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

BASE_DIR = Path(__file__).resolve().parent.parent
ACTIVITY_FILE = BASE_DIR / "data" / "activity.json"


class TopActivity(commands.Cog):
    """Muestra el ranking de mensajes registrados por ROOTGHOST."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _load_data(self) -> dict:
        if not ACTIVITY_FILE.exists():
            return {}
        try:
            with ACTIVITY_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    @app_commands.command(
        name="top-activity",
        description="Muestra el ranking de actividad registrada en este servidor."
    )
    @app_commands.guild_only()
    async def top_activity(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "Este comando solo funciona dentro de un servidor.",
                ephemeral=True
            )
            return

        data = self._load_data()
        guild_data = data.get(str(interaction.guild.id), {})

        if not isinstance(guild_data, dict) or not guild_data:
            await interaction.response.send_message(
                "Todavía no hay actividad registrada. El conteo comienza cuando "
                "ROOTGHOST está conectado y el módulo de actividad está cargado.",
                ephemeral=True
            )
            return

        rows = []
        for user_id, stats in guild_data.items():
            if not isinstance(stats, dict):
                continue
            try:
                count = max(0, int(stats.get("messages", 0)))
                member_id = int(user_id)
            except (TypeError, ValueError):
                continue
            if count > 0:
                rows.append((member_id, count))

        rows.sort(key=lambda item: item[1], reverse=True)
        rows = rows[:10]

        if not rows:
            await interaction.response.send_message(
                "Todavía no hay mensajes contabilizados. Escriban algunos mensajes "
                "y volvé a ejecutar el comando.",
                ephemeral=True
            )
            return

        lines = []
        for position, (member_id, count) in enumerate(rows, start=1):
            member = interaction.guild.get_member(member_id)
            name = member.display_name if member else f"Usuario {member_id}"
            lines.append(f"**{position}.** {discord.utils.escape_markdown(name)} — **{count:,}** mensajes")

        embed = discord.Embed(
            title="ROOTGHOST // TOP ACTIVITY",
            description="\n".join(lines),
            color=discord.Color.dark_teal()
        )
        embed.set_footer(text="ROOTGHOST SECURITY SYSTEM • Actividad desde la instalación")
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TopActivity(bot))
