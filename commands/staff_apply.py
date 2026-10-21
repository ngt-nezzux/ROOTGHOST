import json
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands
DATA=Path(__file__).resolve().parent.parent/'data'/'staff_apply.json'
def load():
 try:return json.loads(DATA.read_text(encoding='utf-8'))
 except (FileNotFoundError,json.JSONDecodeError):return {}
def save(d):DATA.parent.mkdir(parents=True,exist_ok=True);DATA.write_text(json.dumps(d,indent=2),encoding='utf-8')
class ApplyModal(discord.ui.Modal,title='Solicitud para el staff'):
 experiencia=discord.ui.TextInput(label='Experiencia moderando',style=discord.TextStyle.paragraph,max_length=800)
 motivo=discord.ui.TextInput(label='¿Por qué querés entrar?',style=discord.TextStyle.paragraph,max_length=800)
 async def on_submit(self,i):
  cfg=load().get(str(i.guild_id),{});ch=i.guild.get_channel(cfg.get('channel_id')) if cfg.get('channel_id') else None
  if not isinstance(ch,discord.TextChannel):return await i.response.send_message('Primero un administrador debe usar /staff-apply-config.',ephemeral=True)
  e=discord.Embed(title='ROOTGHOST // STAFF APPLICATION',color=0x5865F2);e.add_field(name='Solicitante',value=f'{i.user.mention} (`{i.user.id}`)',inline=False);e.add_field(name='Experiencia',value=self.experiencia.value,inline=False);e.add_field(name='Motivo',value=self.motivo.value,inline=False)
  try:await ch.send(embed=e,allowed_mentions=discord.AllowedMentions.none())
  except discord.HTTPException:return await i.response.send_message('No pude enviar la solicitud; revisá permisos.',ephemeral=True)
  await i.response.send_message('Solicitud enviada al staff.',ephemeral=True)
class ApplyView(discord.ui.View):
 def __init__(self):super().__init__(timeout=None)
 @discord.ui.button(label='Postularme',style=discord.ButtonStyle.primary,custom_id='rootghost:staff:apply')
 async def apply(self,i,b):await i.response.send_modal(ApplyModal())
class StaffApply(commands.Cog):
 def __init__(self,bot):self.bot=bot
 async def cog_load(self):self.bot.add_view(ApplyView())
 @app_commands.command(name='staff-apply-config',description='Configurar canal privado de solicitudes')
 @app_commands.default_permissions(manage_guild=True)
 @app_commands.guild_only()
 async def config(self,i:discord.Interaction,canal:discord.TextChannel):
  if not i.user.guild_permissions.manage_guild:return await i.response.send_message('Necesitás Administrar servidor.',ephemeral=True)
  d=load();d[str(i.guild_id)]={'channel_id':canal.id};save(d);await i.response.send_message(f'Canal configurado: {canal.mention}',ephemeral=True)
 @app_commands.command(name='staff-apply',description='Publicar panel de postulaciones')
 @app_commands.default_permissions(manage_guild=True)
 @app_commands.guild_only()
 async def panel(self,i:discord.Interaction):
  if not i.user.guild_permissions.manage_guild:return await i.response.send_message('Necesitás Administrar servidor.',ephemeral=True)
  await i.response.send_message('Panel publicado.',ephemeral=True);await i.channel.send(embed=discord.Embed(title='ROOTGHOST // STAFF APPLICATIONS',description='Presioná el botón para completar una solicitud.',color=0x5865F2),view=ApplyView())
async def setup(bot):await bot.add_cog(StaffApply(bot))
