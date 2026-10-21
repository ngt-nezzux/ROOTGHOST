
import json
import random
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CONFIG_FILE = DATA_DIR / "captcha.json"


def load_config():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps(data, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )


class CaptchaModal(discord.ui.Modal, title="Verificación ROOTGHOST"):
    answer = discord.ui.TextInput(
        label="¿Cuánto es el resultado?",
        placeholder="Escribí el resultado",
        max_length=5
    )

    def __init__(self, role_id: int):
        super().__init__(timeout=120)
        self.role_id = role_id
        self.a = random.randint(2, 12)
        self.b = random.randint(2, 12)
        self.expected = self.a + self.b
        self.answer.label = f"¿Cuánto es {self.a} + {self.b}?"

    async def on_submit(self, interaction: discord.Interaction):
        if not self.answer.value.strip().isdigit():
            await interaction.response.send_message(
                "Respuesta inválida. Volvé a intentarlo.",
                ephemeral=True
            )
            return

        if int(self.answer.value.strip()) != self.expected:
            await interaction.response.send_message(
                "Verificación incorrecta. Volvé a pulsar el botón.",
                ephemeral=True
            )
            return

        if interaction.guild is None:
            await interaction.response.send_message(
                "Este sistema solo funciona en un servidor.",
                ephemeral=True
            )
            return

        role = interaction.guild.get_role(self.role_id)
        if role is None:
            await interaction.response.send_message(
                "El rol configurado ya no existe. Avisá a un administrador.",
                ephemeral=True
            )
            return

        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "No puedo asignar ese rol. Revisá la jerarquía de roles.",
                ephemeral=True
            )
            return

        try:
            await interaction.user.add_roles(
                role, reason="Captcha ROOTGHOST superado"
            )
        except (discord.Forbidden, discord.HTTPException):
            await interaction.response.send_message(
                "No pude asignar el rol. Revisá mis permisos.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "Verificación completada correctamente.",
            ephemeral=True
        )


class CaptchaPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verificarme",
        emoji="🔐",
        style=discord.ButtonStyle.success,
        custom_id="rootghost:captcha:verify"
    )
    async def verify(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "Este botón solo funciona en un servidor.",
                ephemeral=True
            )
            return

        config = load_config().get(str(interaction.guild.id))
        if not config:
            await interaction.response.send_message(
                "El sistema no está configurado.",
                ephemeral=True
            )
            return

        role = interaction.guild.get_role(config["role_id"])
        if role is None:
            await interaction.response.send_message(
                "El rol de verificación ya no existe.",
                ephemeral=True
            )
            return

        if role in interaction.user.roles:
            await interaction.response.send_message(
                "Ya estás verificado.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            CaptchaModal(role.id)
        )


class Captcha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(CaptchaPanel())

    @app_commands.command(
        name="captcha",
        description="Configura el panel de verificación."
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def captcha(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
        rol_verificado: discord.Role
    ):
        if rol_verificado >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "Mi rol debe estar por encima del rol de verificación.",
                ephemeral=True
            )
            return

        config = load_config()
        config[str(interaction.guild.id)] = {
            "channel_id": canal.id,
            "role_id": rol_verificado.id
        }
        save_config(config)

        embed = discord.Embed(
            title="ROOTGHOST // VERIFICACIÓN",
            description=(
                "Para obtener acceso al servidor, pulsá el botón "
                "y resolvé la prueba de verificación."
            ),
            color=0x5865F2
        )
        embed.set_footer(text="ROOTGHOST SECURITY SYSTEM")

        try:
            await canal.send(
                embed=embed,
                view=CaptchaPanel()
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "No tengo permisos para publicar en ese canal.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"Panel publicado en {canal.mention}.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Captcha(bot))
