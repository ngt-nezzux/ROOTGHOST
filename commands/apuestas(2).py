import asyncio
import json
import random
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

# ROOTGHOST // SISTEMA DE APUESTAS
# Compatible con discord.py 2.x y la carga automática de commands/.
# Usa el mismo archivo/esquema que commands/economia.py:
# data/economia.json -> {"users": {"ID": {"balance": 0, "bank": 0, ...}}}

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ECONOMY_FILE = DATA_DIR / "economia.json"
MONEDA = "GhostCoins"
MAX_APUESTA = 1_000_000


def _leer_datos():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not ECONOMY_FILE.exists():
        return {"users": {}}

    try:
        with ECONOMY_FILE.open("r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
    except (json.JSONDecodeError, OSError):
        datos = {"users": {}}

    if not isinstance(datos, dict):
        datos = {"users": {}}
    if not isinstance(datos.get("users"), dict):
        datos["users"] = {}
    return datos


def _guardar_datos(datos):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporal = ECONOMY_FILE.with_suffix(".tmp")
    with temporal.open("w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=4, ensure_ascii=False)
    temporal.replace(ECONOMY_FILE)


def _cuenta(datos, user_id):
    uid = str(user_id)
    cuenta = datos["users"].setdefault(
        uid,
        {"balance": 0, "bank": 0, "daily": 0, "work": 0},
    )
    # Conserva campos existentes y completa los que falten.
    cuenta.setdefault("balance", 0)
    cuenta.setdefault("bank", 0)
    cuenta.setdefault("daily", 0)
    cuenta.setdefault("work", 0)
    return cuenta


class Apuestas(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Reutiliza el candado de Economia para evitar escrituras simultáneas
        # entre los comandos normales de economía y estas apuestas.
        # El lock se resuelve dinámicamente porque apuestas.py puede cargarse
        # antes que economia.py durante la carga automática de extensiones.
        if not hasattr(bot, "_rootghost_economy_lock"):
            bot._rootghost_economy_lock = asyncio.Lock()

    @property
    def lock(self):
        economia = self.bot.get_cog("Economia")
        return getattr(economia, "lock", None) or self.bot._rootghost_economy_lock

    async def _saldo(self, user_id):
        async with self.lock:
            datos = _leer_datos()
            return int(_cuenta(datos, user_id).get("balance", 0))

    async def _apostar_y_resolver(self, user_id, apuesta, multiplicador, gano):
        """Actualiza saldo y archivo dentro del mismo bloqueo."""
        async with self.lock:
            datos = _leer_datos()
            cuenta = _cuenta(datos, user_id)
            saldo = int(cuenta.get("balance", 0))

            if apuesta <= 0:
                return False, "La apuesta debe ser mayor que 0."
            if apuesta > MAX_APUESTA:
                return False, f"La apuesta máxima es **{MAX_APUESTA:,} {MONEDA}**."
            if saldo < apuesta:
                return False, f"No tenés saldo suficiente. Tu saldo es **{saldo:,} {MONEDA}**."

            if gano:
                ganancia_neta = int(apuesta * multiplicador)
                cuenta["balance"] = saldo + ganancia_neta
                resultado = f"Ganaste **{ganancia_neta:,} {MONEDA}**."
            else:
                cuenta["balance"] = saldo - apuesta
                resultado = f"Perdiste **{apuesta:,} {MONEDA}**."

            _guardar_datos(datos)
            return True, f"{resultado}\nSaldo actual: **{cuenta['balance']:,} {MONEDA}**."

    @app_commands.command(name="dice", description="Apostá a un dado: ganás si sale 4, 5 o 6.")
    @app_commands.describe(apuesta="Cantidad de GhostCoins que querés apostar")
    async def dice(self, interaction: discord.Interaction, apuesta: app_commands.Range[int, 1, MAX_APUESTA]):
        dado = random.randint(1, 6)
        gano = dado >= 4
        ok, resultado = await self._apostar_y_resolver(interaction.user.id, apuesta, 1.0, gano)

        embed = discord.Embed(
            title="ROOTGHOST // DICE",
            description=f"🎲 Salió **{dado}**.\n\n{resultado if ok else resultado}",
            color=discord.Color.green() if ok and gano else discord.Color.red() if ok else discord.Color.orange(),
        )
        embed.set_footer(text="ROOTGHOST ECONOMY SYSTEM")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="slots", description="Probá suerte en la tragamonedas.")
    @app_commands.describe(apuesta="Cantidad de GhostCoins que querés apostar")
    async def slots(self, interaction: discord.Interaction, apuesta: app_commands.Range[int, 1, MAX_APUESTA]):
        simbolos = ["🍒", "🍋", "🍇", "⭐", "💎", "7️⃣"]
        giro = [random.choice(simbolos) for _ in range(3)]

        if giro[0] == giro[1] == giro[2]:
            multiplicador = 5.0 if giro[0] == "7️⃣" else 3.0
            gano = True
            detalle = f"¡Tres iguales! Premio **x{int(multiplicador)}**."
        elif len(set(giro)) == 2:
            multiplicador = 1.0
            gano = True
            detalle = "¡Dos símbolos iguales! Recuperás la apuesta y ganás lo mismo."
        else:
            multiplicador = 0.0
            gano = False
            detalle = "No hubo combinación ganadora."

        ok, resultado = await self._apostar_y_resolver(interaction.user.id, apuesta, multiplicador, gano)
        embed = discord.Embed(
            title="ROOTGHOST // SLOTS",
            description=f"{'　'.join(giro)}\n\n{detalle}\n{resultado}",
            color=discord.Color.green() if ok and gano else discord.Color.red() if ok else discord.Color.orange(),
        )
        embed.set_footer(text="ROOTGHOST ECONOMY SYSTEM")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="highlow", description="Apostá: ¿tu dado será más alto que el de la casa?")
    @app_commands.describe(apuesta="Cantidad de GhostCoins que querés apostar")
    async def highlow(self, interaction: discord.Interaction, apuesta: app_commands.Range[int, 1, MAX_APUESTA]):
        jugador = random.randint(1, 6)
        casa = random.randint(1, 6)
        gano = jugador > casa
        empate = jugador == casa

        # Empate: se devuelve la apuesta sin ganancia ni pérdida.
        if empate:
            async with self.lock:
                datos = _leer_datos()
                cuenta = _cuenta(datos, interaction.user.id)
                saldo = int(cuenta.get("balance", 0))
                if apuesta > MAX_APUESTA or saldo < apuesta:
                    error = f"No tenés saldo suficiente. Tu saldo es **{saldo:,} {MONEDA}**."
                    embed = discord.Embed(title="ROOTGHOST // HIGHLOW", description=error, color=discord.Color.orange())
                    await interaction.response.send_message(embed=embed)
                    return
                _guardar_datos(datos)
            resultado = f"Empate. No se modifica tu saldo (**{saldo:,} {MONEDA}**)."
            ok = True
        else:
            ok, resultado = await self._apostar_y_resolver(interaction.user.id, apuesta, 1.0, gano)

        embed = discord.Embed(
            title="ROOTGHOST // HIGHLOW",
            description=(
                f"🎲 Tu dado: **{jugador}**\n"
                f"🏠 Dado de la casa: **{casa}**\n\n{resultado}"
            ),
            color=discord.Color.green() if ok and gano else discord.Color.red() if ok and not empate else discord.Color.orange(),
        )
        embed.set_footer(text="ROOTGHOST ECONOMY SYSTEM")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="duel", description="Desafiá a otro usuario a un duelo por GhostCoins.")
    @app_commands.describe(
        usuario="Usuario al que querés desafiar",
        apuesta="Cantidad de GhostCoins que cada jugador arriesga",
    )
    async def duel(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        apuesta: app_commands.Range[int, 1, MAX_APUESTA],
    ):
        if usuario.bot:
            await interaction.response.send_message("No podés desafiar a un bot.", ephemeral=True)
            return
        if usuario.id == interaction.user.id:
            await interaction.response.send_message("No podés desafiarte a vos mismo.", ephemeral=True)
            return
        if apuesta <= 0 or apuesta > MAX_APUESTA:
            await interaction.response.send_message("La apuesta no es válida.", ephemeral=True)
            return

        async with self.lock:
            datos = _leer_datos()
            saldo_retador = int(_cuenta(datos, interaction.user.id).get("balance", 0))
            saldo_objetivo = int(_cuenta(datos, usuario.id).get("balance", 0))
        if saldo_retador < apuesta:
            await interaction.response.send_message(
                f"No tenés saldo suficiente. Tu saldo es **{saldo_retador:,} {MONEDA}**.",
                ephemeral=True,
            )
            return
        if saldo_objetivo < apuesta:
            await interaction.response.send_message(
                f"{usuario.mention} no tiene suficientes {MONEDA} para aceptar esta apuesta.",
                ephemeral=True,
            )
            return

        cog = self

        class DuelView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.finalizado = False

            @discord.ui.button(label="Aceptar duelo", style=discord.ButtonStyle.success, emoji="⚔️")
            async def aceptar(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.user.id != usuario.id:
                    await button_interaction.response.send_message("Solo la persona desafiada puede aceptar.", ephemeral=True)
                    return
                if self.finalizado:
                    await button_interaction.response.send_message("Este duelo ya terminó.", ephemeral=True)
                    return

                self.finalizado = True
                for item in self.children:
                    item.disabled = True

                ganador = random.choice([interaction.user, usuario])
                async with cog.lock:
                    datos_actuales = _leer_datos()
                    cuenta_a = _cuenta(datos_actuales, interaction.user.id)
                    cuenta_b = _cuenta(datos_actuales, usuario.id)
                    saldo_a = int(cuenta_a.get("balance", 0))
                    saldo_b = int(cuenta_b.get("balance", 0))

                    # Revalidar al aceptar; los saldos pueden haber cambiado.
                    if saldo_a < apuesta or saldo_b < apuesta:
                        _guardar_datos(datos_actuales)
                        await button_interaction.response.edit_message(
                            content="Duelo cancelado: uno de los dos ya no tiene saldo suficiente.",
                            view=self,
                            embed=None,
                        )
                        return

                    cuenta_a["balance"] = saldo_a - apuesta
                    cuenta_b["balance"] = saldo_b - apuesta
                    cuenta_ganador = _cuenta(datos_actuales, ganador.id)
                    cuenta_ganador["balance"] = int(cuenta_ganador.get("balance", 0)) + apuesta * 2
                    _guardar_datos(datos_actuales)

                await button_interaction.response.edit_message(
                    content=(
                        f"⚔️ **DUELO TERMINADO**\n"
                        f"{interaction.user.mention} vs. {usuario.mention}\n"
                        f"Ganador: {ganador.mention}\n"
                        f"Premio total: **{apuesta * 2:,} {MONEDA}**."
                    ),
                    view=self,
                    embed=None,
                )

            @discord.ui.button(label="Rechazar", style=discord.ButtonStyle.danger, emoji="✖️")
            async def rechazar(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.user.id != usuario.id:
                    await button_interaction.response.send_message("Solo la persona desafiada puede rechazar.", ephemeral=True)
                    return
                if self.finalizado:
                    await button_interaction.response.send_message("Este duelo ya terminó.", ephemeral=True)
                    return
                self.finalizado = True
                for item in self.children:
                    item.disabled = True
                await button_interaction.response.edit_message(
                    content=f"{usuario.mention} rechazó el duelo. No se modificaron los saldos.",
                    view=self,
                    embed=None,
                )

            async def on_timeout(self):
                if self.finalizado:
                    return
                self.finalizado = True
                for item in self.children:
                    item.disabled = True

        embed = discord.Embed(
            title="ROOTGHOST // DUEL",
            description=(
                f"{usuario.mention}, **{interaction.user.mention}** te desafía.\n"
                f"Apuesta por jugador: **{apuesta:,} {MONEDA}**\n"
                f"Premio total: **{apuesta * 2:,} {MONEDA}**\n\n"
                "Tenés 60 segundos para aceptar o rechazar."
            ),
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="ROOTGHOST ECONOMY SYSTEM")
        await interaction.response.send_message(embed=embed, view=DuelView(), ephemeral=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Apuestas(bot))
