import os
from pathlib import Path

import discord
from discord.ext import commands


# ==========================================
# ROOTGHOST // CONFIGURACIÓN PRINCIPAL
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
COMMANDS_DIR = BASE_DIR / "commands"


class RootGhost(commands.Bot):

    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(
            command_prefix="!",
            intents=intents
        )

    # ======================================
    # CARGA Y SINCRONIZACIÓN DE COMANDOS
    # ======================================

    async def setup_hook(self):
        COMMANDS_DIR.mkdir(parents=True, exist_ok=True)

        print("[ROOTGHOST] Iniciando carga de comandos...")

        # Cargar automáticamente las extensiones
        for file in sorted(COMMANDS_DIR.glob("*.py")):
            if file.name.startswith("_"):
                continue

            extension = f"commands.{file.stem}"

            try:
                await self.load_extension(extension)
                print(f"[ROOTGHOST] Cargado: {file.stem}")

            except Exception as error:
                print(
                    f"[ROOTGHOST] Error en "
                    f"{file.stem}: {type(error).__name__}: {error}"
                )

        # Revisar los comandos que están en el árbol local
        print("[ROOTGHOST] Revisando comandos IA...")

        comandos_locales = self.tree.get_commands()
        encontrados_locales = [
            comando.name
            for comando in comandos_locales
            if comando.name.startswith("ia")
        ]

        if encontrados_locales:
            for nombre in encontrados_locales:
                print(
                    f"[ROOTGHOST] Encontrado en el árbol: "
                    f"/{nombre}"
                )
        else:
            print(
                "[ROOTGHOST] AVISO: no se encontraron "
                "comandos IA en el árbol local."
            )

        # Sincronizar los comandos globales con Discord
        try:
            synced = await self.tree.sync()

            print(
                f"[ROOTGHOST] {len(synced)} "
                "comandos sincronizados."
            )

            encontrados_discord = [
                comando.name
                for comando in synced
                if comando.name.startswith("ia")
            ]

            if encontrados_discord:
                for nombre in encontrados_discord:
                    print(
                        f"[ROOTGHOST] Comando IA "
                        f"sincronizado: /{nombre}"
                    )
            else:
                print(
                    "[ROOTGHOST] AVISO: Discord no devolvió "
                    "comandos cuyo nombre empiece por 'ia'."
                )

        except Exception as error:
            print(
                "[ROOTGHOST] Error al sincronizar: "
                f"{type(error).__name__}: {error}"
            )

    # ======================================
    # EVENTO DE CONEXIÓN
    # ======================================

    async def on_ready(self):
        print("=" * 45)
        print(f"[ROOTGHOST] Conectado como: {self.user}")
        print(f"[ROOTGHOST] ID del bot: {self.user.id}")
        print(
            f"[ROOTGHOST] Servidores conectados: "
            f"{len(self.guilds)}"
        )
        print("=" * 45)


# ==========================================
# INICIAR ROOTGHOST
# ==========================================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "Falta DISCORD_TOKEN. Configurá el token "
        "como variable de entorno en Termux."
    )

bot = RootGhost()
bot.run(TOKEN)