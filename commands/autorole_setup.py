
import json
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_FILE = DATA_DIR / "autorole.json"
COLOR = 0x2ECC71


def load_config():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data.setdefault("guilds", {})
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return {"guilds": {}}


def save_config(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp = CONFIG_FILE.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    temp.replace(CONFIG_FILE)


def get_role_ids(guild_id):
    config = load_config().get("guilds", {}).get(str(guild_id), {})
    ids = config.get("role_ids")

    # Compatibilidad con la configuración antigua de un solo rol.
    if ids is None:
        old_id = config.get("role_id")
        ids = [old_id] if old_id else []

    return list(dict.fromkeys(int(role_id) for role_id in ids))


def set_role_ids(guild_id, role_ids):
    data = load_config()
    guilds = data.setdefault("guilds", {})
    key = str(guild_id)

    if role_ids:
        guilds[key] = {
            "role_ids": list(dict.fromkeys(role_ids))
        }
    else:
        guilds.pop(key, None)

    save_config(data)


def make_embed(title, description=""):
    embed = discord.Embed(
        title=f"ROOTGHOST // {title}",
        description=description,
        color=COLOR,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_footer(text="ROOTGHOST SECURITY SYSTEM")
    return embed


def validate_role(guild, role):
    bot_member = guild.me

    if role.is_default() or role.managed:
        return "Ese rol no se puede usar como autorol."

    if bot_member is None:
        return "No pude verificar los permisos del bot."

    if not bot_member.guild_permissions.manage_roles:
        return "Necesito el permiso Gestionar roles."

    if role >= bot_member.top_role:
        return "Mi rol más alto debe estar por encima del rol elegido."

    return None


class AutoRoleSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="autorol-configurar",
        description="Agrega un rol a la asignación automática.",
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles=True)
    async def autorol_configurar(
        self,
        interaction: discord.Interaction,
        rol: discord.Role,
    ):
        guild = interaction.guild
        if guild is None:
            return

        error = validate_role(guild, rol)
        if error:
            await interaction.response.send_message(
                error, ephemeral=True
            )
            return

        role_ids = get_role_ids(guild.id)

        if rol.id in role_ids:
            await interaction.response.send_message(
                f"{rol.mention} ya está configurado como autorol.",
                ephemeral=True,
            )
            return

        role_ids.append(rol.id)
        set_role_ids(guild.id, role_ids)

        await interaction.response.send_message(
            embed=make_embed(
                "AUTOROL AGREGADO",
                f"Se agregó {rol.mention}.\n"
                f"Total de roles configurados: **{len(role_ids)}**.",
            ),
            ephemeral=True,
        )

    @app_commands.command(
        name="autorol-quitar-rol",
        description="Quita un rol de la asignación automática.",
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles=True)
    async def autorol_quitar_rol(
        self,
        interaction: discord.Interaction,
        rol: discord.Role,
    ):
        guild = interaction.guild
        if guild is None:
            return

        role_ids = get_role_ids(guild.id)

        if rol.id not in role_ids:
            await interaction.response.send_message(
                f"{rol.mention} no está configurado como autorol.",
                ephemeral=True,
            )
            return

        role_ids.remove(rol.id)
        set_role_ids(guild.id, role_ids)

        await interaction.response.send_message(
            embed=make_embed(
                "AUTOROL ACTUALIZADO",
                f"Se quitó {rol.mention} de la configuración.",
            ),
            ephemeral=True,
        )

    @app_commands.command(
        name="autorol-ver",
        description="Muestra los roles automáticos configurados.",
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles=True)
    async def autorol_ver(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            return

        role_ids = get_role_ids(guild.id)
        roles = [
            guild.get_role(role_id)
            for role_id in role_ids
        ]
        roles = [role for role in roles if role is not None]

        if roles:
            description = "\n".join(
                f"• {role.mention}" for role in roles
            )
        else:
            description = (
                "No hay roles configurados. "
                "Usa `/autorol-configurar`."
            )

        await interaction.response.send_message(
            embed=make_embed("ROLES AUTOMÁTICOS", description),
            ephemeral=True,
        )

    @app_commands.command(
        name="autorol-quitar",
        description="Desactiva todos los roles automáticos.",
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles=True)
    async def autorol_quitar(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            return

        set_role_ids(guild.id, [])

        await interaction.response.send_message(
            embed=make_embed(
                "AUTOROL DESACTIVADO",
                "Se quitaron todos los roles de la asignación automática.",
            ),
            ephemeral=True,
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        role_ids = get_role_ids(member.guild.id)
        if not role_ids:
            return

        bot_member = member.guild.me

        if (
            bot_member is None
            or not bot_member.guild_permissions.manage_roles
        ):
            print(
                f"[AUTOROL] Falta Gestionar roles "
                f"en {member.guild.name}."
            )
            return

        roles = []

        for role_id in role_ids:
            role = member.guild.get_role(role_id)

            if role is None or role.is_default() or role.managed:
                continue

            if role >= bot_member.top_role:
                print(
                    f"[AUTOROL] Jerarquía insuficiente "
                    f"para {role.name}."
                )
                continue

            roles.append(role)

        if not roles:
            return

        try:
            await member.add_roles(
                *roles,
                reason="ROOTGHOST Autorol múltiple",
            )
            print(
                f"[AUTOROL] Asignados {len(roles)} roles "
                f"a {member} en {member.guild.name}."
            )
        except discord.Forbidden:
            print(
                f"[AUTOROL] Discord rechazó asignar roles "
                f"en {member.guild.name}."
            )
        except discord.HTTPException as error:
            print(f"[AUTOROL] Error de Discord: {error}")


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoRoleSetup(bot))
