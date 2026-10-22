
import os
import re
import json
import time
import asyncio
import urllib.request
import urllib.error

from pathlib import Path
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta

import discord
from discord import app_commands
from discord.ext import commands


# ==========================================================
# ROOTGHOST // OPENAI AI SYSTEM
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_FILE = DATA_DIR / "ia_config.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")

API_URL = "https://api.openai.com/v1/responses"

SYSTEM_PROMPT = """
Sos ROOTGHOST AI, la inteligencia artificial del bot ROOTGHOST.
Respondé en español de forma clara, útil y natural.
Ayudá con Python, Discord, programación, juegos y preguntas generales.
Explicá desde cero cuando la persona sea principiante.
No afirmes que realizaste acciones que no hiciste.
No reveles claves, contraseñas ni datos privados.
Si no sabés algo, reconocé la incertidumbre.
Usá respuestas fáciles de leer en Discord.
"""

INVITE_REGEX = re.compile(
    r"(?:https?://)?(?:www\.)?"
    r"(?:discord\.gg|discord(?:app)?\.com/invite)/[a-zA-Z0-9-]+",
    re.IGNORECASE,
)

historial = defaultdict(lambda: deque(maxlen=8))
ultimo_uso = {}
mensajes_recientes = defaultdict(deque)

COOLDOWN_IA = 8
MAX_PREGUNTA = 1500
MAX_RESPUESTA = 1900


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

def cargar_config():
    predeterminado = {
        "seguridad": True,
        "canal_logs": {}
    }

    if not CONFIG_FILE.exists():
        guardar_config(predeterminado)
        return predeterminado

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        if not isinstance(datos, dict):
            return predeterminado

        predeterminado.update(datos)

        if not isinstance(predeterminado.get("canal_logs"), dict):
            predeterminado["canal_logs"] = {}

        return predeterminado

    except (OSError, json.JSONDecodeError):
        return predeterminado


def guardar_config(config):
    temporal = CONFIG_FILE.with_suffix(".tmp")

    with temporal.open("w", encoding="utf-8") as archivo:
        json.dump(config, archivo, indent=4, ensure_ascii=False)

    temporal.replace(CONFIG_FILE)


CONFIG = cargar_config()


# ==========================================================
# HORA Y FECHA DE ARGENTINA
# ==========================================================

def hora_argentina():
    return datetime.now(timezone(timedelta(hours=-3)))


def obtener_fecha_argentina():
    fecha = hora_argentina()

    dias = [
        "lunes", "martes", "miércoles", "jueves",
        "viernes", "sábado", "domingo"
    ]

    meses = [
        "enero", "febrero", "marzo", "abril",
        "mayo", "junio", "julio", "agosto",
        "septiembre", "octubre", "noviembre", "diciembre"
    ]

    return (
        f"{dias[fecha.weekday()]}, "
        f"{fecha.day} de {meses[fecha.month - 1]} de {fecha.year}"
    )


def responder_hora_o_fecha(pregunta):
    texto = pregunta.casefold()
    fecha = hora_argentina()

    pide_hora = bool(
        re.search(r"\b(hora|horario)\b", texto)
    )

    pide_fecha = (
        bool(re.search(r"\b(fecha|día|dia)\b", texto))
        or bool(re.search(r"\bhoy\b", texto))
    )

    if pide_hora:
        return (
            "🕒 **Hora de Argentina**\n"
            f"Son las **{fecha:%H:%M}** (UTC−3)."
        )

    if pide_fecha:
        return (
            "📅 **Fecha de Argentina**\n"
            f"Hoy es **{obtener_fecha_argentina()}**."
        )

    return None


# ==========================================================
# CONEXIÓN CON OPENAI
# ==========================================================

def llamada_openai(pregunta, conversaciones):
    if not OPENAI_API_KEY:
        raise RuntimeError("Falta configurar OPENAI_API_KEY.")

    entradas = []

    for pregunta_anterior, respuesta_anterior in conversaciones:
        entradas.append({
            "role": "user",
            "content": pregunta_anterior
        })

        entradas.append({
            "role": "assistant",
            "content": respuesta_anterior
        })

    entradas.append({
        "role": "user",
        "content": pregunta
    })

    cuerpo = {
        "model": OPENAI_MODEL,
        "instructions": SYSTEM_PROMPT,
        "input": entradas,
        "max_output_tokens": 900,
        "store": False
    }

    solicitud = urllib.request.Request(
        API_URL,
        data=json.dumps(cuerpo).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(solicitud, timeout=45) as respuesta:
            datos = json.loads(
                respuesta.read().decode("utf-8")
            )
    except urllib.error.HTTPError as error:
        detalle = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"OpenAI API devolvió HTTP {error.code}: {detalle[:500]}"
        ) from error

    partes_texto = []

    for elemento in datos.get("output", []):
        if elemento.get("type") != "message":
            continue

        for parte in elemento.get("content", []):
            if parte.get("type") == "output_text":
                texto = parte.get("text", "")
                if texto:
                    partes_texto.append(texto)

    resultado = "\n".join(partes_texto).strip()

    if not resultado:
        raise RuntimeError("OpenAI no devolvió una respuesta de texto.")

    return resultado[:MAX_RESPUESTA]


# ==========================================================
# COG PRINCIPAL
# ==========================================================

class RootGhostAI(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def registrar_incidente(self, guild, descripcion):
        canal_id = CONFIG.get("canal_logs", {}).get(str(guild.id))

        if not canal_id:
            return

        canal = guild.get_channel(int(canal_id))

        if canal is None:
            return

        try:
            await canal.send(
                f"🛡️ **ROOTGHOST SECURITY**\n{descripcion}",
                allowed_mentions=discord.AllowedMentions.none()
            )
        except (discord.Forbidden, discord.HTTPException):
            pass

    async def generar_respuesta(self, pregunta, clave):
        conversacion = list(historial[clave])

        respuesta = await asyncio.to_thread(
            llamada_openai,
            pregunta,
            conversacion
        )

        historial[clave].append((pregunta, respuesta))
        return respuesta

    # ------------------------------------------------------
    # /ia
    # ------------------------------------------------------

    @app_commands.command(
        name="ia",
        description="Preguntale algo a ROOTGHOST AI."
    )
    @app_commands.describe(
        pregunta="Escribí tu pregunta para la inteligencia artificial."
    )
    async def ia(
        self,
        interaction: discord.Interaction,
        pregunta: str
    ):
        pregunta = pregunta.strip()

        if not pregunta:
            await interaction.response.send_message(
                "Escribí una pregunta.",
                ephemeral=True
            )
            return

        if len(pregunta) > MAX_PREGUNTA:
            await interaction.response.send_message(
                f"La pregunta no puede superar {MAX_PREGUNTA} caracteres.",
                ephemeral=True
            )
            return

        clave = (interaction.guild_id, interaction.user.id)
        ahora = time.monotonic()
        restante = COOLDOWN_IA - (
            ahora - ultimo_uso.get(clave, 0)
        )

        if restante > 0:
            await interaction.response.send_message(
                f"⏳ Esperá {restante:.1f} segundos antes de preguntar de nuevo.",
                ephemeral=True
            )
            return

        ultimo_uso[clave] = ahora

        directa = responder_hora_o_fecha(pregunta)

        if directa:
            await interaction.response.send_message(directa)
            return

        await interaction.response.defer(thinking=True)

        try:
            respuesta = await self.generar_respuesta(pregunta, clave)

            await interaction.followup.send(
                respuesta,
                allowed_mentions=discord.AllowedMentions.none()
            )

        except Exception as error:
            print(f"[ROOTGHOST OPENAI] {error}")

            await interaction.followup.send(
                "⚠️ No pude obtener una respuesta de la IA. "
                "Revisá la API key, el modelo y la conexión.",
                allowed_mentions=discord.AllowedMentions.none()
            )

    # ------------------------------------------------------
    # /ia-reset
    # ------------------------------------------------------

    @app_commands.command(
        name="ia-reset",
        description="Reinicia tu historial temporal con la IA."
    )
    async def ia_reset(self, interaction: discord.Interaction):
        clave = (interaction.guild_id, interaction.user.id)
        historial.pop(clave, None)

        await interaction.response.send_message(
            "🧠 Historial temporal reiniciado.",
            ephemeral=True
        )

    # ------------------------------------------------------
    # /ia-seguridad
    # ------------------------------------------------------

    @app_commands.command(
        name="ia-seguridad",
        description="Activa o desactiva los filtros básicos de seguridad."
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(
        habilitada="Activar o desactivar los filtros."
    )
    async def ia_seguridad(
        self,
        interaction: discord.Interaction,
        habilitada: bool
    ):
        CONFIG["seguridad"] = habilitada
        guardar_config(CONFIG)

        estado = "activada" if habilitada else "desactivada"

        await interaction.response.send_message(
            f"🛡️ Seguridad básica {estado}.",
            ephemeral=True
        )

    # ------------------------------------------------------
    # /ia-log
    # ------------------------------------------------------

    @app_commands.command(
        name="ia-log",
        description="Configura el canal de registros de seguridad."
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(
        canal="Canal donde se registrarán los incidentes."
    )
    async def ia_log(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel
    ):
        CONFIG.setdefault("canal_logs", {})[
            str(interaction.guild_id)
        ] = canal.id

        guardar_config(CONFIG)

        await interaction.response.send_message(
            f"✅ Los registros se enviarán a {canal.mention}.",
            ephemeral=True
        )

    # ------------------------------------------------------
    # MENSAJES AUTOMÁTICOS: Rg pregunta
    # ------------------------------------------------------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        contenido = message.content.strip()

        if not contenido:
            return

        puede_moderar = (
            message.author.guild_permissions.administrator
            or message.author.guild_permissions.manage_guild
        )

        # FILTROS BÁSICOS DE SEGURIDAD
        if CONFIG.get("seguridad", True) and not puede_moderar:

            if INVITE_REGEX.search(contenido):
                try:
                    await message.delete()

                    await self.registrar_incidente(
                        message.guild,
                        f"Invitación de Discord eliminada. "
                        f"Usuario: {message.author} | "
                        f"Canal: #{message.channel.name}"
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass

                return

            clave_spam = (message.guild.id, message.author.id)
            ahora = time.monotonic()
            registros = mensajes_recientes[clave_spam]

            registros.append(ahora)

            while registros and ahora - registros[0] > 7:
                registros.popleft()

            if len(registros) >= 5:
                registros.clear()

                try:
                    await message.delete()
                except (discord.Forbidden, discord.HTTPException):
                    pass

                await self.registrar_incidente(
                    message.guild,
                    f"Posible spam detectado. "
                    f"Usuario: {message.author} | "
                    f"Canal: #{message.channel.name}"
                )
                return

        # DETECTAR RG AL PRINCIPIO DEL MENSAJE
        coincidencia = re.match(
            r"^\s*rg\b[\s,:-]*(.*)$",
            contenido,
            re.IGNORECASE
        )

        if not coincidencia:
            return

        pregunta = coincidencia.group(1).strip()

        if not pregunta:
            await message.reply(
                "🧠 Escribí tu pregunta después de `Rg`.\n"
                "Ejemplo: `Rg explicame qué es Python`",
                mention_author=False,
                allowed_mentions=discord.AllowedMentions.none()
            )
            return

        if len(pregunta) > MAX_PREGUNTA:
            await message.reply(
                f"La pregunta no puede superar {MAX_PREGUNTA} caracteres.",
                mention_author=False
            )
            return

        clave = (message.guild.id, message.author.id)
        ahora = time.monotonic()
        restante = COOLDOWN_IA - (
            ahora - ultimo_uso.get(clave, 0)
        )

        if restante > 0:
            await message.reply(
                f"⏳ Esperá {restante:.1f} segundos para volver a preguntar.",
                mention_author=False,
                allowed_mentions=discord.AllowedMentions.none()
            )
            return

        ultimo_uso[clave] = ahora

        directa = responder_hora_o_fecha(pregunta)

        if directa:
            await message.reply(
                directa,
                mention_author=False,
                allowed_mentions=discord.AllowedMentions.none()
            )
            return

        async with message.channel.typing():
            try:
                respuesta = await self.generar_respuesta(pregunta, clave)

                await message.reply(
                    respuesta,
                    mention_author=False,
                    allowed_mentions=discord.AllowedMentions.none()
                )

            except Exception as error:
                print(f"[ROOTGHOST OPENAI] {error}")

                await message.reply(
                    "⚠️ No pude obtener una respuesta de la IA. "
                    "Intentá de nuevo más tarde.",
                    mention_author=False,
                    allowed_mentions=discord.AllowedMentions.none()
                )


async def setup(bot):
    await bot.add_cog(RootGhostAI(bot))
