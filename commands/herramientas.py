
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone


class Herramientas(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # /userinfo
    @app_commands.command(
        name="userinfo",
        description="Muestra información de un usuario"
    )
    @app_commands.describe(usuario="Usuario que querés consultar")
    @app_commands.guild_only()
    async def userinfo(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member = None
    ):
        usuario = usuario or interaction.user

        embed = discord.Embed(
            title="ROOTGHOST // USER INFO",
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=usuario.display_avatar.url)
        embed.add_field(name="Usuario", value=usuario.mention, inline=True)
        embed.add_field(name="ID", value=str(usuario.id), inline=True)
        embed.add_field(
            name="Cuenta creada",
            value=discord.utils.format_dt(usuario.created_at, style="D"),
            inline=False
        )
        embed.add_field(
            name="Se unió al servidor",
            value=(
                discord.utils.format_dt(usuario.joined_at, style="D")
                if usuario.joined_at else "Desconocido"
            ),
            inline=False
        )
        embed.add_field(
            name="Roles",
            value=str(max(0, len(usuario.roles) - 1)),
            inline=True
        )
        embed.set_footer(text="ROOTGHOST SECURITY SYSTEM")

        await interaction.response.send_message(embed=embed)

    # /serverinfo
    @app_commands.command(
        name="serverinfo",
        description="Muestra información del servidor"
    )
    @app_commands.guild_only()
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild

        embed = discord.Embed(
            title="ROOTGHOST // SERVER INFO",
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc)
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="Servidor", value=guild.name, inline=False)
        embed.add_field(name="ID", value=str(guild.id), inline=True)
        embed.add_field(
            name="Miembros",
            value=str(guild.member_count or 0),
            inline=True
        )
        embed.add_field(
            name="Canales",
            value=str(len(guild.channels)),
            inline=True
        )
        embed.add_field(
            name="Creado",
            value=discord.utils.format_dt(guild.created_at, style="D"),
            inline=False
        )
        embed.set_footer(text="ROOTGHOST SECURITY SYSTEM")

        await interaction.response.send_message(embed=embed)

    # /clear
    @app_commands.command(
        name="clear",
        description="Borra mensajes recientes del canal"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(cantidad="Cantidad de mensajes a borrar (1-100)")
    async def clear(
        self,
        interaction: discord.Interaction,
        cantidad: app_commands.Range[int, 1, 100]
    ):
        channel = interaction.channel

        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "Este comando solo funciona en canales de texto.",
                ephemeral=True
            )
            return

        if not channel.permissions_for(interaction.guild.me).manage_messages:
            await interaction.response.send_message(
                "No tengo permiso para gestionar mensajes en este canal.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            borrados = await channel.purge(
                limit=cantidad,
                bulk=True,
                reason=f"/clear ejecutado por {interaction.user}"
            )
            await interaction.followup.send(
                f"Se eliminaron {len(borrados)} mensajes.",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "Discord me denegó el permiso para borrar mensajes.",
                ephemeral=True
            )
        except discord.HTTPException:
            await interaction.followup.send(
                "No pude borrar los mensajes. Intentá de nuevo.",
                ephemeral=True
            )

    # /say
    @app_commands.command(
        name="say",
        description="Envía un mensaje como ROOTGHOST"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(mensaje="Texto que publicará el bot")
    async def say(
        self,
        interaction: discord.Interaction,
        mensaje: app_commands.Range[str, 1, 2000]
    ):
        await interaction.response.send_message(
            "Mensaje publicado.",
            ephemeral=True
        )

        await interaction.channel.send(
            mensaje,
            allowed_mentions=discord.AllowedMentions.none()
        )

    # /avatar
    @app_commands.command(
        name="avatar",
        description="Muestra el avatar de un usuario"
    )
    @app_commands.describe(usuario="Usuario cuyo avatar querés ver")
    async def avatar(
        self,
        interaction: discord.Interaction,
        usuario: discord.User = None
    ):
        usuario = usuario or interaction.user

        embed = discord.Embed(
            title=f"Avatar de {usuario.display_name}",
            color=discord.Color.blurple()
        )
        embed.set_image(url=usuario.display_avatar.url)
        embed.set_footer(text="ROOTGHOST SECURITY SYSTEM")

        await interaction.response.send_message(embed=embed)

    # /announce
    @app_commands.command(
        name="announce",
        description="Publica un anuncio con formato"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(
        titulo="Título del anuncio",
        mensaje="Contenido del anuncio",
        color="Color hexadecimal opcional, por ejemplo #5865F2"
    )
    async def announce(
        self,
        interaction: discord.Interaction,
        titulo: app_commands.Range[str, 1, 256],
        mensaje: app_commands.Range[str, 1, 3500],
        color: str = "#5865F2"
    ):
        color = color.strip().removeprefix("#")

        try:
            if (
                len(color) != 6
                or any(c not in "0123456789abcdefABCDEF" for c in color)
            ):
                raise ValueError

            embed_color = discord.Color(int(color, 16))
        except ValueError:
            await interaction.response.send_message(
                "Color inválido. Usá un hexadecimal como #5865F2.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=titulo,
            description=mensaje,
            color=embed_color,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="ROOTGHOST SECURITY SYSTEM")

        await interaction.response.send_message(
            "Anuncio publicado.",
            ephemeral=True
        )

        await interaction.channel.send(
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none()
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Herramientas(bot))
