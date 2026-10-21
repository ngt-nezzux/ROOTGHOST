import json
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands
DATA=Path(__file__).resolve().parent.parent/'data'/'rules.json'
def load():
 try:return json.loads(DATA.read_text(encoding='utf-8'))
 except (FileNotFoundError,json.JSONDecodeError):return {}
def save(d):DATA.parent.mkdir(parents=True,exist_ok=True);DATA.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding='utf-8')
class RulesView(discord.ui.View):
 def __init__(self,rules):super().__init__(timeout=None);self.rules=rules
 @discord.ui.button(label='Ver reglas',style=discord.ButtonStyle.secondary,custom_id='rootghost:rules:show')
 async def show(self,i,b):await i.response.send_message(self.rules[:1900],ephemeral=True)
class Rules(commands.Cog):
 def __init__(self,bot):self.bot=bot
 async def cog_load(self):
  for cfg in load().values():self.bot.add_view(RulesView(cfg['rules']),message_id=cfg.get('message_id'))
 @app_commands.command(name='rules-setup',description='Publicar panel de reglas con botón')
 @app_commands.default_permissions(manage_guild=True)
 @app_commands.guild_only()
 async def setup_rules(self,i:discord.Interaction,reglas:str):
  if not i.user.guild_permissions.manage_guild:return await i.response.send_message('Necesitás Administrar servidor.',ephemeral=True)
  reglas=reglas.strip()
  if not reglas or len(reglas)>1900:return await i.response.send_message('Las reglas deben tener entre 1 y 1900 caracteres.',ephemeral=True)
  await i.response.defer(ephemeral=True,thinking=True);msg=await i.channel.send(embed=discord.Embed(title='ROOTGHOST // SERVER RULES',description='Consultá las reglas con el botón.',color=0x5865F2),view=RulesView(reglas))
  d=load();d[str(i.guild_id)]={'rules':reglas,'message_id':msg.id};save(d);await i.followup.send('Panel de reglas publicado.',ephemeral=True)
async def setup(bot):await bot.add_cog(Rules(bot))
