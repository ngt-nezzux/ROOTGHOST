
import discord
from discord import app_commands
from discord.ext import commands


class Role(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="role",
        description="Asigna o quita un rol a un miembro."
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.describe(
        miembro="Miembro al que querés modificar el rol.",
        rol="Rol que querés asignar o quitar.",
        accion="Elegí si querés asignar o quitar el rol."
    )
    @app_commands.choices(accion=[
        app_commands.Choice(name="Asignar", value="add"),
        app_commands.Choice(name="Quitar", value="remove")
    ])
    async def role(
        self,
        interaction: discord.Interaction,
        miembro: discord.Member,
        rol: discord.Role,
        accion: app_commands.Choice[str]
    ):
        guild = interaction.guild
        bot_member = guild.me

        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "No tenés permiso para administrar roles.",
                ephemeral=True
            )
            return

        if not interaction.app_permissions.manage_roles:
            await interaction.response.send_message(
                "ROOTGHOST necesita el permiso Administrar roles.",
                ephemeral=True
            )
            return

        if rol.is_default() or rol.managed:
            await interaction.response.send_message(
                "Ese rol no se puede asignar o quitar manualmente.",
                ephemeral=True
            )
            return

        if rol >= interaction.user.top_role:
            await interaction.response.send_message(
                "No podés modificar un rol igual o superior al tuyo.",
                ephemeral=True
            )
            return

        if bot_member is None or rol >= bot_member.top_role:
            await interaction.response.send_message(
                "Mi rol debe estar por encima del rol seleccionado.",
                ephemeral=True
            )
            return

        if miembro.id == interaction.user.id:
            await interaction.response.send_message(
                "No podés usar este comando sobre vos mismo.",
                ephemeral=True
            )
            return

        try:
            if accion.value == "add":
                if rol in miembro.roles:
                    await interaction.response.send_message(
                        "Ese miembro ya tiene ese rol.",
                        ephemeral=True
                    )
                    return

                await miembro.add_roles(
                    rol,
                    reason=f"ROOTGHOST: asignado por {interaction.user}"
                )
                resultado = f"Se asignó {rol.mention} a {miembro.mention}."

            else:
                if rol not in miembro.roles:
                    await interaction.response.send_message(
                        "Ese miembro no tiene ese rol.",
                        ephemeral=True
                    )
                    return

                await miembro.remove_roles(
                    rol,
                    reason=f"ROOTGHOST: quitado por {interaction.user}"
                )
                resultado = f"Se quitó {rol.mention} a {miembro.mention}."

            embed = discord.Embed(
                title="ROOTGHOST // ROLE MANAGEMENT",
                description=resultado,
                color=0x5865F2
            )
            embed.set_footer(text="ROOTGHOST SECURITY SYSTEM")

            await interaction.response.send_message(embed=embed)

        except discord.Forbidden:
            await interaction.response.send_message(
                "Discord rechazó la acción. Revisá mis permisos "
                "y la jerarquía de roles.",
                ephemeral=True
            )
        except discord.HTTPException:
            await interaction.response.send_message(
                "No se pudo modificar el rol. Intentá nuevamente.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Role(bot))
