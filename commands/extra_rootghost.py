# ROOTGHOST // EXTRA COMMANDS
# Instalar como: ~/ROOTGHOST/commands/extra_rootghost.py
# Requiere discord.py 2.x. Datos persistentes: data/rootghost_extra.json

import asyncio
import json
import time
from pathlib import Path
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / "data"
DATA_FILE = DATA_DIR / "rootghost_extra.json"
COIN = "GhostCoins"


def defaults():
    return {"reputation": {}, "items": {}, "badges": {}, "audit": {},
            "reminders": [], "missions": {}, "rep_cooldowns": {}}


def read_data():
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("invalid data")
    except (OSError, ValueError, json.JSONDecodeError):
        data = {}
    for key, value in defaults().items():
        if not isinstance(data.get(key), type(value)):
            data[key] = value
    return data


class ExtraRootGhost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = read_data()
        self.lock = asyncio.Lock()
        self.reminder_loop.start()

    def cog_unload(self):
        self.reminder_loop.cancel()

    async def save(self):
        async with self.lock:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            temp = DATA_FILE.with_suffix(".tmp")
            temp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
            temp.replace(DATA_FILE)

    def bucket(self, name, guild_id):
        return self.data[name].setdefault(str(guild_id), {})

    async def audit(self, guild, actor, action, detail):
        entries = self.bucket("audit", guild.id).setdefault("entries", [])
        entries.append({"time": int(time.time()), "actor": str(actor)[:100],
                        "action": str(action)[:80], "detail": str(detail)[:250]})
        del entries[:-100]
        await self.save()

    def rank_stats(self, guild_id, user_id):
        try:
            data = json.loads((BASE / "data" / "rank.json").read_text(encoding="utf-8"))
            stats = data.get(str(guild_id), {}).get(str(user_id), {})
            return max(0, int(stats.get("xp", 0) or 0)), max(0, int(stats.get("messages", 0) or 0))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return 0, 0

    @app_commands.command(name="reputacion", description="Da reputación a un miembro (una vez cada 24 h).")
    @app_commands.guild_only()
    @app_commands.describe(miembro="Miembro que recibirá reputación", motivo="Motivo breve")
    async def reputacion(self, interaction: discord.Interaction, miembro: discord.Member, motivo: str = "Buena contribución"):
        if miembro.bot or miembro.id == interaction.user.id:
            return await interaction.response.send_message("Elige a otro miembro que no sea un bot.", ephemeral=True)
        key = f"{interaction.guild_id}:{interaction.user.id}"
        now = int(time.time())
        last = int(self.data["rep_cooldowns"].get(key, 0))
        if now - last < 86400:
            hours = (86400 - (now - last)) // 3600
            return await interaction.response.send_message(f"Ya diste reputación hoy. Vuelve en aproximadamente {hours} h.", ephemeral=True)
        reps = self.bucket("reputation", interaction.guild_id)
        reps[str(miembro.id)] = int(reps.get(str(miembro.id), 0)) + 1
        self.data["rep_cooldowns"][key] = now
        await self.audit(interaction.guild, interaction.user, "reputacion", f"{miembro}: {motivo}")
        await interaction.response.send_message(f"⭐ {interaction.user.mention} dio reputación a {miembro.mention}.\nTotal: **{reps[str(miembro.id)]}**\nMotivo: {discord.utils.escape_mentions(motivo[:250])}")

    @app_commands.command(name="logros", description="Consulta logros desbloqueados y próximos objetivos.")
    @app_commands.guild_only()
    @app_commands.describe(miembro="Miembro a consultar")
    async def logros(self, interaction: discord.Interaction, miembro: discord.Member = None):
        m = miembro or interaction.user
        xp, messages = self.rank_stats(interaction.guild_id, m.id)
        rep = int(self.bucket("reputation", interaction.guild_id).get(str(m.id), 0))
        checks = [(messages >= 1, "👋 Primer mensaje"), (messages >= 100, "💬 100 mensajes"),
                  (xp >= 1000, "⚡ 1.000 XP"), (xp >= 5000, "🔥 5.000 XP"), (rep >= 5, "⭐ 5 reputaciones")]
        unlocked = [name for ok, name in checks if ok]
        locked = [name for ok, name in checks if not ok]
        e = discord.Embed(title=f"ROOTGHOST // LOGROS · {m.display_name}", color=0x5865F2)
        e.set_thumbnail(url=m.display_avatar.url)
        e.add_field(name=f"Desbloqueados ({len(unlocked)})", value="\n".join(unlocked) or "Todavía ninguno.", inline=False)
        e.add_field(name="Próximos objetivos", value="\n".join("• " + x for x in locked) or "¡Todos completados!", inline=False)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="inventario", description="Consulta el inventario de un miembro.")
    @app_commands.guild_only()
    @app_commands.describe(miembro="Miembro a consultar")
    async def inventario(self, interaction: discord.Interaction, miembro: discord.Member = None):
        m = miembro or interaction.user
        items = self.bucket("items", interaction.guild_id).get(str(m.id), [])
        lines = [f"• **{discord.utils.escape_markdown(str(x.get('name', 'Objeto')))}** ×{max(1, int(x.get('quantity', 1)))}" for x in items[:25]]
        e = discord.Embed(title="ROOTGHOST // INVENTARIO", description=f"Inventario de {m.mention}", color=0x5865F2)
        e.add_field(name="Objetos", value="\n".join(lines) if lines else "Vacío por ahora. Se puede conectar con la tienda existente.", inline=False)
        e.set_thumbnail(url=m.display_avatar.url)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="misiones", description="Consulta tus misiones diarias.")
    @app_commands.guild_only()
    @app_commands.describe(miembro="Miembro a consultar")
    async def misiones(self, interaction: discord.Interaction, miembro: discord.Member = None):
        m = miembro or interaction.user
        _, messages = self.rank_stats(interaction.guild_id, m.id)
        rep = int(self.bucket("reputation", interaction.guild_id).get(str(m.id), 0))
        today = datetime.now(timezone.utc).date().isoformat()
        user_data = self.bucket("missions", interaction.guild_id).setdefault(str(m.id), {})
        if user_data.get("date") != today:
            user_data.update({"date": today, "claimed": []})
            await self.save()
        lines = [
            f"**Enviar 10 mensajes** — `{min(messages, 10)}/10` · recompensa informativa: 100 {COIN}",
            f"**Recibir reputación** — `{min(rep, 1)}/1` · recompensa informativa: 75 {COIN}",
        ]
        e = discord.Embed(title="ROOTGHOST // MISIONES DIARIAS", description="\n\n".join(lines), color=0x57F287)
        e.set_footer(text="Las recompensas son informativas; todavía no modifican la economía.")
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="insignias", description="Muestra las insignias de un miembro.")
    @app_commands.guild_only()
    @app_commands.describe(miembro="Miembro a consultar")
    async def insignias(self, interaction: discord.Interaction, miembro: discord.Member = None):
        m = miembro or interaction.user
        badges = self.bucket("badges", interaction.guild_id).get(str(m.id), [])
        e = discord.Embed(title="ROOTGHOST // INSIGNIAS", description=f"Insignias de {m.mention}", color=0x5865F2)
        e.add_field(name="Colección", value="\n".join("🏅 " + discord.utils.escape_markdown(str(x)) for x in badges[:25]) or "Todavía no tiene insignias.", inline=False)
        e.set_thumbnail(url=m.display_avatar.url)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="auditoria", description="Consulta las últimas acciones registradas por este módulo.")
    @app_commands.guild_only()
    @app_commands.default_permissions(view_audit_log=True)
    @app_commands.describe(cantidad="Entradas a mostrar (1-15)")
    async def auditoria(self, interaction: discord.Interaction, cantidad: app_commands.Range[int, 1, 15] = 10):
        if not interaction.user.guild_permissions.view_audit_log:
            return await interaction.response.send_message("Necesitas el permiso Ver registro de auditoría.", ephemeral=True)
        entries = self.bucket("audit", interaction.guild_id).get("entries", [])[-cantidad:]
        if not entries:
            return await interaction.response.send_message("Todavía no hay acciones registradas por este módulo.", ephemeral=True)
        lines = [f"<t:{int(x['time'])}:R> · **{discord.utils.escape_markdown(x['action'])}** · {discord.utils.escape_mentions(x['actor'])}\n{discord.utils.escape_mentions(x['detail'])}" for x in reversed(entries)]
        e = discord.Embed(title="ROOTGHOST // AUDITORÍA", description="\n\n".join(lines)[:4000], color=0xED4245)
        e.set_footer(text="Se conservan las últimas 100 entradas del módulo.")
        await interaction.response.send_message(embed=e, ephemeral=True)

    @app_commands.command(name="diagnostico", description="Revisa latencia y extensiones cargadas.")
    @app_commands.guild_only()
    async def diagnostico(self, interaction: discord.Interaction):
        ms = round(self.bot.latency * 1000)
        exts = list(self.bot.extensions)
        e = discord.Embed(title="ROOTGHOST // DIAGNÓSTICO", color=0x57F287 if ms < 250 else 0xFEE75C)
        e.add_field(name="Estado", value="🟢 Online", inline=True)
        e.add_field(name="Latencia", value=f"{ms} ms", inline=True)
        e.add_field(name="Extensiones", value=f"{len(exts)} cargadas", inline=True)
        e.add_field(name="Módulos", value=", ".join(f"`{x}`" for x in exts[:20]) or "Ninguno", inline=False)
        await interaction.response.send_message(embed=e, ephemeral=True)

    @app_commands.command(name="recordatorio", description="Te envía un recordatorio por mensaje privado.")
    @app_commands.guild_only()
    @app_commands.describe(minutos="Minutos hasta el recordatorio (1-10080)", texto="Qué quieres recordar")
    async def recordatorio(self, interaction: discord.Interaction, minutos: app_commands.Range[int, 1, 10080], texto: app_commands.Range[str, 1, 300]):
        due = int(time.time()) + int(minutos) * 60
        self.data["reminders"].append({"due": due, "user_id": interaction.user.id, "text": str(texto), "id": f"{interaction.user.id}-{due}-{len(self.data['reminders'])}"})
        await self.save()
        await interaction.response.send_message(f"🔔 Listo. Te avisaré por privado <t:{due}:R>.", ephemeral=True)

    @tasks.loop(seconds=20)
    async def reminder_loop(self):
        now = int(time.time())
        due = [x for x in self.data["reminders"] if int(x.get("due", now + 1)) <= now]
        if not due:
            return
        ids = {x["id"] for x in due}
        self.data["reminders"] = [x for x in self.data["reminders"] if x.get("id") not in ids]
        await self.save()
        for x in due:
            try:
                user = self.bot.get_user(int(x["user_id"])) or await self.bot.fetch_user(int(x["user_id"]))
                await user.send(f"🔔 **ROOTGHOST — Recordatorio**\n{discord.utils.escape_mentions(x['text'])}")
            except (discord.HTTPException, KeyError, ValueError):
                pass

    @reminder_loop.before_loop
    async def before_reminder_loop(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="encuesta", description="Crea una encuesta con 2 a 5 opciones.")
    @app_commands.guild_only()
    @app_commands.describe(pregunta="Pregunta", opcion1="Primera opción", opcion2="Segunda opción", opcion3="Tercera opción (opcional)", opcion4="Cuarta opción (opcional)", opcion5="Quinta opción (opcional)")
    async def encuesta(self, interaction: discord.Interaction, pregunta: app_commands.Range[str, 1, 200], opcion1: app_commands.Range[str, 1, 80], opcion2: app_commands.Range[str, 1, 80], opcion3: app_commands.Range[str, 1, 80] = None, opcion4: app_commands.Range[str, 1, 80] = None, opcion5: app_commands.Range[str, 1, 80] = None):
        options = [x.strip() for x in (opcion1, opcion2, opcion3, opcion4, opcion5) if x and x.strip()]
        if len(set(x.casefold() for x in options)) != len(options):
            return await interaction.response.send_message("No repitas opciones.", ephemeral=True)
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        e = discord.Embed(title="ROOTGHOST // ENCUESTA", description=f"**{discord.utils.escape_mentions(pregunta)}**\n\n" + "\n".join(f"{emojis[i]} {discord.utils.escape_mentions(x)}" for i, x in enumerate(options)), color=0x5865F2)
        e.set_footer(text=f"Creada por {interaction.user.display_name}")
        await interaction.response.send_message(embed=e)
        msg = await interaction.original_response()
        for emoji in emojis[:len(options)]:
            try:
                await msg.add_reaction(emoji)
            except discord.HTTPException:
                break
        await self.audit(interaction.guild, interaction.user, "encuesta", pregunta)

    @app_commands.command(name="tarjeta", description="Muestra una tarjeta con estadísticas sociales.")
    @app_commands.guild_only()
    @app_commands.describe(miembro="Miembro a consultar")
    async def tarjeta(self, interaction: discord.Interaction, miembro: discord.Member = None):
        m = miembro or interaction.user
        xp, messages = self.rank_stats(interaction.guild_id, m.id)
        level = int((xp / 100) ** 0.5)
        rep = int(self.bucket("reputation", interaction.guild_id).get(str(m.id), 0))
        e = discord.Embed(title="ROOTGHOST // USER CARD", description=f"## {discord.utils.escape_markdown(m.display_name)}\n`LEVEL {level}`\n\n**XP:** {xp:,}\n**Mensajes:** {messages:,}\n**Reputación:** {rep}\n**Cuenta creada:** <t:{int(m.created_at.timestamp())}:D>", color=0x5865F2)
        e.set_thumbnail(url=m.display_avatar.url)
        e.set_footer(text="ROOTGHOST COMMUNITY SYSTEM")
        await interaction.response.send_message(embed=e)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.audit(member.guild, "Discord", "member_join", f"Se unió {member}")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.audit(member.guild, "Discord", "member_remove", f"Salió {member}")

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await self.audit(guild, "Discord", "member_ban", f"Usuario baneado: {user}")

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        await self.audit(guild, "Discord", "member_unban", f"Usuario desbaneado: {user}")


async def setup(bot):
    await bot.add_cog(ExtraRootGhost(bot))
