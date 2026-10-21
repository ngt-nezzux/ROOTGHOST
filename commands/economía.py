
import os
import json
import random
import asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta

import discord
from discord import app_commands
from discord.ext import commands

# ROOTGHOST // ECONOMY SYSTEM
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "economia.json"

# Reemplaza estos números por tus IDs reales de Discord.
# Para copiar un ID: activa el Modo desarrollador de Discord
# y usa "Copiar ID de usuario".
ADMIN_IDS = {
    938604108594704384,
    # 987654321098765432,
}

MONEDA = "GhostCoins"
RECOMPENSA_DIARIA = 500
RECOMPENSA_TRABAJO_MIN = 100
RECOMPENSA_TRABAJO_MAX = 300
MAX_APUESTA = 10000000000000

DATA_DIR.mkdir(parents=True, exist_ok=True)


class Economia(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.lock = asyncio.Lock()
        if not DATA_FILE.exists():
            self._save({"users": {}})

    def _load(self):
        try:
            with DATA_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return {"users": {}}
            if not isinstance(data.get("users"), dict):
                data["users"] = {}
            return data
        except (json.JSONDecodeError, OSError):
            return {"users": {}}

    def _save(self, data):
        temp = DATA_FILE.with_suffix(".tmp")
        with temp.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        temp.replace(DATA_FILE)

    def _account(self, data, user_id):
        key = str(user_id)
        if key not in data["users"]:
            data["users"][key] = {
                "balance": 0,
                "bank": 0,
                "daily": 0,
                "work": 0,
            }
        return data["users"][key]

    def _is_admin(self, user):
        return user.id in ADMIN_IDS

    async def _deny(self, interaction):
        await interaction.response.send_message(
            "⛔ Acceso denegado. Tu ID no está autorizado.",
            ephemeral=True,
        )

    async def _admin_check(self, interaction):
        if not self._is_admin(interaction.user):
            await self._deny(interaction)
            return False
        return True

    def _embed(self, title, description, color=0x5865F2):
        embed = discord.Embed(
            title=f"ROOTGHOST // {title}",
            description=description,
            color=color,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(text="ROOTGHOST ECONOMY SYSTEM")
        return embed

    @app_commands.command(name="balance", description="Consulta tu saldo o el de otro usuario.")
    @app_commands.describe(usuario="Usuario que quieres consultar")
    async def balance(
        self,
        interaction: discord.Interaction,
        usuario: discord.User = None,
    ):
        target = usuario or interaction.user
        async with self.lock:
            data = self._load()
            account = self._account(data, target.id)
            self._save(data)

        embed = self._embed(
            "CUENTA BANCARIA",
            f"**Usuario:** {target.mention}\n"
            f"**Billetera:** `{account['balance']:,} {MONEDA}`\n"
            f"**Banco:** `{account['bank']:,} {MONEDA}`\n"
            f"**Patrimonio:** `{account['balance'] + account['bank']:,} {MONEDA}`"
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Reclama tu recompensa diaria.")
    async def daily(self, interaction: discord.Interaction):
        now = int(datetime.now(timezone.utc).timestamp())
        async with self.lock:
            data = self._load()
            account = self._account(data, interaction.user.id)
            remaining = 86400 - (now - account["daily"])

            if remaining > 0:
                hours, rem = divmod(remaining, 3600)
                minutes = rem // 60
                await interaction.response.send_message(
                    f"⏳ Ya reclamaste tu recompensa. Vuelve en "
                    f"**{hours} h {minutes} min**.",
                    ephemeral=True,
                )
                return

            account["balance"] += RECOMPENSA_DIARIA
            account["daily"] = now
            self._save(data)

        await interaction.response.send_message(
            embed=self._embed(
                "RECOMPENSA DIARIA",
                f"Recibiste **{RECOMPENSA_DIARIA:,} {MONEDA}**.\n"
                f"Saldo actual: **{account['balance']:,} {MONEDA}**",
                0x2ECC71,
            )
        )

    @app_commands.command(name="work", description="Trabaja para ganar monedas.")
    async def work(self, interaction: discord.Interaction):
        now = int(datetime.now(timezone.utc).timestamp())
        async with self.lock:
            data = self._load()
            account = self._account(data, interaction.user.id)
            remaining = 3600 - (now - account["work"])

            if remaining > 0:
                await interaction.response.send_message(
                    f"⏳ Debes esperar **{remaining // 60} min "
                    f"{remaining % 60} s** para volver a trabajar.",
                    ephemeral=True,
                )
                return

            reward = random.randint(
                RECOMPENSA_TRABAJO_MIN, RECOMPENSA_TRABAJO_MAX
            )
            account["balance"] += reward
            account["work"] = now
            self._save(data)

        await interaction.response.send_message(
            embed=self._embed(
                "JORNADA COMPLETADA",
                f"Ganaste **{reward:,} {MONEDA}**.\n"
                f"Saldo: **{account['balance']:,} {MONEDA}**",
                0x2ECC71,
            )
        )

    @app_commands.command(name="pay", description="Transfiere monedas a otro usuario.")
    @app_commands.describe(usuario="Destinatario", cantidad="Cantidad a transferir")
    async def pay(
        self,
        interaction: discord.Interaction,
        usuario: discord.User,
        cantidad: app_commands.Range[int, 1, 1000000000],
    ):
        if usuario.bot or usuario.id == interaction.user.id:
            await interaction.response.send_message(
                "❌ No puedes transferir monedas a bots ni a ti mismo.",
                ephemeral=True,
            )
            return

        async with self.lock:
            data = self._load()
            sender = self._account(data, interaction.user.id)
            receiver = self._account(data, usuario.id)

            if sender["balance"] < cantidad:
                await interaction.response.send_message(
                    "❌ No tienes suficiente saldo en tu billetera.",
                    ephemeral=True,
                )
                return

            sender["balance"] -= cantidad
            receiver["balance"] += cantidad
            self._save(data)

        await interaction.response.send_message(
            embed=self._embed(
                "TRANSFERENCIA COMPLETADA",
                f"**Emisor:** {interaction.user.mention}\n"
                f"**Receptor:** {usuario.mention}\n"
                f"**Cantidad:** `{cantidad:,} {MONEDA}`",
                0x2ECC71,
            )
        )

    @app_commands.command(name="leaderboard", description="Top 10 usuarios más ricos.")
    async def leaderboard(self, interaction: discord.Interaction):
        async with self.lock:
            data = self._load()
            users = sorted(
                data["users"].items(),
                key=lambda item: item[1].get("balance", 0)
                + item[1].get("bank", 0),
                reverse=True,
            )[:10]

        lines = []
        for position, (user_id, account) in enumerate(users, start=1):
            user = self.bot.get_user(int(user_id))
            name = user.display_name if user else f"Usuario {user_id}"
            total = account.get("balance", 0) + account.get("bank", 0)
            lines.append(
                f"**{position}.** {discord.utils.escape_markdown(name)} — "
                f"`{total:,} {MONEDA}`"
            )

        await interaction.response.send_message(
            embed=self._embed(
                "RANKING DE RIQUEZA",
                "\n".join(lines) if lines else "Todavía no hay cuentas registradas.",
            )
        )

    @app_commands.command(name="coinflip", description="Apuesta monedas a cara o cruz.")
    @app_commands.describe(
        apuesta="Cantidad de monedas",
        eleccion="Elige cara o cruz",
    )
    @app_commands.choices(eleccion=[
        app_commands.Choice(name="Cara", value="cara"),
        app_commands.Choice(name="Cruz", value="cruz"),
    ])
    async def coinflip(
        self,
        interaction: discord.Interaction,
        apuesta: app_commands.Range[int, 1, MAX_APUESTA],
        eleccion: app_commands.Choice[str],
    ):
        async with self.lock:
            data = self._load()
            account = self._account(data, interaction.user.id)

            if account["balance"] < apuesta:
                await interaction.response.send_message(
                    "❌ No tienes suficientes monedas para esa apuesta.",
                    ephemeral=True,
                )
                return

            resultado = random.choice(["cara", "cruz"])
            account["balance"] -= apuesta
            gano = resultado == eleccion.value
            if gano:
                account["balance"] += apuesta * 2
            self._save(data)
            saldo = account["balance"]

        await interaction.response.send_message(
            embed=self._embed(
                "COINFLIP",
                f"**Tu elección:** {eleccion.name}\n"
                f"**Resultado:** {resultado.title()}\n"
                f"**Resultado de la partida:** "
                f"{'Ganaste' if gano else 'Perdiste'}\n"
                f"**Saldo actual:** `{saldo:,} {MONEDA}`",
                0x2ECC71 if gano else 0xE74C3C,
            )
        )

    @app_commands.command(name="eco-add", description="[ADMIN] Agrega monedas a un usuario.")
    @app_commands.describe(usuario="Destinatario", cantidad="Monedas que recibirá")
    async def eco_add(
        self,
        interaction: discord.Interaction,
        usuario: discord.User,
        cantidad: app_commands.Range[int, 1, 1000000000],
    ):
        if not await self._admin_check(interaction):
            return
        async with self.lock:
            data = self._load()
            account = self._account(data, usuario.id)
            account["balance"] += cantidad
            self._save(data)
            saldo = account["balance"]

        await interaction.response.send_message(
            f"✅ Se agregaron **{cantidad:,} {MONEDA}** a {usuario.mention}. "
            f"Saldo: `{saldo:,}`."
        )

    @app_commands.command(name="eco-remove", description="[ADMIN] Quita monedas de un usuario.")
    @app_commands.describe(usuario="Usuario", cantidad="Monedas que quitará")
    async def eco_remove(
        self,
        interaction: discord.Interaction,
        usuario: discord.User,
        cantidad: app_commands.Range[int, 1, 1000000000],
    ):
        if not await self._admin_check(interaction):
            return
        async with self.lock:
            data = self._load()
            account = self._account(data, usuario.id)
            removed = min(cantidad, account["balance"])
            account["balance"] -= removed
            self._save(data)
            saldo = account["balance"]

        await interaction.response.send_message(
            f"✅ Se quitaron **{removed:,} {MONEDA}** a {usuario.mention}. "
            f"Saldo: `{saldo:,}`."
        )

    @app_commands.command(name="eco-set", description="[ADMIN] Establece el saldo de un usuario.")
    @app_commands.describe(usuario="Usuario", cantidad="Nuevo saldo")
    async def eco_set(
        self,
        interaction: discord.Interaction,
        usuario: discord.User,
        cantidad: app_commands.Range[int, 0, 1000000000],
    ):
        if not await self._admin_check(interaction):
            return
        async with self.lock:
            data = self._load()
            account = self._account(data, usuario.id)
            account["balance"] = cantidad
            self._save(data)

        await interaction.response.send_message(
            f"✅ Saldo de {usuario.mention} establecido en **{cantidad:,} {MONEDA}**."
        )

    @app_commands.command(name="eco-reset", description="[ADMIN] Reinicia la cuenta de un usuario.")
    @app_commands.describe(usuario="Cuenta que quieres reiniciar")
    async def eco_reset(
        self,
        interaction: discord.Interaction,
        usuario: discord.User,
    ):
        if not await self._admin_check(interaction):
            return
        async with self.lock:
            data = self._load()
            data["users"][str(usuario.id)] = {
                "balance": 0, "bank": 0, "daily": 0, "work": 0
            }
            self._save(data)

        await interaction.response.send_message(
            f"♻️ Cuenta de {usuario.mention} reiniciada."
        )

    @app_commands.command(name="eco-giveall", description="[ADMIN] Da monedas a todos los miembros.")
    @app_commands.describe(cantidad="Monedas que recibirá cada miembro")
    async def eco_giveall(
        self,
        interaction: discord.Interaction,
        cantidad: app_commands.Range[int, 1, 1000000000],
    ):
        if not await self._admin_check(interaction):
            return
        if interaction.guild is None:
            await interaction.response.send_message(
                "Este comando solo puede usarse dentro de un servidor.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        members = [m for m in interaction.guild.members if not m.bot]

        async with self.lock:
            data = self._load()
            for member in members:
                account = self._account(data, member.id)
                account["balance"] += cantidad
            self._save(data)

        await interaction.followup.send(
            f"✅ Se entregaron **{cantidad:,} {MONEDA}** a "
            f"**{len(members)} miembros**.",
            ephemeral=True,
        )

    
    @app_commands.command(
        name="eco-richest",
        description="[ADMIN] Consulta las cuentas más ricas."
    )
    async def eco_richest(self, interaction: discord.Interaction):
        if not await self._admin_check(interaction):
            return

        async with self.lock:
            data = self._load()
            users = sorted(
                data["users"].items(),
                key=lambda item: (
                    item[1].get("balance", 0)
                    + item[1].get("bank", 0)
                ),
                reverse=True,
            )[:10]

        lines = []
        for position, (user_id, account) in enumerate(users, start=1):
            user = self.bot.get_user(int(user_id))
            name = (
                discord.utils.escape_markdown(user.display_name)
                if user
                else f"Usuario {user_id}"
            )
            total = account.get("balance", 0) + account.get("bank", 0)
            lines.append(
                f"**{position}.** {name} — `{total:,} {MONEDA}`"
            )

        await interaction.response.send_message(
            embed=self._embed(
                "RANKING PRIVADO DE ECONOMÍA",
                "\n".join(lines) if lines else "No hay cuentas registradas."
            ),
            ephemeral=True,
        )


    @app_commands.command(name="economy-help", description="Lista los comandos de economía.")
    async def economy_help(self, interaction: discord.Interaction):
        embed = self._embed(
            "CENTRO DE ECONOMÍA",
            "**Miembros**\n"
            "`/balance` `/daily` `/work` `/pay` `/leaderboard` `/coinflip`\n\n"
            "**Administración autorizada por ID**\n"
            "`/eco-add` `/eco-remove` `/eco-set` `/eco-reset`\n"
            "`/eco-giveall` `/eco-richest`\n\n"
            f"Moneda: **{MONEDA}**"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Economia(bot))
