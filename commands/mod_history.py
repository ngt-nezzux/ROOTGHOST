import json
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
HISTORY_FILE = DATA_DIR / "mod_history.json"


def read_history():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8")) if HISTORY_FILE.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


def write_history(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def add_entry(guild_id, user_id, action, details=""):
    data = read_history()
    entries = data.setdefault(str(guild_id), {}).setdefault(str(user_id), [])
    entries.append({"action": action, "details": details[:300], "timestamp": discord.utils.utcnow().isoformat()})
    data[str(guild_id)][str(user_id)] = entries[-25:]
    write_history(data)


class ModHistory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mod-history", description="Consulta el historial de moderación registrado por ROOTGHOST.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mod_history(self, interaction: discord.Interaction, miembro: discord.Member):
        entries = read_history().get(str(interaction.guild_id), {}).get(str(miembro.id), [])
        embed = discord.Embed(title="ROOTGHOST // MODERATION HISTORY", color=0x5865F2)
        embed.description = f"Miembro: {miembro.mention}\nID: `{miembro.id}`"
        if not entries:
            embed.add_field(name="Sin registros", value="No hay eventos guardados por este módulo. No importa automáticamente casos históricos de otros comandos.", inline=False)
        else:
            for entry in entries[-10:][::-1]:
                embed.add_field(
                    name=f"{entry.get('action', 'Evento')} • {entry.get('timestamp', '')[:16].replace('T', ' ')}",
                    value=entry.get("details") or "Sin detalles",
                    inline=False
                )
        embed.set_footer(text="ROOTGHOST SECURITY SYSTEM")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        add_entry(guild.id, user.id, "Ban", "El evento de ban fue detectado. El motivo puede no estar disponible.")

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        add_entry(guild.id, user.id, "Unban", "El miembro fue desbaneado.")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.guild.id != after.guild.id:
            return
        if before.timed_out_until != after.timed_out_until:
            if after.timed_out_until:
                add_entry(after.guild.id, after.id, "Timeout", f"Fin: {after.timed_out_until.isoformat()}")
            elif before.timed_out_until:
                add_entry(after.guild.id, after.id, "Timeout finalizado", "Se retiró el timeout.")

async def setup(bot):
    await bot.add_cog(ModHistory(bot))
