import json
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands
DATA=Path(__file__).resolve().parent.parent/'data'/'cases.json'
def load():
 try:return json.loads(DATA.read_text(encoding='utf-8'))
 except (FileNotFoundError,json.JSONDecodeError):return {}
def save(d):DATA.parent.mkdir(parents=True,exist_ok=True);DATA.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding='utf-8')
class Cases(commands.Cog):
 def __init__(self,bot):self.bot=bot
 @app_commands.command(name='case',description='Consultar casos de moderación guardados')
 @app_commands.default_permissions(moderate_members=True)
 @app_commands.guild_only()
 async def case(self,i:discord.Interaction,miembro:discord.Member):
  if not(i.user.guild_permissions.moderate_members or i.user.guild_permissions.view_audit_log):return await i.response.send_message('Necesitás permisos de moderación.',ephemeral=True)
  cs=load().get(str(i.guild_id),{}).get(str(miembro.id),[])
  await i.response.send_message('\n'.join(f'`#{c["id"]}` **{c["action"]}** — {c["reason"][:120]}' for c in cs[-10:]) if cs else 'No hay casos guardados para este miembro. Los casos no se importan automáticamente del registro de Discord.',ephemeral=True)
 @app_commands.command(name='case-add',description='Guardar manualmente un caso de moderación')
 @app_commands.default_permissions(moderate_members=True)
 @app_commands.guild_only()
 async def add(self,i:discord.Interaction,miembro:discord.Member,accion:str,motivo:str):
  if not i.user.guild_permissions.moderate_members:return await i.response.send_message('Necesitás Moderar miembros.',ephemeral=True)
  if not accion.strip() or len(accion)>40 or not motivo.strip() or len(motivo)>500:return await i.response.send_message('Acción: máximo 40 caracteres; motivo: máximo 500.',ephemeral=True)
  d=load();g=d.setdefault(str(i.guild_id),{});cs=g.setdefault(str(miembro.id),[]);num=sum(map(len,g.values()))+1
  cs.append({'id':num,'action':accion.strip(),'reason':motivo.strip(),'moderator_id':i.user.id,'timestamp':discord.utils.utcnow().isoformat()});save(d)
  await i.response.send_message(f'Caso #{num} guardado para {miembro.mention}.',ephemeral=True)
async def setup(bot):await bot.add_cog(Cases(bot))
