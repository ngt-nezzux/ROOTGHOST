import discord
from discord import app_commands
from discord.ext import commands
class Slowmode(commands.Cog):
 def __init__(self,bot):self.bot=bot
 @app_commands.command(name='slowmode',description='Configurar el modo lento del canal actual')
 @app_commands.default_permissions(manage_channels=True)
 @app_commands.guild_only()
 async def slowmode(self,i:discord.Interaction,segundos:app_commands.Range[int,0,21600]):
  if not i.user.guild_permissions.manage_channels:return await i.response.send_message('Necesitás Gestionar canales.',ephemeral=True)
  if not isinstance(i.channel,discord.TextChannel):return await i.response.send_message('Solo funciona en canales de texto normales.',ephemeral=True)
  try:await i.channel.edit(slowmode_delay=segundos,reason=f'ROOTGHOST slowmode por {i.user}')
  except discord.Forbidden:return await i.response.send_message('Al bot le falta Gestionar canales.',ephemeral=True)
  except discord.HTTPException:return await i.response.send_message('Discord no pudo cambiar el modo lento.',ephemeral=True)
  await i.response.send_message('Modo lento desactivado.' if segundos==0 else f'Modo lento configurado en {segundos} segundos.',ephemeral=True)
async def setup(bot):await bot.add_cog(Slowmode(bot))
