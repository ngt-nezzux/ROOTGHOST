from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands


class HelpPages(discord.ui.View):
    """Paginación para mostrar todos los comandos registrados."""

    def __init__(self, interaction: discord.Interaction, pages: list[discord.Embed]):
        super().__init__(timeout=180)
        self.owner_id = interaction.user.id
        self.pages = pages
        self.index = 0
        self._refresh_buttons()

    def _refresh_buttons(self) -> None:
        self.previous_button.disabled = self.index <= 0
        self.next_button.disabled = self.index >= len(self.pages) - 1

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "Solo quien abrió esta ayuda puede cambiar de página.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Anterior", emoji="⬅️", style=discord.ButtonStyle.secondary)
    async def previous_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.index = max(0, self.index - 1)
        self._refresh_buttons()
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)

    @discord.ui.button(label="Siguiente", emoji="➡️", style=discord.ButtonStyle.primary)
    async def next_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.index = min(len(self.pages) - 1, self.index + 1)
        self._refresh_buttons()
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)


class Ayuda(commands.Cog):
    """Ayuda automática basada en los comandos slash cargados en el bot."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _registered_commands(self, guild: discord.Guild) -> list[app_commands.Command]:
        # Reúne comandos globales y comandos específicos del servidor, evitando duplicados.
        combined: dict[str, app_commands.Command] = {}

        for command in self.bot.tree.get_commands():
            combined[command.name] = command

        for command in self.bot.tree.get_commands(guild=guild):
            combined[command.name] = command

        # No mostramos comandos internos de Discord ni grupos vacíos.
        return sorted(combined.values(), key=lambda command: command.name.casefold())

    @staticmethod
    def _command_description(command: app_commands.Command) -> str:
        description = (command.description or "").strip()
        if not description or description == "...":
            description = "Sin descripción configurada."
        return description[:180]

    def _make_pages(
        self, guild: discord.Guild, commands_list: list[app_commands.Command]
    ) -> list[discord.Embed]:
        # 10 comandos por página para que la ayuda sea legible en móvil.
        chunks = [commands_list[i:i + 10] for i in range(0, len(commands_list), 10)]
        if not chunks:
            chunks = [[]]

        pages: list[discord.Embed] = []
        for page_number, chunk in enumerate(chunks, start=1):
            embed = discord.Embed(
                title="ROOTGHOST // CENTRO DE AYUDA",
                description=(
                    "Lista automática de comandos slash disponibles.\n"
                    "Se genera desde los comandos cargados en ROOTGHOST."
                ),
                color=discord.Color.dark_teal(),
            )

            if not chunk:
                embed.add_field(
                    name="Sin comandos detectados",
                    value="No se encontraron comandos slash registrados en el árbol del bot.",
                    inline=False,
                )
            else:
                for command in chunk:
                    embed.add_field(
                        name=f"/{command.name}",
                        value=self._command_description(command),
                        inline=False,
                    )

            embed.set_footer(
                text=f"ROOTGHOST SECURITY SYSTEM • Página {page_number}/{len(chunks)} • "
                     f"{len(commands_list)} comandos"
            )
            pages.append(embed)

        return pages

    @app_commands.command(
        name="ayuda",
        description="Muestra automáticamente los comandos slash de ROOTGHOST.",
    )
    @app_commands.guild_only()
    async def ayuda(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "Este comando solo funciona dentro de un servidor.",
                ephemeral=True,
            )
            return

        commands_list = self._registered_commands(interaction.guild)

        # Evita que /ayuda se cuente a sí mismo como una entrada más.
        commands_list = [command for command in commands_list if command.name != "ayuda"]
        pages = self._make_pages(interaction.guild, commands_list)
        view = HelpPages(interaction, pages)

        await interaction.response.send_message(
            embed=pages[0],
            view=view,
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    # Este archivo reemplaza al módulo ayuda.py existente; no lo cargues como otro nombre.
    await bot.add_cog(Ayuda(bot))
