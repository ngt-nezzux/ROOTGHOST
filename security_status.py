import discord
from discord import app_commands
from discord.ext import commands


class SecurityStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="security-status", description="Revisar configuraciones básicas de seguridad")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def security_status(self, interaction: discord.Interaction):
        guild = interaction.guild
        me = guild.me
        checks = [
            ("Ver registro de auditoría", me.guild_permissions.view_audit_log),
            ("Gestionar mensajes", me.guild_permissions.manage_messages),
            ("Expulsar miembros", me.guild_permissions.kick_members),
            ("Banear miembros", me.guild_permissions.ban_members),
            ("Gestionar roles", me.guild_permissions.manage_roles),
            ("Gestionar canales", me.guild_permissions.manage_channels),
        ]
        embed = discord.Embed(title="ROOTGHOST // SECURITY STATUS", color=0x5865F2)
        embed.description = "Revisión de permisos del bot. Esto no garantiza protección total."
        embed.add_field(name="Servidor", value=guild.name, inline=False)
        embed.add_field(
            name="Permisos del bot",
            value="\n".join(f"{'✅' if ok else '⚠️'} {label}" for label, ok in checks),
            inline=False,
        )
        embed.add_field(
            name="Members Intent",
            value="Activado" if self.bot.intents.members else "Desactivado",
            inline=True,
        )
        embed.add_field(
            name="Message Content Intent",
            value="Activado" if self.bot.intents.message_content else "Desactivado",
            inline=True,
        )
        embed.set_footer(text="ROOTGHOST SECURITY SYSTEM")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(SecurityStatus(bot))
