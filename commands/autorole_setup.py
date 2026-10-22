# ROOTGHOST // AUTOROLE
# discord.py 2.x | Extension para el cargador automatico commands/*.py
# Guardar como commands/autorole_setup.py
# Requiere Members Intent y permiso Gestionar roles.
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


def get_role_id(guild_id):
    return load_config().get("guilds", {}).get(str(guild_id), {}).get("role_id")


def set_role_id(guild_id, role_id):
    data = load_config()
    guilds = data.setdefault("guilds", {})
    if role_id is None:
        guilds.pop(str(guild_id), None)
    else:
        guilds.setdefault(str(guild_id), {})["role_id"] = role_id
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


class AutoRoleSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="autorol-configurar", description="Elige el rol para los nuevos miembros.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles=True)
    async def autorol_configurar(self, interaction: discord.Interaction, rol: discord.Role):
        guild = interaction.guild
        if guild is None:
            return
        if rol.is_default() or rol.managed:
            await interaction.response.send_message("Ese rol no se puede usar como autorol.", ephemeral=True)
            return
        bot_member = guild.me
        if bot_member is None or not bot_member.guild_permissions.manage_roles:
            await interaction.response.send_message("Necesito el permiso Gestionar roles.", ephemeral=True)
            return
        if rol >= bot_member.top_role:
            await interaction.response.send_message(
                "Mi rol más alto debe estar por encima del rol que quieres asignar.", ephemeral=True
            )
            return
        set_role_id(guild.id, rol.id)
        await interaction.response.send_message(
            embed=make_embed("AUTOROL CONFIGURADO", f"Los nuevos miembros recibirán {rol.mention}."),
            ephemeral=True,
        )

    @app_commands.command(name="autorol-ver", description="Muestra el autorol configurado.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles=True)
    async def autorol_ver(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            return
        role_id = get_role_id(guild.id)
        role = guild.get_role(role_id) if role_id else None
        if role is None:
            await interaction.response.send_message(
                embed=make_embed("AUTOROL", "No hay un rol configurado. Usa `/autorol-configurar`."),
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            embed=make_embed("AUTOROL ACTIVO", f"Rol automático: {role.mention}"), ephemeral=True
        )

    @app_commands.command(name="autorol-quitar", description="Desactiva el autorol del servidor.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles=True)
    async def autorol_quitar(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            return
        set_role_id(guild.id, None)
        await interaction.response.send_message(
            embed=make_embed("AUTOROL DESACTIVADO", "Se desactivó la asignación automática."),
            ephemeral=True,
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        role_id = get_role_id(member.guild.id)
        if not role_id:
            return
        role = member.guild.get_role(role_id)
        bot_member = member.guild.me
        if role is None or role.is_default() or role.managed:
            return
        if (
            bot_member is None
            or not bot_member.guild_permissions.manage_roles
            or role >= bot_member.top_role
        ):
            print(f"[AUTOROL] Revisa permisos/jerarquía del rol {role_id} en servidor {member.guild.id}.")
            return
        try:
            await member.add_roles(role, reason="ROOTGHOST Autorol")
            print(f"[AUTOROL] Asignado {role.name} a {member} en {member.guild.name}")
        except discord.Forbidden:
            print(f"[AUTOROL] Discord rechazó asignar el rol {role_id} en servidor {member.guild.id}.")
        except discord.HTTPException as error:
            print(f"[AUTOROL] Error de Discord al asignar rol: {error}")


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoRoleSetup(bot))
