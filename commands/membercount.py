
import discord
from discord import app_commands
from discord.ext import commands


class MemberCount(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="membercount",
        description="Muestra las estadísticas de miembros del servidor."
    )
    @app_commands.guild_only()
    async def membercount(self, interaction: discord.Interaction):
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "Este comando solo funciona en un servidor.",
                ephemeral=True
            )
            return

        # La precisión depende de que esté habilitado Members Intent.
        if not self.bot.intents.members:
            await interaction.response.send_message(
                "Para obtener estadísticas precisas, habilitá "
                "Members Intent en bot.py y en Discord Developer Portal.",
                ephemeral=True
            )
            return

        members = guild.members
        humans = sum(not member.bot for member in members)
        bots = sum(member.bot for member in members)

        embed = discord.Embed(
            title="ROOTGHOST // MEMBER STATISTICS",
            description=f"Estadísticas de **{guild.name}**",
            color=0x5865F2,
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="👥 Miembros totales",
            value=f"`{guild.member_count or len(members):,}`",
            inline=True
        )
        embed.add_field(
            name="👤 Usuarios humanos en caché",
            value=f"`{humans:,}`",
            inline=True
        )
        embed.add_field(
            name="🤖 Bots en caché",
            value=f"`{bots:,}`",
            inline=True
        )

        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.set_footer(text="ROOTGHOST SECURITY SYSTEM")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(MemberCount(bot))
