import discord
from discord import app_commands
from discord.ext import commands


class RoleInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="role-info", description="Muestra información de un rol del servidor.")
    @app_commands.guild_only()
    async def role_info(self, interaction: discord.Interaction, rol: discord.Role):
        embed = discord.Embed(title="ROOTGHOST // ROLE INFO", color=rol.color or 0x5865F2)
        embed.add_field(name="Rol", value=f"{rol.mention} (`{rol.id}`)", inline=False)
        embed.add_field(name="Integrantes", value=str(len(rol.members)), inline=True)
        embed.add_field(name="Posición", value=str(rol.position), inline=True)
        embed.add_field(name="Mencionable", value="Sí" if rol.mentionable else "No", inline=True)
        embed.add_field(name="Separado", value="Sí" if rol.hoist else "No", inline=True)
        perms = [name.replace("_", " ").title() for name, value in rol.permissions if value]
        embed.add_field(name="Permisos habilitados", value=", ".join(perms[:25]) if perms else "Ninguno", inline=False)
        embed.set_footer(text="ROOTGHOST SECURITY SYSTEM")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(RoleInfo(bot))
