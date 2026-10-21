
import json
from pathlib import Path
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LOG_FILE = DATA_DIR / "modlogs.json"


def read_logs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        return []
    try:
        return json.loads(LOG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def record_log(guild_id, user_id, action, moderator_id=None, reason=None):
    logs = read_logs()
    logs.append({
        "guild_id": guild_id,
        "user_id": user_id,
        "action": action,
        "moderator_id": moderator_id,
        "reason": reason or "Sin motivo especificado",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    # Limitar el tamaño del archivo.
    logs = logs[-5000:]

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text(
        json.dumps(logs, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


class ModLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        moderator_id = None
        reason = None

        try:
            async for entry in guild.audit_logs(
                limit=6, action=discord.AuditLogAction.ban
            ):
                if entry.target and entry.target.id == user.id:
                    moderator_id = entry.user.id if entry.user else None
                    reason = entry.reason
                    break
        except discord.Forbidden:
            pass

        record_log(
            guild.id, user.id, "BAN",
            moderator_id, reason
        )

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        record_log(guild.id, user.id, "UNBAN")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # Diferenciar una salida voluntaria de una expulsión
        # requiere consultar el registro de auditoría.
        try:
            async for entry in member.guild.audit_logs(
                limit=6, action=discord.AuditLogAction.kick
            ):
                if (
                    entry.target
                    and entry.target.id == member.id
                    and (discord.utils.utcnow() - entry.created_at).total_seconds() < 15
                ):
                    record_log(
                        member.guild.id,
                        member.id,
                        "KICK",
                        entry.user.id if entry.user else None,
                        entry.reason
                    )
                    return
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        old_timeout = before.timed_out_until
        new_timeout = after.timed_out_until

        if old_timeout == new_timeout:
            return

        if new_timeout is not None:
            record_log(
                after.guild.id,
                after.id,
                "TIMEOUT",
                reason=f"Hasta {new_timeout.isoformat()}"
            )
        elif old_timeout is not None:
            record_log(
                after.guild.id,
                after.id,
                "TIMEOUT REMOVED"
            )

    @app_commands.command(
        name="modlogs",
        description="Consulta el historial de moderación."
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(
        usuario="Usuario cuyo historial querés consultar."
    )
    async def modlogs(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member = None
    ):
        logs = [
            entry for entry in read_logs()
            if entry["guild_id"] == interaction.guild.id
            and (
                usuario is None
                or entry["user_id"] == usuario.id
            )
        ]

        logs = logs[-10:][::-1]

        embed = discord.Embed(
            title="ROOTGHOST // MODERATION LOGS",
            color=0x5865F2,
            timestamp=discord.utils.utcnow()
        )

        if not logs:
            embed.description = "No hay registros para mostrar."
        else:
            for entry in logs:
                timestamp = entry.get("timestamp", "")
                try:
                    date = datetime.fromisoformat(timestamp).strftime(
                        "%d/%m/%Y %H:%M UTC"
                    )
                except ValueError:
                    date = "Fecha desconocida"

                user_id = entry["user_id"]
                moderator_id = entry.get("moderator_id")
                moderator = (
                    f"<@{moderator_id}>"
                    if moderator_id else "No identificado"
                )

                embed.add_field(
                    name=f"{entry['action']} — {date}",
                    value=(
                        f"Usuario: <@{user_id}> (`{user_id}`)\n"
                        f"Moderador: {moderator}\n"
                        f"Motivo: {entry.get('reason') or 'Sin motivo'}"
                    )[:1024],
                    inline=False
                )

        embed.set_footer(text="ROOTGHOST SECURITY SYSTEM")

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(ModLogs(bot))
