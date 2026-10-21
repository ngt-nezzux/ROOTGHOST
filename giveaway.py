import asyncio
import random
import discord
from discord import app_commands
from discord.ext import commands


class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tasks = set()

    @app_commands.command(name="giveaway", description="Crear un sorteo sencillo")
    @app_commands.describe(
        premio="Qué se sortea",
        duracion_minutos="Duración entre 1 y 10080 minutos",
        ganadores="Cantidad de ganadores (1 a 10)",
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def giveaway(self, interaction: discord.Interaction, premio: str, duracion_minutos: app_commands.Range[int, 1, 10080], ganadores: app_commands.Range[int, 1, 10] = 1):
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("Necesitás Administrar servidor.", ephemeral=True)
        premio = premio.strip()
        if not premio or len(premio) > 200:
            return await interaction.response.send_message("El premio debe tener entre 1 y 200 caracteres.", ephemeral=True)
        embed = discord.Embed(title="ROOTGHOST // GIVEAWAY", description=f"**Premio:** {premio}\n**Organiza:** {interaction.user.mention}\n**Ganadores:** {ganadores}\n**Finaliza:** en {duracion_minutos} minuto(s)\n\nReaccioná con 🎉 para participar.", color=0x5865F2)
        embed.set_footer(text="El sorteo activo no se recupera si el bot se reinicia.")
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            message = await interaction.channel.send(embed=embed)
            await message.add_reaction("🎉")
        except discord.HTTPException:
            return await interaction.followup.send("No pude publicar el sorteo. Revisá mis permisos.", ephemeral=True)

        async def finish():
            await asyncio.sleep(duracion_minutos * 60)
            try:
                message = await interaction.channel.fetch_message(message.id)
                users = []
                reaction = discord.utils.get(message.reactions, emoji="🎉")
                if reaction:
                    async for user in reaction.users():
                        if not user.bot:
                            users.append(user)
                winners = random.sample(users, min(ganadores, len(users))) if users else []
                result = message.embeds[0].copy()
                result.title = "ROOTGHOST // GIVEAWAY FINALIZADO"
                result.add_field(name="Resultado", value=", ".join(u.mention for u in winners) if winners else "No hubo participantes.", inline=False)
                await message.edit(embed=result)
                if winners:
                    await interaction.channel.send(f"🎉 Felicitaciones {', '.join(u.mention for u in winners)}. Ganaron **{premio}**.", allowed_mentions=discord.AllowedMentions(users=winners))
            except (discord.HTTPException, discord.NotFound):
                pass

        task = asyncio.create_task(finish())
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        await interaction.followup.send(f"Sorteo publicado en {interaction.channel.mention}.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Giveaway(bot))
