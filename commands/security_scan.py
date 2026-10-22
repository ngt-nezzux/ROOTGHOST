
import discord
from discord import app_commands
from discord.ext import commands


class SecurityScan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="security-scan",
        description="Analiza riesgos de seguridad del servidor."
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def security_scan(self, interaction: discord.Interaction):
        guild = interaction.guild
        await interaction.response.defer(ephemeral=True, thinking=True)

        riesgos = []

        # 1. Roles con Administrador
        roles_admin = [
            role for role in guild.roles
            if role.permissions.administrator and not role.is_default()
        ]

        if roles_admin:
            nombres = ", ".join(
                discord.utils.escape_markdown(role.name)
                for role in roles_admin[:8]
            )
            riesgos.append((
                "🟠 Roles administradores",
                f"Se detectaron {len(roles_admin)} roles con Administrador: "
                f"{nombres}. Revisá que sean de confianza."
            ))
        else:
            riesgos.append((
                "🟢 Roles administradores",
                "No se detectaron roles adicionales con Administrador."
            ))

        # 2. Permisos de @everyone
        everyone = guild.default_role.permissions
        peligros = []

        if everyone.administrator:
            peligros.append("Administrador")
        if everyone.manage_guild:
            peligros.append("Gestionar servidor")
        if everyone.manage_roles:
            peligros.append("Gestionar roles")
        if everyone.manage_channels:
            peligros.append("Gestionar canales")
        if everyone.ban_members:
            peligros.append("Banear miembros")
        if everyone.kick_members:
            peligros.append("Expulsar miembros")
        if everyone.mention_everyone:
            peligros.append("Mencionar @everyone")

        if peligros:
            riesgos.append((
                "🔴 Permisos de @everyone",
                "Permisos sensibles: " + ", ".join(peligros)
                + ". Revisá la configuración del rol."
            ))
        else:
            riesgos.append((
                "🟢 Permisos de @everyone",
                "No se detectaron los permisos sensibles revisados."
            ))

        # 3. Canales donde @everyone puede escribir
        canales_publicos = [
            canal for canal in guild.text_channels
            if canal.permissions_for(guild.default_role).view_channel
            and canal.permissions_for(guild.default_role).send_messages
        ]

        if canales_publicos:
            riesgos.append((
                "🟠 Canales públicos",
                f"{len(canales_publicos)} canales permiten escribir a @everyone. "
                "Confirmá que sea intencional."
            ))
        else:
            riesgos.append((
                "🟢 Canales públicos",
                "No se detectaron canales de texto donde @everyone pueda escribir."
            ))

        # 4. Permiso para crear invitaciones
        if everyone.create_instant_invite:
            riesgos.append((
                "🟠 Invitaciones",
                "@everyone puede crear invitaciones. Desactivá el permiso "
                "si no es necesario."
            ))
        else:
            riesgos.append((
                "🟢 Invitaciones",
                "@everyone no puede crear invitaciones."
            ))

        # 5. Nivel de verificación
        nivel = str(guild.verification_level).replace("_", " ").title()

        if guild.verification_level in (
            discord.VerificationLevel.none,
            discord.VerificationLevel.low
        ):
            riesgos.append((
                "🟠 Verificación",
                f"Nivel actual: {nivel}. Considerá aumentarlo si sufrís spam o raids."
            ))
        else:
            riesgos.append((
                "🟢 Verificación",
                f"Nivel actual: {nivel}."
            ))

        embed = discord.Embed(
            title="ROOTGHOST // SECURITY SCAN",
            description=(
                f"**Servidor:** {discord.utils.escape_markdown(guild.name)}\n"
                f"**Controles revisados:** {len(riesgos)}\n"
                "**Este análisis no modifica la configuración.**"
            ),
            color=discord.Color.green()
        )

        for titulo, detalle in riesgos:
            embed.add_field(
                name=titulo,
                value=detalle,
                inline=False
            )

        embed.set_footer(
            text="ROOTGHOST SECURITY SYSTEM • Análisis de solo lectura"
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @security_scan.error
    async def security_scan_error(self, interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            mensaje = "⛔ Necesitás el permiso Administrador para usar este comando."
        else:
            mensaje = "⚠️ No se pudo completar el análisis. Revisá los logs del bot."

        if interaction.response.is_done():
            await interaction.followup.send(mensaje, ephemeral=True)
        else:
            await interaction.response.send_message(mensaje, ephemeral=True)


async def setup(bot):
    await bot.add_cog(SecurityScan(bot))
