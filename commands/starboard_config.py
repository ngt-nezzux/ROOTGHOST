import json
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands
DATA=Path(__file__).resolve().parent.parent/'data'/'starboard.json'
def load():
 try:return json.loads(DATA.read_text(encoding='utf-8'))
 except (FileNotFoundError,json.JSONDecodeError):return {}
def save(d):DATA.parent.mkdir(parents=True,exist_ok=True);DATA.write_text(json.dumps(d,indent=2),encoding='utf-8')
class Starboard(commands.Cog):
 def __init__(self,bot):self.bot=bot;self.sent=set()
 @app_commands.command(name='starboard-config',description='Configurar canal de mensajes destacados')
 @app_commands.default_permissions(manage_guild=True)
 @app_commands.guild_only()
 async def config(self,i:discord.Interaction,canal:discord.TextChannel,votos:app_commands.Range[int,2,20]=3):
  if not i.user.guild_permissions.manage_guild:return await i.response.send_message('Necesitás Administrar servidor.',ephemeral=True)
  d=load();d[str(i.guild_id)]={'channel_id':canal.id,'threshold':votos};save(d);await i.response.send_message(f'Starboard: {canal.mention}, mínimo {votos} ⭐.',ephemeral=True)
 @commands.Cog.listener()
 async def on_raw_reaction_add(self,p):
  if str(p.emoji)!='⭐' or not p.guild_id:return
  cfg=load().get(str(p.guild_id),{})
  if not cfg:return
  try:
   src=self.bot.get_channel(p.channel_id);msg=await src.fetch_message(p.message_id);react=discord.utils.get(msg.reactions,emoji='⭐')
   if not react or react.count<cfg['threshold'] or msg.id in self.sent:return
   dst=self.bot.get_channel(cfg['channel_id'])
   if not isinstance(dst,discord.TextChannel):return
   e=discord.Embed(description=msg.content[:3500] or '*Mensaje sin texto*',color=0xF1C40F);e.add_field(name='Autor',value=msg.author.mention);e.add_field(name='Canal',value=msg.channel.mention);e.add_field(name='Mensaje',value=f'[Abrir]({msg.jump_url})');e.set_footer(text=f'⭐ {react.count} · ROOTGHOST STARBOARD')
   await dst.send(embed=e,allowed_mentions=discord.AllowedMentions.none());self.sent.add(msg.id)
  except (discord.Forbidden,discord.HTTPException,AttributeError,KeyError):pass
async def setup(bot):await bot.add_cog(Starboard(bot))
