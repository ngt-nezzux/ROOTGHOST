import discord
from discord import app_commands
from discord.ext import commands


class ChannelLock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="channel-lock", description="Bloquea o desbloquea mensajes en un canal de texto.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.describe(bloquear="Sí para bloquear el canal; No para desbloquearlo", canal="Canal que se modificará (opcional)", motivo="Motivo del cambio")
    async def channel_lock(self, interaction: discord.Interaction, bloquear: bool, canal: discord.TextChannel = None, motivo: app_commands.Range[str, 1, 300] = "Sin motivo indicado"):
        canal = canal or interaction.channel
        if not isinstance(canal, discord.TextChannel) or canal.guild.id != interaction.guild_id:
            return await interaction.response.send_message("❌ Seleccioná un canal de texto de este servidor.", ephemeral=True)
        bot_member = interaction.guild.me
        if bot_member is None or not canal.permissions_for(bot_member).manage_channels:
            return await interaction.response.send_message("❌ Necesito el permiso Gestionar canales para cambiar los permisos.", ephemeral=True)
        overwrite = canal.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = not bloquear
        try:
            await canal.set_permissions(
                interaction.guild.default_role,
                overwrite=overwrite,
                reason=f"{interaction.user} ({interaction.user.id}): {motivo}"
            )
        except discord.Forbidden:
            return await interaction.response.send_message("❌ Discord rechazó el cambio de permisos. Revisá la jerarquía y mis permisos.", ephemeral=True)
        except discord.HTTPException:
            return await interaction.response.send_message("❌ No pude cambiar los permisos del canal.", ephemeral=True)
        state = "bloqueado" if bloquear else "desbloqueado"
        await interaction.response.send_message(
            f"ROOTGHOST // CHANNEL LOCK\n{canal.mention} quedó **{state}**.\nMotivo: {motivo}",
            allowed_mentions=discord.AllowedMentions.none()
        )

async def setup(bot):
    await bot.add_cog(ChannelLock(bot))
