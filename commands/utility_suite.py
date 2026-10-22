# ROOTGHOST // UTILITY SUITE
# discord.py 2.x | Extension para el cargador automatico commands/*.py
# Incluye reportes, auditoria, backup JSON, analiticas, encuestas y panel staff.
# Guardar como: commands/utility_suite.py

from __future__ import annotations
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_FILE = DATA_DIR / "utility_suite.json"
COLOR = 0x2ECC71


def now_utc():
    return datetime.now(timezone.utc)


def load_config():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {"guilds": {}}
    except (OSError, json.JSONDecodeError):
        return {"guilds": {}}


def save_config(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp = CONFIG_FILE.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    temp.replace(CONFIG_FILE)


def guild_config(guild_id):
    return load_config().setdefault("guilds", {}).get(str(guild_id), {})


def set_guild_config(guild_id, key, value):
    data = load_config()
    data.setdefault("guilds", {}).setdefault(str(guild_id), {})[key] = value
    save_config(data)


def make_embed(title, description=""):
    embed = discord.Embed(
        title=f"ROOTGHOST // {title}",
        description=description,
        color=COLOR,
        timestamp=now_utc(),
    )
    embed.set_footer(text="ROOTGHOST SECURITY SYSTEM")
    return embed


def can_manage(member):
    return member.guild_permissions.administrator or member.guild_permissions.manage_guild


class PollView(discord.ui.View):
    def __init__(self, question, options, creator_id):
        super().__init__(timeout=86400)
        self.question = question
        self.options = options
        self.creator_id = creator_id
        self.votes = {}
        self.closed = False
        for i, option in enumerate(options):
            button = discord.ui.Button(
                label=option[:80],
                style=discord.ButtonStyle.primary,
                custom_id=f"rgpoll_{id(self)}_{i}",
                row=i // 3,
            )
            button.callback = self.vote_callback(i)
            self.add_item(button)

    def vote_callback(self, index):
        async def callback(interaction: discord.Interaction):
            if self.closed:
                await interaction.response.send_message("La encuesta está cerrada.", ephemeral=True)
                return
            self.votes[interaction.user.id] = index
            await interaction.response.send_message(
                f"Voto registrado: **{self.options[index]}**.", ephemeral=True
            )
            await self.refresh(interaction)
        return callback

    async def refresh(self, interaction):
        message = interaction.message
        if message is None:
            return
        counts = [0] * len(self.options)
        for choice in self.votes.values():
            counts[choice] += 1
        total = len(self.votes)
        embed = make_embed(f"ENCUESTA // {self.question}")
        for option, count in zip(self.options, counts):
            percent = round(count * 100 / total) if total else 0
            blocks = percent // 10
            embed.add_field(
                name=option,
                value=f"{'█' * blocks}{'░' * (10 - blocks)} **{count}** voto(s) · {percent}%",
                inline=False,
            )
        embed.set_footer(text=f"ROOTGHOST SECURITY SYSTEM • {total} votante(s)")
        try:
            await message.edit(embed=embed, view=self)
        except discord.HTTPException:
            pass

    @discord.ui.button(
        label="Cerrar encuesta",
        style=discord.ButtonStyle.danger,
        custom_id="rgpoll_close",
        row=4,
    )
    async def close_poll(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user
        allowed = member.id == self.creator_id or (
            isinstance(member, discord.Member) and can_manage(member)
        )
        if not allowed:
            await interaction.response.send_message(
                "Solo quien creó la encuesta o el staff puede cerrarla.", ephemeral=True
            )
            return
        self.closed = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)


class UtilitySuite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rg-configurar-reportes", description="Configura el canal de reportes.")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def configure_reports(self, interaction: discord.Interaction, canal: discord.TextChannel):
        set_guild_config(interaction.guild_id, "report_channel_id", canal.id)
        await interaction.response.send_message(
            embed=make_embed("REPORTES CONFIGURADOS", f"Los reportes se enviarán a {canal.mention}."),
            ephemeral=True,
        )

    @app_commands.command(name="rg-reportar", description="Envía un reporte privado al staff.")
    @app_commands.guild_only()
    async def report(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        motivo: app_commands.Range[str, 10, 800],
        enlace: Optional[str] = None,
    ):
        config = guild_config(interaction.guild_id)
        channel_id = config.get("report_channel_id")
        channel = interaction.guild.get_channel(channel_id) if channel_id else None
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "El canal no está configurado. Un administrador debe usar `/rg-configurar-reportes`.",
                ephemeral=True,
            )
            return
        embed = make_embed("NUEVO REPORTE", f"**Motivo:** {motivo}")
        embed.add_field(name="Usuario reportado", value=f"{usuario.mention}\n`{usuario.id}`", inline=True)
        embed.add_field(name="Reportado por", value=f"{interaction.user.mention}\n`{interaction.user.id}`", inline=True)
        embed.add_field(name="Servidor", value=interaction.guild.name, inline=False)
        if enlace:
            embed.add_field(name="Enlace relacionado", value=enlace[:1000], inline=False)
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("No tengo permiso para enviar al canal configurado.", ephemeral=True)
            return
        await interaction.response.send_message("Reporte enviado al equipo de moderación.", ephemeral=True)

    @app_commands.command(name="rg-security-audit", description="Revisa permisos sensibles del servidor.")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def security_audit(self, interaction: discord.Interaction):
        guild = interaction.guild
        await interaction.response.defer(ephemeral=True, thinking=True)
        findings = []
        admin_roles = [
            role.name for role in guild.roles
            if not role.is_default() and not role.managed and role.permissions.administrator
        ]
        findings.append(
            "⚠️ **Roles con Administrador:** " + ", ".join(f"`{n}`" for n in admin_roles[:15])
            if admin_roles else "✅ No se detectaron roles personalizados con Administrador."
        )
        everyone = guild.default_role.permissions
        sensitive = []
        for attr, label in (
            ("mention_everyone", "Mencionar @everyone/@here"),
            ("manage_channels", "Gestionar canales"),
            ("manage_roles", "Gestionar roles"),
            ("administrator", "Administrador"),
        ):
            if getattr(everyone, attr):
                sensitive.append(label)
        findings.append(
            "⚠️ **Permisos sensibles en @everyone:** " + ", ".join(sensitive)
            if sensitive else "✅ @everyone no tiene los permisos sensibles comprobados."
        )
        if guild.me and guild.me.guild_permissions.administrator:
            findings.append("ℹ️ ROOTGHOST tiene Administrador; revisa si necesita todos esos permisos.")
        embed = make_embed("AUDITORÍA DE SEGURIDAD", "\n\n".join(findings))
        embed.add_field(
            name="Resumen",
            value=f"Roles: **{len(guild.roles)}** · Canales: **{len(guild.channels)}** · Miembros: **{guild.member_count or 'N/D'}**",
            inline=False,
        )
        embed.set_footer(text="ROOTGHOST SECURITY SYSTEM • Revisión orientativa, no exhaustiva")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="rg-config-backup", description="Exporta ajustes básicos del servidor en JSON.")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def config_backup(self, interaction: discord.Interaction):
        guild = interaction.guild
        await interaction.response.defer(ephemeral=True, thinking=True)
        payload = {
            "exported_at_utc": now_utc().isoformat(),
            "guild": {"id": guild.id, "name": guild.name},
            "roles": [
                {
                    "name": r.name, "color": r.color.value, "hoist": r.hoist,
                    "mentionable": r.mentionable, "permissions_value": r.permissions.value,
                    "position": r.position,
                }
                for r in reversed(guild.roles) if not r.managed
            ],
            "channels": [
                {
                    "name": c.name, "type": str(c.type),
                    "category": c.category.name if c.category else None,
                    "position": c.position, "topic": getattr(c, "topic", None),
                    "slowmode_delay": getattr(c, "slowmode_delay", None),
                }
                for c in guild.channels
            ],
            "settings": {
                "verification_level": str(guild.verification_level),
                "explicit_content_filter": str(guild.explicit_content_filter),
                "default_notifications": str(guild.default_notifications),
                "afk_timeout": guild.afk_timeout,
            },
            "note": "Exportación de referencia; no restaura todo automáticamente. No incluye tokens ni historial de mensajes.",
        }
        raw = io.BytesIO(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))
        file = discord.File(raw, filename=f"rootghost-backup-{guild.id}.json")
        await interaction.followup.send(
            "Copia de configuración generada. Guárdala de forma segura; no es una restauración completa.",
            file=file,
            ephemeral=True,
        )

    @app_commands.command(name="rg-server-analytics", description="Muestra estadísticas básicas del servidor.")
    @app_commands.guild_only()
    async def analytics(self, interaction: discord.Interaction):
        guild = interaction.guild
        members = guild.members
        bots = sum(member.bot for member in members)
        total = guild.member_count or len(members)
        embed = make_embed("SERVER ANALYTICS", f"**{guild.name}**")
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Miembros", value=str(total), inline=True)
        embed.add_field(name="Personas", value=str(max(total - bots, 0)), inline=True)
        embed.add_field(name="Bots en caché", value=str(bots), inline=True)
        embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="Canales de texto", value=str(sum(isinstance(c, discord.TextChannel) for c in guild.channels)), inline=True)
        embed.add_field(name="Canales de voz", value=str(sum(isinstance(c, discord.VoiceChannel) for c in guild.channels)), inline=True)
        embed.add_field(name="Categorías", value=str(sum(isinstance(c, discord.CategoryChannel) for c in guild.channels)), inline=True)
        embed.add_field(name="Creado", value=discord.utils.format_dt(guild.created_at, style="D"), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="rg-encuesta", description="Publica una encuesta con 2 a 5 opciones.")
    @app_commands.guild_only()
    async def poll(
        self,
        interaction: discord.Interaction,
        pregunta: app_commands.Range[str, 5, 180],
        opcion1: app_commands.Range[str, 1, 80],
        opcion2: app_commands.Range[str, 1, 80],
        opcion3: Optional[app_commands.Range[str, 1, 80]] = None,
        opcion4: Optional[app_commands.Range[str, 1, 80]] = None,
        opcion5: Optional[app_commands.Range[str, 1, 80]] = None,
    ):
        options = [s.strip() for s in (opcion1, opcion2, opcion3, opcion4, opcion5) if s and s.strip()]
        if len(set(s.casefold() for s in options)) != len(options):
            await interaction.response.send_message("No repitas opciones.", ephemeral=True)
            return
        view = PollView(pregunta, options, interaction.user.id)
        embed = make_embed(f"ENCUESTA // {pregunta}")
        for option in options:
            embed.add_field(name=option, value="░░░░░░░░░░ **0** voto(s) · 0%", inline=False)
        embed.set_footer(text="ROOTGHOST SECURITY SYSTEM • La encuesta finaliza en 24 horas")
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="rg-staff-panel", description="Muestra las herramientas del equipo.")
    @app_commands.guild_only()
    async def staff_panel(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member) or not can_manage(interaction.user):
            await interaction.response.send_message(
                "Acceso denegado: necesitas Gestionar servidor o Administrador.", ephemeral=True
            )
            return
        config = guild_config(interaction.guild_id)
        channel = interaction.guild.get_channel(config.get("report_channel_id", 0))
        report_destination = channel.mention if isinstance(channel, discord.TextChannel) else "Sin configurar"
        embed = make_embed("STAFF PANEL", "Centro rápido de herramientas de moderación.")
        embed.add_field(name="Canal de reportes", value=report_destination, inline=False)
        embed.add_field(
            name="Comandos",
            value=(
                "`/rg-reportar` — enviar reportes\n"
                "`/rg-configurar-reportes` — elegir canal\n"
                "`/rg-security-audit` — revisar permisos\n"
                "`/rg-config-backup` — exportar configuración\n"
                "`/rg-server-analytics` — estadísticas\n"
                "`/rg-encuesta` — crear encuesta"
            ),
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(UtilitySuite(bot))
