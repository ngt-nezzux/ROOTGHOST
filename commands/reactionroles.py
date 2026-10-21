import json
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands
DATA=Path(__file__).resolve().parent.parent/'data'/'reactionroles.json'
def load():
 try:return json.loads(DATA.read_text(encoding='utf-8'))
 except (FileNotFoundError,json.JSONDecodeError):return {}
def save(d):DATA.parent.mkdir(parents=True,exist_ok=True);DATA.write_text(json.dumps(d,indent=2),encoding='utf-8')
class RoleButton(discord.ui.Button):
 def __init__(self,rid,label):super().__init__(label=label[:80],style=discord.ButtonStyle.secondary,custom_id=f'rootghost:rr:{rid}');self.rid=rid
 async def callback(self,i):
  role=i.guild.get_role(self.rid) if i.guild else None
  if not role:return await i.response.send_message('Ese rol ya no existe.',ephemeral=True)
  if role.is_default() or role.managed or role>=i.guild.me.top_role:return await i.response.send_message('No puedo asignar ese rol por la jerarquía.',ephemeral=True)
  try:
   if role in i.user.roles:await i.user.remove_roles(role,reason='ROOTGHOST role panel');msg=f'Rol quitado: {role.name}'
   else:await i.user.add_roles(role,reason='ROOTGHOST role panel');msg=f'Rol asignado: {role.name}'
   await i.response.send_message(msg,ephemeral=True)
  except discord.Forbidden:await i.response.send_message('Me falta Gestionar roles.',ephemeral=True)
class RoleView(discord.ui.View):
 def __init__(self,roles):
  super().__init__(timeout=None)
  for rid,label in roles:self.add_item(RoleButton(rid,label))
class ReactionRoles(commands.Cog):
 def __init__(self,bot):self.bot=bot
 async def cog_load(self):
  for panels in load().values():
   for p in panels:self.bot.add_view(RoleView([(int(r['id']),r['label']) for r in p['roles']]),message_id=p['message_id'])
 @app_commands.command(name='reactionroles',description='Publicar panel de roles con botones')
 @app_commands.default_permissions(manage_roles=True)
 @app_commands.guild_only()
 async def panel(self,i:discord.Interaction,rol1:discord.Role,rol2:discord.Role=None,rol3:discord.Role=None,rol4:discord.Role=None):
  if not i.user.guild_permissions.manage_roles:return await i.response.send_message('Necesitás Gestionar roles.',ephemeral=True)
  roles=list(dict.fromkeys(r for r in (rol1,rol2,rol3,rol4) if r))
  if not i.guild.me.guild_permissions.manage_roles:return await i.response.send_message('Al bot le falta Gestionar roles.',ephemeral=True)
  for r in roles:
   if r.is_default() or r.managed or r>=i.guild.me.top_role:return await i.response.send_message(f'El rol {r.name} no se puede ofrecer por la jerarquía.',ephemeral=True)
  view=RoleView([(r.id,r.name) for r in roles]);embed=discord.Embed(title='ROOTGHOST // ROLE SELECTION',description='Presioná un botón para obtener o quitar un rol.',color=0x5865F2)
  await i.response.defer(ephemeral=True,thinking=True);msg=await i.channel.send(embed=embed,view=view)
  d=load();d.setdefault(str(i.guild_id),[]).append({'message_id':msg.id,'roles':[{'id':r.id,'label':r.name} for r in roles]});save(d)
  await i.followup.send('Panel de roles publicado.',ephemeral=True)
async def setup(bot):await bot.add_cog(ReactionRoles(bot))
