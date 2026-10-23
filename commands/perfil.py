import json
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

BASE_DIR = Path(__file__).resolve().parent.parent
RANK_FILE = BASE_DIR / "data" / "rank.json"
ECONOMY_FILE = BASE_DIR / "data" / "economia.json"
MONEDA = "GhostCoins"


def read_json(path):
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


class Perfil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="perfil",
        description="Muestra el perfil social, nivel y economía de un miembro."
    )
    @app_commands.describe(miembro="Miembro cuyo perfil quieres consultar")
    @app_commands.guild_only()
    async def perfil(
        self,
        interaction: discord.Interaction,
        miembro: discord.Member = None
    ):
        member = miembro or interaction.user
        guild_id = str(interaction.guild_id)
        user_id = str(member.id)

        # Experiencia y actividad
        ranks = read_json(RANK_FILE)
        profile = ranks.get(guild_id, {}).get(
            user_id, {"xp": 0, "messages": 0}
        )

        xp = max(0, int(profile.get("xp", 0)))
        messages = max(0, int(profile.get("messages", 0)))
        level = int((xp / 100) ** 0.5)
        current_xp = level ** 2 * 100
        next_xp = (level + 1) ** 2 * 100
        progress = xp - current_xp
        needed = next_xp - current_xp
        percentage = min(100, int(progress / needed * 100)) if needed else 100
        bar_filled = percentage // 10
        progress_bar = "█" * bar_filled + "░" * (10 - bar_filled)

        # Economía: lectura del archivo existente, sin modificar cuentas
        economy = read_json(ECONOMY_FILE)
        users = economy.get("users", {})
        account = users.get(user_id, {}) if isinstance(users, dict) else {}

        wallet = max(0, int(account.get("balance", 0)))
        bank = max(0, int(account.get("bank", 0)))
        total = wallet + bank

        # Fechas de Discord
        created = int(member.created_at.timestamp())
        joined = (
            int(member.joined_at.timestamp())
            if member.joined_at else None
        )

        embed = discord.Embed(
            title="ROOTGHOST // PERFIL DE USUARIO",
            description=f"Perfil de {member.mention}",
            color=0x5865F2,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(
            name="IDENTIDAD",
            value=(
                f"**Usuario:** {discord.utils.escape_markdown(member.display_name)}\n"
                f"**ID:** `{member.id}`\n"
                f"**Cuenta creada:** <t:{created}:D>\n"
                f"**Ingreso al servidor:** "
                f"{f'<t:{joined}:D>' if joined else 'No disponible'}"
            ),
            inline=False
        )

        embed.add_field(
            name="RANGO Y ACTIVIDAD",
            value=(
                f"**Nivel:** `{level}`\n"
                f"**Experiencia:** `{xp:,} XP`\n"
                f"**Mensajes contabilizados:** `{messages:,}`\n"
                f"**Progreso:** `{progress:,}/{needed:,} XP` ({percentage}%)\n"
                f"`{progress_bar}`"
            ),
            inline=False
        )

        embed.add_field(
            name="ECONOMÍA",
            value=(
                f"**Billetera:** `{wallet:,} {MONEDA}`\n"
                f"**Banco:** `{bank:,} {MONEDA}`\n"
                f"**Patrimonio:** `{total:,} {MONEDA}`"
            ),
            inline=False
        )

        embed.set_footer(text="ROOTGHOST COMMUNITY SYSTEM")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Perfil(bot))
