import discord
from discord import app_commands
from discord.ext import commands


class ServerStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="serverstats", description="Ver estadísticas detalladas del servidor")
    @app_commands.guild_only()
    async def serverstats(self, interaction: discord.Interaction):
        guild = interaction.guild
        cached_members = list(guild.members)
        humans = sum(not member.bot for member in cached_members)
        bots = sum(member.bot for member in cached_members)
        text_channels = sum(isinstance(c, discord.TextChannel) for c in guild.channels)
        voice_channels = sum(isinstance(c, discord.VoiceChannel) for c in guild.channels)
        categories = sum(isinstance(c, discord.CategoryChannel) for c in guild.channels)
        embed = discord.Embed(title="ROOTGHOST // SERVER STATISTICS", color=0x5865F2)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
        embed.add_field(name="Servidor", value=guild.name, inline=False)
        embed.add_field(name="Miembros registrados", value=str(guild.member_count or "No disponible"), inline=True)
        embed.add_field(name="Humanos en caché", value=str(humans), inline=True)
        embed.add_field(name="Bots en caché", value=str(bots), inline=True)
        embed.add_field(name="Canales de texto", value=str(text_channels), inline=True)
        embed.add_field(name="Canales de voz", value=str(voice_channels), inline=True)
        embed.add_field(name="Categorías", value=str(categories), inline=True)
        embed.add_field(name="Roles", value=str(max(0, len(guild.roles) - 1)), inline=True)
        embed.add_field(name="Creado el", value=discord.utils.format_dt(guild.created_at, style="D"), inline=True)
        embed.set_footer(text="Las cifras en caché dependen de Members Intent.")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(ServerStats(bot))
