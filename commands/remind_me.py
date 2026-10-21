import asyncio
import discord
from discord import app_commands
from discord.ext import commands


class RemindMe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tasks = set()

    @app_commands.command(name="remind-me", description="Programa un recordatorio privado.")
    @app_commands.describe(minutos="Cuántos minutos faltan (1 a 10080)", mensaje="Texto del recordatorio")
    async def remind_me(self, interaction: discord.Interaction, minutos: app_commands.Range[int, 1, 10080], mensaje: app_commands.Range[str, 1, 500]):
        await interaction.response.send_message(
            f"Recordatorio programado para dentro de {minutos} minuto(s). Aviso: los recordatorios pendientes se pierden si ROOTGHOST se reinicia.",
            ephemeral=True
        )
        async def deliver():
            await asyncio.sleep(minutos * 60)
            try:
                await interaction.user.send(f"⏰ **ROOTGHOST // RECORDATORIO**\n{mensaje}")
            except (discord.Forbidden, discord.HTTPException):
                try:
                    channel = interaction.channel
                    if channel:
                        await channel.send(
                            f"{interaction.user.mention}, tu recordatorio: {mensaje}",
                            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False)
                        )
                except discord.HTTPException:
                    pass
        task = asyncio.create_task(deliver())
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

async def setup(bot):
    await bot.add_cog(RemindMe(bot))
