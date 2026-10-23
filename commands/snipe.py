import discord
from discord import app_commands
from discord.ext import commands
from datetime import timezone

COLOR = 0x2ECC71


class Snipe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.deleted_messages = {}

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.guild is None:
            return

        # Ignorar mensajes de bots y guardar el último mensaje por canal.
        if message.author.bot:
            return

        self.deleted_messages[message.channel.id] = {
            "author": str(message.author),
            "author_id": message.author.id,
            "content": message.content or "*Sin contenido de texto*",
            "created_at": message.created_at,
            "deleted_at": discord.utils.utcnow(),
            "attachments": [
                attachment.url for attachment in message.attachments
            ],
        }

    @app_commands.command(
        name="snipe",
        description="Muestra el último mensaje eliminado de este canal.",
    )
    @app_commands.guild_only()
    async def snipe(self, interaction: discord.Interaction):
        data = self.deleted_messages.get(interaction.channel_id)

        if data is None:
            await interaction.response.send_message(
                "No hay mensajes eliminados registrados en este canal "
                "desde que inicié.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="ROOTGHOST // SNIPE",
            description=data["content"][:4000],
            color=COLOR,
            timestamp=data["deleted_at"],
        )
        embed.set_author(
            name=data["author"],
            icon_url=(
                interaction.guild.get_member(data["author_id"]).display_avatar.url
                if interaction.guild.get_member(data["author_id"])
                else None
            ),
        )
        embed.add_field(
            name="Mensaje enviado",
            value=discord.utils.format_dt(data["created_at"], style="F"),
            inline=False,
        )
        embed.add_field(
            name="Mensaje eliminado",
            value=discord.utils.format_dt(data["deleted_at"], style="F"),
            inline=False,
        )

        if data["attachments"]:
            urls = "\n".join(data["attachments"][:5])
            embed.add_field(
                name="Archivos adjuntos",
                value=urls[:1000],
                inline=False,
            )

        embed.set_footer(text="ROOTGHOST SECURITY SYSTEM")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Snipe(bot))
