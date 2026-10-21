import discord
from discord import app_commands
from discord.ext import commands


class SlowmodeStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="slowmode-status", description="Consulta el modo lento de un canal.")
    @app_commands.guild_only()
    @app_commands.describe(canal="Canal de texto a consultar (opcional)")
    async def slowmode_status(self, interaction: discord.Interaction, canal: discord.TextChannel = None):
        canal = canal or interaction.channel
        if not isinstance(canal, discord.TextChannel):
            return await interaction.response.send_message("No pude identificar un canal de texto.", ephemeral=True)
        if canal.guild.id != interaction.guild_id:
            return await interaction.response.send_message("El canal debe pertenecer a este servidor.", ephemeral=True)
        seconds = canal.slowmode_delay
        if seconds == 0:
            text = "El modo lento está **desactivado**."
        else:
            text = f"El modo lento está **activado**: un mensaje cada **{seconds} segundo(s)**."
        embed = discord.Embed(title="ROOTGHOST // SLOWMODE STATUS", description=f"{canal.mention}\n{text}", color=0x5865F2)
        embed.set_footer(text="ROOTGHOST SECURITY SYSTEM")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(SlowmodeStatus(bot))
