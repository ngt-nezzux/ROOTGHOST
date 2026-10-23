import json
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands
DATA=Path(__file__).resolve().parent.parent/'data'/'rank.json'
def load():
 try:return json.loads(DATA.read_text(encoding='utf-8'))
 except (FileNotFoundError,json.JSONDecodeError):return {}
class Leaderboard(commands.Cog):
 def __init__(self,bot):self.bot=bot
 @app_commands.command(name='leaderboard-xp', description='Mostrar ranking de experiencia del servidor')
 @app_commands.guild_only()
 async def leaderboard(self,i:discord.Interaction):
  users=load().get(str(i.guild_id),{});ranked=sorted(users.items(),key=lambda x:x[1].get('xp',0),reverse=True)[:10];lines=[]
  for n,(uid,p) in enumerate(ranked,1):
   m=i.guild.get_member(int(uid));name=m.display_name if m else f'Usuario {uid}';xp=int(p.get('xp',0));lvl=int((xp/100)**0.5);lines.append(f'**{n}.** {discord.utils.escape_markdown(name)} — Nivel {lvl} · {xp:,} XP')
  e=discord.Embed(title='ROOTGHOST // LEADERBOARD',description='\n'.join(lines) if lines else 'Todavía no hay datos de XP. Este comando usa data/rank.json.',color=0x5865F2);await i.response.send_message(embed=e)
async def setup(bot):await bot.add_cog(Leaderboard(bot))
