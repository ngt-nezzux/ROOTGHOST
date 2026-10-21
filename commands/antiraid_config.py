import json, time
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands
DATA=Path(__file__).resolve().parent.parent/'data'/'antiraid.json'
def load():
 try:return json.loads(DATA.read_text(encoding='utf-8'))
 except (FileNotFoundError,json.JSONDecodeError):return {}
def save(d):
 DATA.parent.mkdir(parents=True,exist_ok=True); DATA.write_text(json.dumps(d,indent=2),encoding='utf-8')
class AntiRaid(commands.Cog):
 def __init__(self,bot):self.bot=bot;self.joins={}
 @app_commands.command(name='antiraid-config',description='Configurar alertas por entradas masivas')
 @app_commands.default_permissions(manage_guild=True)
 @app_commands.guild_only()
 async def config(self,i:discord.Interaction,umbral:app_commands.Range[int,3,30],ventana_segundos:app_commands.Range[int,10,300]=30,canal:discord.TextChannel=None):
  if not i.user.guild_permissions.manage_guild:return await i.response.send_message('Necesitás Administrar servidor.',ephemeral=True)
  d=load();d[str(i.guild_id)]={'threshold':umbral,'window':ventana_segundos,'channel_id':canal.id if canal else None};save(d)
  await i.response.send_message(f'Alertas configuradas: {umbral} entradas en {ventana_segundos}s.',ephemeral=True)
 @commands.Cog.listener()
 async def on_member_join(self,m):
  cfg=load().get(str(m.guild.id),{});now=time.monotonic();key=m.guild.id
  ts=[t for t in self.joins.get(key,[]) if now-t<=cfg.get('window',30)];ts.append(now);self.joins[key]=ts
  if not cfg or len(ts)<cfg['threshold']:return
  self.joins[key]=[];ch=m.guild.get_channel(cfg.get('channel_id')) if cfg.get('channel_id') else None
  if ch:
   try:await ch.send(f'⚠️ ROOTGHOST ANTIRAID: {len(ts)} entradas en {cfg["window"]} segundos. Revisá la actividad.')
   except discord.HTTPException:pass
async def setup(bot):await bot.add_cog(AntiRaid(bot))
