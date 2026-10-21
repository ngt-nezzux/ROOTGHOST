
import json
import re
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands


# ROOTGHOST // CONFIGURACIÓN
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CONFIG_FILE = DATA_DIR / "tickets.json"


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


def ticket_owner_id(channel):
    topic = channel.topic or ""

    match = re.search(r"rootghost_ticket_owner=(\d+)", topic)
    return int(match.group(1)) if match else None


class TicketControls(discord.ui.View):
    """Botones persistentes para administrar un ticket."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Cerrar ticket",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="rootghost:tickets:close"
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        channel = interaction.channel
        guild = interaction.guild

        if guild is None or not isinstance(
            channel, discord.TextChannel
        ):
            await interaction.response.send_message(
                "Este botón solo funciona dentro de un ticket.",
                ephemeral=True
            )
            return

        owner_id = ticket_owner_id(channel)

        if owner_id is None:
            await interaction.response.send_message(
                "Este canal no parece ser un ticket de ROOTGHOST.",
                ephemeral=True
            )
            return

        config = load_config().get(str(guild.id), {})
        support_role_id = config.get("support_role_id")

        is_owner = interaction.user.id == owner_id
        is_manager = interaction.user.guild_permissions.manage_channels

        support_role = (
            guild.get_role(support_role_id)
            if support_role_id else None
        )
        is_support = (
            support_role is not None
            and support_role in interaction.user.roles
        )

        if not (is_owner or is_manager or is_support):
            await interaction.response.send_message(
                "No tenés permiso para cerrar este ticket.",
                ephemeral=True
            )
            return

        owner = guild.get_member(owner_id)

        try:
            if owner is not None:
                overwrite = channel.overwrites_for(owner)
                overwrite.send_messages = False
                await channel.set_permissions(
                    owner,
                    overwrite=overwrite,
                    reason=f"Ticket cerrado por {interaction.user}"
                )

            if not channel.name.startswith("cerrado-"):
                new_name = f"cerrado-{channel.name}"[:100]
                await channel.edit(
                    name=new_name,
                    reason=f"Ticket cerrado por {interaction.user}"
                )

            await interaction.response.send_message(
                "🔒 Ticket cerrado correctamente.",
                ephemeral=True
            )

            # Evitar que se vuelva a utilizar el botón.
            await interaction.message.edit(view=None)

            await channel.send(
                embed=discord.Embed(
                    title="ROOTGHOST // TICKET CLOSED",
                    description=(
                        f"Ticket cerrado por {interaction.user.mention}.\n"
                        "El canal queda disponible para el personal "
                        "autorizado."
                    ),
                    color=0x5865F2
                ),
                allowed_mentions=discord.AllowedMentions.none()
            )

        except discord.Forbidden:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "No tengo permisos para cerrar este ticket.",
                    ephemeral=True
                )
        except discord.HTTPException:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Ocurrió un error al cerrar el ticket.",
                    ephemeral=True
                )


class TicketPanel(discord.ui.View):
    """Panel persistente para abrir tickets."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Abrir ticket",
        emoji="🎫",
        style=discord.ButtonStyle.primary,
        custom_id="rootghost:tickets:open"
    )
    async def open_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "Este panel solo funciona en un servidor.",
                ephemeral=True
            )
            return

        config = load_config().get(str(guild.id))

        if not config:
            await interaction.response.send_message(
                "El sistema de tickets no está configurado.",
                ephemeral=True
            )
            return

        # Comprobar si ya existe un ticket abierto.
        for channel in guild.text_channels:
            if ticket_owner_id(channel) == interaction.user.id:
                if not channel.name.startswith("cerrado-"):
                    await interaction.response.send_message(
                        f"Ya tenés un ticket abierto: {channel.mention}",
                        ephemeral=True
                    )
                    return

        await interaction.response.defer(
            ephemeral=True,
            thinking=True
        )

        category_id = config.get("category_id")
        category = (
            guild.get_channel(category_id)
            if category_id else None
        )

        if category_id and not isinstance(
            category, discord.CategoryChannel
        ):
            await interaction.followup.send(
                "La categoría configurada ya no existe. "
                "Volvé a configurar el sistema.",
                ephemeral=True
            )
            return

        bot_member = guild.me
        if bot_member is None:
            await interaction.followup.send(
                "No pude identificar al bot en el servidor.",
                ephemeral=True
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            ),
            bot_member: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True
            )
        }

        support_role_id = config.get("support_role_id")
        support_role = (
            guild.get_role(support_role_id)
            if support_role_id else None
        )

        if support_role is not None:
            overwrites[support_role] = (
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                )
            )

        slug = re.sub(
            r"[^a-z0-9-]",
            "",
            interaction.user.name.lower().replace(" ", "-")
        )[:40] or "usuario"

        channel_name = f"ticket-{slug}"[:100]

        try:
            channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=(
                    f"ROOTGHOST support ticket | "
                    f"rootghost_ticket_owner={interaction.user.id}"
                ),
                reason=f"Ticket abierto por {interaction.user}"
            )

            embed = discord.Embed(
                title="ROOTGHOST // SUPPORT TICKET",
                description=(
                    f"Hola {interaction.user.mention}.\n\n"
                    "Describí tu consulta y el equipo de soporte "
                    "te responderá cuando esté disponible.\n\n"
                    "No compartas contraseñas ni tokens privados."
                ),
                color=0x5865F2
            )
            embed.add_field(
                name="Estado",
                value="🟢 Abierto",
                inline=True
            )
            embed.set_footer(
                text="ROOTGHOST SECURITY SYSTEM"
            )

            await channel.send(
                content=interaction.user.mention,
                embed=embed,
                view=TicketControls(),
                allowed_mentions=discord.AllowedMentions(
                    users=True,
                    roles=False,
                    everyone=False
                )
            )

            await interaction.followup.send(
                f"Ticket creado correctamente: {channel.mention}",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.followup.send(
                "No tengo permisos suficientes para crear el ticket. "
                "Revisá Manage Channels, View Channels y Send Messages.",
                ephemeral=True
            )
        except discord.HTTPException:
            await interaction.followup.send(
                "Discord no pudo crear el ticket. Intentá nuevamente.",
                ephemeral=True
            )


class TicketSetup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # Registrar las vistas persistentes al iniciar el bot.
        self.bot.add_view(TicketPanel())
        self.bot.add_view(TicketControls())

    @app_commands.command(
        name="ticket-setup",
        description="Configura el panel de tickets de ROOTGHOST."
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        canal="Canal donde se publicará el panel.",
        categoria="Categoría donde se crearán los tickets.",
        rol_soporte="Rol que podrá ver y atender los tickets."
    )
    async def ticket_setup(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
        categoria: discord.CategoryChannel = None,
        rol_soporte: discord.Role = None
    ):
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "Este comando solo funciona en un servidor.",
                ephemeral=True
            )
            return

        bot_member = guild.me
        if bot_member is None:
            await interaction.response.send_message(
                "No pude identificar al bot en el servidor.",
                ephemeral=True
            )
            return

        if rol_soporte is not None and rol_soporte >= bot_member.top_role:
            await interaction.response.send_message(
                "El rol de soporte no puede estar por encima "
                "del rol más alto del bot.",
                ephemeral=True
            )
            return

        await interaction.response.defer(
            ephemeral=True,
            thinking=True
        )

        embed = discord.Embed(
            title="ROOTGHOST // SUPPORT CENTER",
            description=(
                "¿Necesitás ayuda del equipo?\n\n"
                "Pulsá **Abrir ticket** para crear un canal privado "
                "donde puedas explicar tu consulta.\n\n"
                "El abuso del sistema puede generar restricciones."
            ),
            color=0x5865F2
        )
        embed.set_footer(
            text="ROOTGHOST SECURITY SYSTEM"
        )

        try:
            await canal.send(
                embed=embed,
                view=TicketPanel()
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "No puedo publicar en ese canal. "
                "Necesito View Channel, Send Messages y Embed Links.",
                ephemeral=True
            )
            return
        except discord.HTTPException:
            await interaction.followup.send(
                "No se pudo publicar el panel de tickets.",
                ephemeral=True
            )
            return

        config = load_config()
        config[str(guild.id)] = {
            "panel_channel_id": canal.id,
            "category_id": categoria.id if categoria else None,
            "support_role_id": (
                rol_soporte.id if rol_soporte else None
            )
        }
        save_config(config)

        await interaction.followup.send(
            f"Panel de tickets publicado en {canal.mention}.\n"
            f"Categoría: {categoria.mention if categoria else 'Sin categoría'}\n"
            f"Rol de soporte: {rol_soporte.mention if rol_soporte else 'Sin rol específico'}",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(TicketSetup(bot))
