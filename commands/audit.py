import discord
from discord import app_commands
from discord.ext import commands
class Audit(commands.Cog):
 def __init__(self,bot):self.bot=bot
 @app_commands.command(name='audit',description='Consultar acciones recientes del registro de auditoría')
 @app_commands.default_permissions(view_audit_log=True)
 @app_commands.guild_only()
 async def audit(self,i:discord.Interaction,cantidad:app_commands.Range[int,1,10]=5):
  if not i.user.guild_permissions.view_audit_log:return await i.response.send_message('Necesitás Ver registro de auditoría.',ephemeral=True)
  if not i.guild.me.guild_permissions.view_audit_log:return await i.response.send_message('Al bot le falta Ver registro de auditoría.',ephemeral=True)
  await i.response.defer(ephemeral=True);lines=[]
  try:
   async for e in i.guild.audit_logs(limit=cantidad):lines.append(f'**{e.action.name}** · {e.user or "Desconocido"} · objetivo: `{str(e.target)[:70]}` · {(e.reason or "Sin motivo")[:80]}')
  except discord.Forbidden:return await i.followup.send('Discord denegó el acceso al registro.',ephemeral=True)
  await i.followup.send('\n'.join(lines) if lines else 'No hay entradas disponibles.',ephemeral=True)
async def setup(bot):await bot.add_cog(Audit(bot))
