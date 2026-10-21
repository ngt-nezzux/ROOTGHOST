import os,time,platform
import discord
from discord import app_commands
from discord.ext import commands
class Health(commands.Cog):
 def __init__(self,bot):self.bot=bot;self.started=time.monotonic()
 @app_commands.command(name='health',description='Comprobar estado básico del bot')
 async def health(self,i:discord.Interaction):
  ms=round(self.bot.latency*1000) if self.bot.latency is not None else 0;u=int(time.monotonic()-self.started);d,r=divmod(u,86400);h,r=divmod(r,3600);m,s=divmod(r,60)
  e=discord.Embed(title='ROOTGHOST // HEALTH CHECK',color=0x2ECC71 if ms<250 else 0xE67E22);e.add_field(name='Gateway',value='Conectado' if self.bot.is_ready() else 'No listo');e.add_field(name='Latencia',value=f'{ms} ms');e.add_field(name='Tiempo activo',value=f'{d}d {h}h {m}m {s}s');e.add_field(name='Python',value=platform.python_version())
  try:
   import psutil;e.add_field(name='RAM del proceso',value=f'{psutil.Process(os.getpid()).memory_info().rss/1024**2:.1f} MB')
  except ImportError:e.add_field(name='RAM',value='Instalá psutil para medirla')
  await i.response.send_message(embed=e,ephemeral=True)
async def setup(bot):await bot.add_cog(Health(bot))
