import json
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

DATA = Path(__file__).resolve().parent.parent / "data" / "report.json"


def load_config():
    try:
        return json.loads(DATA.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_config(data):
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


class Report(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="report", description="Reportar un miembro al equipo de moderación")
    @app_commands.describe(miembro="Miembro que querés reportar", motivo="Explicá brevemente qué ocurrió")
    @app_commands.guild_only()
    async def report(self, interaction: discord.Interaction, miembro: discord.Member, motivo: str):
        if miembro.id == interaction.user.id:
            return await interaction.response.send_message("No podés reportarte a vos mismo.", ephemeral=True)
        if miembro.bot:
            return await interaction.response.send_message("No se pueden reportar bots con este comando.", ephemeral=True)
        motivo = motivo.strip()
        if not motivo or len(motivo) > 800:
            return await interaction.response.send_message("El motivo debe tener entre 1 y 800 caracteres.", ephemeral=True)

        config = load_config().get(str(interaction.guild_id), {})
        channel_id = config.get("channel_id")
        channel = interaction.guild.get_channel(channel_id) if channel_id else None
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                "El canal de reportes no está configurado. Un administrador debe usar `/report-config`.",
                ephemeral=True,
            )

        embed = discord.Embed(title="ROOTGHOST // NUEVO REPORTE", color=0x5865F2)
        embed.add_field(name="Reportado", value=f"{miembro.mention}\n`{miembro.id}`", inline=True)
        embed.add_field(name="Reportado por", value=f"{interaction.user.mention}\n`{interaction.user.id}`", inline=True)
        embed.add_field(name="Canal", value=interaction.channel.mention if interaction.channel else "No disponible", inline=False)
        embed.add_field(name="Motivo", value=motivo, inline=False)
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text="ROOTGHOST SECURITY SYSTEM")
        try:
            await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        except discord.HTTPException:
            return await interaction.response.send_message("No pude enviar el reporte. Revisá mis permisos en el canal configurado.", ephemeral=True)
        await interaction.response.send_message("Tu reporte fue enviado al equipo de moderación.", ephemeral=True)

    @app_commands.command(name="report-config", description="Configurar el canal privado de reportes")
    @app_commands.describe(canal="Canal donde recibirá los reportes el staff")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def report_config(self, interaction: discord.Interaction, canal: discord.TextChannel):
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("Necesitás Administrar servidor.", ephemeral=True)
        data = load_config()
        data[str(interaction.guild_id)] = {"channel_id": canal.id}
        save_config(data)
        await interaction.response.send_message(f"Canal de reportes configurado: {canal.mention}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Report(bot))
