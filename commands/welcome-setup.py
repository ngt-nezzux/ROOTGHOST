
import json
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CONFIG_FILE = DATA_DIR / "welcome.json"


def load_config():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(config):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps(config, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )


class WelcomeSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="welcome-setup",
        description="Configura los mensajes de bienvenida."
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        canal="Canal donde se enviarán las bienvenidas.",
        mensaje="Mensaje personalizado de bienvenida."
    )
    async def welcome_setup(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
        mensaje: str
    ):
        if len(mensaje) > 1500:
            await interaction.response.send_message(
                "El mensaje no puede superar los 1500 caracteres.",
                ephemeral=True
            )
            return

        config = load_config()
        config[str(interaction.guild.id)] = {
            "channel_id": canal.id,
            "message": mensaje
        }
        save_config(config)

        await interaction.response.send_message(
            f"Canal de bienvenida configurado: {canal.mention}\n"
            "La configuración quedó guardada.",
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        config = load_config().get(str(member.guild.id))
        if not config:
            return

        channel = member.guild.get_channel(config["channel_id"])
        if not isinstance(channel, discord.TextChannel):
            return

        message = config.get("message", "¡Bienvenido/a {mention}!")

        message = message.replace("{mention}", member.mention)
        message = message.replace("{username}", member.display_name)
        message = message.replace("{server}", member.guild.name)
        message = message.replace(
            "{member_count}", str(member.guild.member_count)
        )

        embed = discord.Embed(
            title="ROOTGHOST // NEW MEMBER",
            description=message,
            color=0x5865F2
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="ROOTGHOST SECURITY SYSTEM")

        try:
            await channel.send(
                embed=embed,
                allowed_mentions=discord.AllowedMentions(
                    users=True, roles=False, everyone=False
                )
            )
        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass


async def setup(bot):
    await bot.add_cog(WelcomeSetup(bot))
