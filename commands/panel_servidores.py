
import discord
from discord import app_commands
from discord.ext import commands


class ServidoresPanel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="servidores-panel",
        description="Muestra los servidores donde está ROOTGHOST."
    )
    async def servidores_panel(
        self,
        interaction: discord.Interaction
    ):
        servidores = sorted(
            self.bot.guilds,
            key=lambda guild: guild.member_count or 0,
            reverse=True
        )

        if not servidores:
            await interaction.response.send_message(
                "ROOTGHOST todavía no está conectado a ningún servidor.",
                ephemeral=True
            )
            return

        pagina_tamano = 8
        paginas = [
            servidores[i:i + pagina_tamano]
            for i in range(0, len(servidores), pagina_tamano)
        ]

        async def crear_embed(numero):
            grupo = paginas[numero]
            embed = discord.Embed(
                title="ROOTGHOST // SERVER CONTROL",
                description=(
                    f"**Servidores conectados:** {len(servidores)}\n"
                    f"**Página:** {numero + 1}/{len(paginas)}"
                ),
                color=discord.Color.from_rgb(0, 255, 120)
            )

            for guild in grupo:
                embed.add_field(
                    name=f"🛰️ {guild.name[:100]}",
                    value=(
                        f"**ID:** `{guild.id}`\n"
                        f"**Miembros:** {guild.member_count or 'No disponible'}\n"
                        f"**Propietario ID:** `{guild.owner_id}`"
                    ),
                    inline=False
                )

            embed.set_footer(text="ROOTGHOST SECURITY SYSTEM")
            return embed

        class Navegacion(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=180)
                self.pagina = 0
                self.actualizar_botones()

            def actualizar_botones(self):
                self.anterior.disabled = self.pagina == 0
                self.siguiente.disabled = (
                    self.pagina >= len(paginas) - 1
                )

            async def comprobar_usuario(self, interaction):
                if interaction.user.id != interaction_original.user.id:
                    await interaction.response.send_message(
                        "Este panel no te pertenece.",
                        ephemeral=True
                    )
                    return False
                return True

            @discord.ui.button(
                label="Anterior",
                emoji="◀️",
                style=discord.ButtonStyle.secondary
            )
            async def anterior(self, interaction, button):
                if not await self.comprobar_usuario(interaction):
                    return
                self.pagina -= 1
                self.actualizar_botones()
                await interaction.response.edit_message(
                    embed=await crear_embed(self.pagina),
                    view=self
                )

            @discord.ui.button(
                label="Siguiente",
                emoji="▶️",
                style=discord.ButtonStyle.success
            )
            async def siguiente(self, interaction, button):
                if not await self.comprobar_usuario(interaction):
                    return
                self.pagina += 1
                self.actualizar_botones()
                await interaction.response.edit_message(
                    embed=await crear_embed(self.pagina),
                    view=self
                )

        interaction_original = interaction
        vista = Navegacion()

        await interaction.response.send_message(
            embed=await crear_embed(0),
            view=vista,
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ServidoresPanel(bot))
