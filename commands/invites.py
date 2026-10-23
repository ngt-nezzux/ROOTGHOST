import json
import asyncio
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "invites.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class InviteSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()
        self.cache = {}
        self.data = self.load_data()

    def load_data(self):
        try:
            with DATA_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and isinstance(data.get("guilds"), dict):
                return data
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass
        return {"guilds": {}}

    def save_data(self):
        temp = DATA_FILE.with_suffix(".tmp")
        with temp.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        temp.replace(DATA_FILE)

    def guild_data(self, guild_id):
        return self.data.setdefault("guilds", {}).setdefault(
            str(guild_id), {"invites": {}, "members": {}}
        )

    async def fetch_invites(self, guild):
        try:
            return await guild.invites()
        except (discord.Forbidden, discord.HTTPException):
            return None

    async def refresh_cache(self, guild):
        invites = await self.fetch_invites(guild)
        if invites is None:
            return
        self.cache[guild.id] = {
            invite.code: {
                "uses": invite.uses or 0,
                "inviter_id": invite.inviter.id if invite.inviter else None,
            }
            for invite in invites
        }

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            await self.refresh_cache(guild)

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        await self.refresh_cache(invite.guild)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        await self.refresh_cache(invite.guild)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        old = self.cache.get(member.guild.id, {})
        invites = await self.fetch_invites(member.guild)
        if invites is None:
            return

        current = {}
        used = []

        for invite in invites:
            uses = invite.uses or 0
            current[invite.code] = {
                "uses": uses,
                "inviter_id": invite.inviter.id if invite.inviter else None,
            }
            previous = old.get(invite.code, {})
            if uses > previous.get("uses", 0):
                used.append(invite)

        self.cache[member.guild.id] = current

        if len(used) != 1 or used[0].inviter is None:
            return

        inviter_id = str(used[0].inviter.id)
        member_id = str(member.id)

        async with self.lock:
            data = self.guild_data(member.guild.id)
            record = data["invites"].setdefault(
                inviter_id, {"joins": 0, "leaves": 0, "members": []}
            )

            membership = data["members"].get(member_id)
            if membership is None:
                record["joins"] += 1
                record["members"].append(member_id)
            elif membership.get("left"):
                record["joins"] += 1
                record["members"].append(member_id)

            data["members"][member_id] = {
                "inviter_id": inviter_id,
                "left": False,
                "invite_code": used[0].code,
            }
            self.save_data()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        async with self.lock:
            data = self.guild_data(member.guild.id)
            membership = data["members"].get(str(member.id))
            if not membership or membership.get("left"):
                return

            membership["left"] = True
            record = data["invites"].get(str(membership.get("inviter_id")))
            if record:
                record["leaves"] = record.get("leaves", 0) + 1
            self.save_data()

    def stats(self, guild_id, user_id):
        record = self.guild_data(guild_id)["invites"].get(str(user_id), {})
        joins = int(record.get("joins", 0))
        leaves = int(record.get("leaves", 0))
        return joins, leaves, max(0, joins - leaves)

    def embed(self, title, description):
        result = discord.Embed(
            title=f"ROOTGHOST // {title}",
            description=description,
            color=discord.Color.from_rgb(35, 220, 120),
        )
        result.set_footer(text="ROOTGHOST SECURITY SYSTEM")
        return result

    @app_commands.command(
        name="invites",
        description="Consulta tus invitaciones registradas."
    )
    async def invites(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message(
                "Este comando solo funciona dentro de un servidor.",
                ephemeral=True,
            )
            return

        joins, leaves, valid = self.stats(
            interaction.guild.id, interaction.user.id
        )
        await interaction.response.send_message(embed=self.embed(
            "INVITACIONES",
            f"**Usuario:** {interaction.user.mention}\n"
            f"**Entradas registradas:** {joins}\n"
            f"**Miembros que salieron:** {leaves}\n"
            f"**Invitaciones válidas estimadas:** {valid}",
        ))

    @app_commands.command(
        name="invite-check",
        description="Consulta las invitaciones registradas de un miembro."
    )
    @app_commands.describe(miembro="Miembro que querés consultar")
    async def invite_check(
        self,
        interaction: discord.Interaction,
        miembro: discord.Member,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "Este comando solo funciona dentro de un servidor.",
                ephemeral=True,
            )
            return

        joins, leaves, valid = self.stats(
            interaction.guild.id, miembro.id
        )
        await interaction.response.send_message(embed=self.embed(
            "REVISIÓN DE INVITACIONES",
            f"**Miembro:** {miembro.mention}\n"
            f"**Entradas registradas:** {joins}\n"
            f"**Miembros que salieron:** {leaves}\n"
            f"**Invitaciones válidas estimadas:** {valid}",
        ))

    @app_commands.command(
        name="invite-leaderboard",
        description="Muestra el ranking de invitaciones válidas."
    )
    async def invite_leaderboard(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message(
                "Este comando solo funciona dentro de un servidor.",
                ephemeral=True,
            )
            return

        records = self.guild_data(interaction.guild.id)["invites"]
        ranking = []

        for user_id in records:
            joins, leaves, valid = self.stats(
                interaction.guild.id, user_id
            )
            if valid > 0:
                ranking.append((int(user_id), joins, leaves, valid))

        ranking.sort(key=lambda item: item[3], reverse=True)
        lines = [
            f"**{position}.** <@{user_id}> — **{valid}** válidas "
            f"({joins} entradas, {leaves} salidas)"
            for position, (user_id, joins, leaves, valid)
            in enumerate(ranking[:10], 1)
        ]

        description = "\n".join(lines) or (
            "Todavía no hay invitaciones registradas."
        )
        await interaction.response.send_message(
            embed=self.embed("INVITE LEADERBOARD", description)
        )


async def setup(bot):
    await bot.add_cog(InviteSystem(bot))
