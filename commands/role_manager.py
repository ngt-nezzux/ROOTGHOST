# ROOTGHOST // ROLE MANAGER
# discord.py 2.x | Extension para el cargador automatico commands/*.py
# Guardar como: commands/role_manager.py
#
# Comandos:
# /rol-all       -> asigna un rol a los miembros humanos del servidor
# /remove-all    -> quita un rol a los miembros humanos del servidor
# /rol-add       -> asigna un rol a un miembro
# /rol-remove    -> quita un rol a un miembro
# /rol-info      -> muestra informacion de un rol
# /rol-list      -> lista roles del servidor
#
# Las operaciones masivas requieren confirmacion y procesan en lotes.
# No intenta modificar @everyone, roles administrados ni roles iguales/superiores al bot.

from __future__ import annotations

import asyncio
import discord
from discord import app_commands
from discord.ext import commands

COLOR = 0x2ECC71
BATCH_SIZE = 5
DELAY_BETWEEN_BATCHES = 1.0


def embed(title: str, description: str = "") -> discord.Embed:
    result = discord.Embed(
        title=f"ROOTGHOST // {title}",
        description=description,
        color=COLOR,
        timestamp=discord.utils.utcnow(),
    )
    result.set_footer(text="ROOTGHOST SECURITY SYSTEM")
    return result


def role_is_manageable(guild: discord.Guild, role: discord.Role) -> tuple[bool, str]:
    if role.is_default():
        return False, "No se puede administrar el rol @everyone."
    if role.managed:
        return False, "Ese rol está administrado por una integración y no se puede modificar."
    bot_member = guild.me
    if bot_member is None or not bot_member.guild_permissions.manage_roles:
        return False, "ROOTGHOST necesita el permiso **Gestionar roles**."
    if role >= bot_member.top_role:
        return False, "El rol de ROOTGHOST debe estar por encima del rol seleccionado."
    return True, ""


class MassRoleConfirm(discord.ui.View):
    def __init__(self, cog: "RoleManager", role: discord.Role, remove: bool, actor_id: int):
        super().__init__(timeout=60)
        self.cog = cog
        self.role = role
        self.remove = remove
        self.actor_id = actor_id
        self.finished = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.actor_id:
            await interaction.response.send_message(
                "Solo quien inició esta operación puede confirmarla.", ephemeral=True
            )
            return False
        if not isinstance(interaction.user, discord.Member) or not (
            interaction.user.guild_permissions.manage_roles
            or interaction.user.guild_permissions.administrator
        ):
            await interaction.response.send_message(
                "Ya no tienes permisos suficientes para esta operación.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Confirmar", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.finished:
            await interaction.response.send_message("Esta operación ya terminó.", ephemeral=True)
            return
        self.finished = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content="Operación confirmada. Procesando miembros por lotes…", view=self
        )
        await self.cog.run_mass_role(interaction, self.role, self.remove)

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.finished = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="Operación cancelada.", view=self)


class RoleManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_guilds: set[int] = set()

    async def run_mass_role(
        self, interaction: discord.Interaction, role: discord.Role, remove: bool
    ):
        guild = interaction.guild
        if guild is None:
            return

        ok, reason = role_is_manageable(guild, role)
        if not ok:
            await interaction.followup.send(reason, ephemeral=True)
            return

        if guild.id in self.active_guilds:
            await interaction.followup.send(
                "Ya hay una operación masiva de roles en curso en este servidor.",
                ephemeral=True,
            )
            return

        self.active_guilds.add(guild.id)
        added = 0
        removed = 0
        skipped = 0
        failed = 0
        try:
            # Solo miembros humanos; evita bots para no afectar integraciones.
            members = list(guild.members)
            targets = [
                member for member in members
                if not member.bot
                and ((role in member.roles) if remove else (role not in member.roles))
            ]

            for start in range(0, len(targets), BATCH_SIZE):
                batch = targets[start:start + BATCH_SIZE]
                for member in batch:
                    # Revalidar jerarquía/permisos en caso de cambios durante el proceso.
                    ok, _ = role_is_manageable(guild, role)
                    if not ok:
                        skipped += len(targets) - (start + batch.index(member))
                        break
                    try:
                        if remove:
                            await member.remove_roles(role, reason=f"ROOTGHOST bulk role by {interaction.user}")
                            removed += 1
                        else:
                            await member.add_roles(role, reason=f"ROOTGHOST bulk role by {interaction.user}")
                            added += 1
                    except discord.Forbidden:
                        failed += 1
                    except discord.HTTPException:
                        failed += 1
                else:
                    if start + BATCH_SIZE < len(targets):
                        await asyncio.sleep(DELAY_BETWEEN_BATCHES)
                    continue
                break

            action = "eliminación" if remove else "asignación"
            result = embed(
                "OPERACIÓN MASIVA FINALIZADA",
                f"**Acción:** {action}\\n**Rol:** {role.mention}",
            )
            result.add_field(name="Miembros objetivo", value=str(len(targets)), inline=True)
            result.add_field(name="Completados", value=str(removed if remove else added), inline=True)
            result.add_field(name="Fallidos", value=str(failed), inline=True)
            if skipped:
                result.add_field(name="Omitidos", value=str(skipped), inline=True)
            result.set_footer(text="ROOTGHOST SECURITY SYSTEM • Solo miembros humanos")
            await interaction.followup.send(embed=result, ephemeral=True)
        finally:
            self.active_guilds.discard(guild.id)

    @app_commands.command(name="rol-all", description="Asigna un rol a todos los miembros humanos.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.describe(rol="Rol que se asignará a los miembros")
    async def rol_all(self, interaction: discord.Interaction, rol: discord.Role):
        guild = interaction.guild
        if guild is None:
            return
        ok, reason = role_is_manageable(guild, rol)
        if not ok:
            await interaction.response.send_message(reason, ephemeral=True)
            return
        view = MassRoleConfirm(self, rol, False, interaction.user.id)
        await interaction.response.send_message(
            embed=embed(
                "CONFIRMAR ROL-ALL",
                f"Vas a asignar {rol.mention} a todos los miembros humanos que todavía no lo tengan.\\n"
                "La operación se hará por lotes y puede tardar. ¿Continuar?",
            ),
            view=view,
            ephemeral=True,
        )

    @app_commands.command(name="remove-all", description="Quita un rol a todos los miembros humanos que lo tengan.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.describe(rol="Rol que se quitará a los miembros")
    async def remove_all(self, interaction: discord.Interaction, rol: discord.Role):
        guild = interaction.guild
        if guild is None:
            return
        ok, reason = role_is_manageable(guild, rol)
        if not ok:
            await interaction.response.send_message(reason, ephemeral=True)
            return
        view = MassRoleConfirm(self, rol, True, interaction.user.id)
        await interaction.response.send_message(
            embed=embed(
                "CONFIRMAR REMOVE-ALL",
                f"Vas a quitar {rol.mention} a todos los miembros humanos que lo tengan.\\n"
                "La operación se hará por lotes y puede tardar. ¿Continuar?",
            ),
            view=view,
            ephemeral=True,
        )

    @app_commands.command(name="rol-add", description="Asigna un rol a un miembro.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles=True)
    async def rol_add(self, interaction: discord.Interaction, miembro: discord.Member, rol: discord.Role):
        ok, reason = role_is_manageable(interaction.guild, rol)
        if not ok:
            await interaction.response.send_message(reason, ephemeral=True)
            return
        if miembro.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "No puedo administrar a ese miembro por su jerarquía de roles.", ephemeral=True
            )
            return
        if rol in miembro.roles:
            await interaction.response.send_message(
                f"{miembro.mention} ya tiene {rol.mention}.", ephemeral=True
            )
            return
        try:
            await miembro.add_roles(rol, reason=f"ROOTGHOST role-add by {interaction.user}")
            await interaction.response.send_message(
                embed=embed("ROL ASIGNADO", f"Se asignó {rol.mention} a {miembro.mention}."),
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.response.send_message("Discord rechazó la acción por permisos o jerarquía.", ephemeral=True)

    @app_commands.command(name="rol-remove", description="Quita un rol a un miembro.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles=True)
    async def rol_remove(self, interaction: discord.Interaction, miembro: discord.Member, rol: discord.Role):
        ok, reason = role_is_manageable(interaction.guild, rol)
        if not ok:
            await interaction.response.send_message(reason, ephemeral=True)
            return
        if miembro.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "No puedo administrar a ese miembro por su jerarquía de roles.", ephemeral=True
            )
            return
        if rol not in miembro.roles:
            await interaction.response.send_message(
                f"{miembro.mention} no tiene {rol.mention}.", ephemeral=True
            )
            return
        try:
            await miembro.remove_roles(rol, reason=f"ROOTGHOST role-remove by {interaction.user}")
            await interaction.response.send_message(
                embed=embed("ROL ELIMINADO", f"Se quitó {rol.mention} a {miembro.mention}."),
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.response.send_message("Discord rechazó la acción por permisos o jerarquía.", ephemeral=True)

    @app_commands.command(name="rol-info", description="Muestra información de un rol.")
    @app_commands.guild_only()
    async def rol_info(self, interaction: discord.Interaction, rol: discord.Role):
        perms = [name.replace("_", " ").title() for name, value in rol.permissions if value]
        result = embed(f"ROL // {rol.name}", f"ID: `{rol.id}`")
        result.add_field(name="Color", value=str(rol.color), inline=True)
        result.add_field(name="Miembros", value=str(len(rol.members)), inline=True)
        result.add_field(name="Posición", value=str(rol.position), inline=True)
        result.add_field(name="Mencionable", value="Sí" if rol.mentionable else "No", inline=True)
        result.add_field(name="Administrador", value="Sí" if rol.permissions.administrator else "No", inline=True)
        result.add_field(name="Permisos activos", value=", ".join(perms[:25]) or "Ninguno", inline=False)
        await interaction.response.send_message(embed=result, ephemeral=True)

    @app_commands.command(name="rol-list", description="Lista los roles del servidor.")
    @app_commands.guild_only()
    async def rol_list(self, interaction: discord.Interaction):
        guild = interaction.guild
        roles = [role for role in reversed(guild.roles) if not role.is_default()]
        lines = [f"{role.mention} — posición {role.position}" for role in roles[:40]]
        if len(roles) > 40:
            lines.append(f"… y {len(roles) - 40} roles más.")
        result = embed("ROLES DEL SERVIDOR", "\\n".join(lines) or "No hay roles personalizados.")
        await interaction.response.send_message(embed=result, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(RoleManager(bot))
