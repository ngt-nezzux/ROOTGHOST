import json
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands
DATA=Path(__file__).resolve().parent.parent/'data'/'tempvoice.json'
def load():
 try:return json.loads(DATA.read_text(encoding='utf-8'))
 except (FileNotFoundError,json.JSONDecodeError):return {}
def save(d):DATA.parent.mkdir(parents=True,exist_ok=True);DATA.write_text(json.dumps(d,indent=2),encoding='utf-8')
class TempVoice(commands.Cog):
 def __init__(self,bot):self.bot=bot
 @app_commands.command(name='tempvoice-setup',description='Configurar un generador de canales de voz temporales')
 @app_commands.default_permissions(manage_channels=True)
 @app_commands.guild_only()
 async def config(self,i:discord.Interaction,generador:discord.VoiceChannel,categoria:discord.CategoryChannel=None):
  if not i.user.guild_permissions.manage_channels:return await i.response.send_message('Necesitás Gestionar canales.',ephemeral=True)
  if not i.guild.me.guild_permissions.manage_channels:return await i.response.send_message('Al bot le falta Gestionar canales.',ephemeral=True)
  d=load();d[str(i.guild_id)]={'generator_id':generador.id,'category_id':categoria.id if categoria else generador.category_id};save(d)
  await i.response.send_message(f'Generador configurado: {generador.mention}.',ephemeral=True)
 @commands.Cog.listener()
 async def on_voice_state_update(self,m,before,after):
  if before.channel and before.channel.name.startswith('🔊 ') and len(before.channel.members)==0:
   try:await before.channel.delete(reason='ROOTGHOST: sala temporal vacía')
   except (discord.Forbidden,discord.HTTPException):pass
  if m.bot or not after.channel:return
  cfg=load().get(str(m.guild.id),{})
  if after.channel.id!=cfg.get('generator_id'):return
  cat=m.guild.get_channel(cfg.get('category_id')) if cfg.get('category_id') else after.channel.category
  try:
   ch=await m.guild.create_voice_channel(f'🔊 {m.display_name}'[:95],category=cat,overwrites={m:discord.PermissionOverwrite(view_channel=True,connect=True)})
   await m.move_to(ch,reason='ROOTGHOST temporary voice')
  except (discord.Forbidden,discord.HTTPException):pass
async def setup(bot):await bot.add_cog(TempVoice(bot))
