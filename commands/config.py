import json
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands
DATA=Path(__file__).resolve().parent.parent/'data'
FILES={'Reportes':'report.json','Antiraid':'antiraid.json','Voces temporales':'tempvoice.json','Solicitudes staff':'staff_apply.json','Starboard':'starboard.json','Reglas':'rules.json','Sugerencias':'suggestion_config.json','Captcha':'captcha.json','Bienvenida':'welcome.json','Tickets':'tickets.json'}
def read(name):
 try:return json.loads((DATA/name).read_text(encoding='utf-8'))
 except (FileNotFoundError,json.JSONDecodeError):return {}
class Config(commands.Cog):
 def __init__(self,bot):self.bot=bot
 @app_commands.command(name='config',description='Ver resumen de ajustes de ROOTGHOST')
 @app_commands.default_permissions(manage_guild=True)
 @app_commands.guild_only()
 async def config(self,i:discord.Interaction):
  if not i.user.guild_permissions.manage_guild:return await i.response.send_message('Necesitás Administrar servidor.',ephemeral=True)
  gid=str(i.guild_id);lines=[f'{"✅" if gid in read(fn) and read(fn)[gid] else "➖"} **{label}:** {"configurado" if gid in read(fn) and read(fn)[gid] else "sin configuración detectada"}' for label,fn in FILES.items()]
  e=discord.Embed(title='ROOTGHOST // CONFIGURATION',description='\n'.join(lines),color=0x5865F2);e.set_footer(text='Detecta archivos locales; no valida permisos ni funcionamiento.');await i.response.send_message(embed=e,ephemeral=True)
async def setup(bot):await bot.add_cog(Config(bot))
