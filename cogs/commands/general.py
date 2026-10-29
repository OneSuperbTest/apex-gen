import discord
from discord import ui
from discord.ext import commands
import time
from datetime import datetime
from database import db
from utils.emojis import emoji as Emoji

class GeneralCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_uptime(self) -> str:
        """Calculate human-readable uptime from bot start time."""
        uptime_delta = datetime.now() - self.bot.start_time
        d = uptime_delta.days
        h, rem = divmod(uptime_delta.seconds, 3600)
        m, s = divmod(rem, 60)
        parts = []
        if d: parts.append(f"{d}d")
        if h: parts.append(f"{h}h")
        if m: parts.append(f"{m}m")
        parts.append(f"{s}s")
        return " ".join(parts)

    def build_stats_view(self) -> ui.LayoutView:
        """Build the full /stats diagnostic view."""
        import psutil
        import platform
        import os
        process = psutil.Process(os.getpid())
        mem_pct = process.memory_percent()
        cpu_pct = process.cpu_percent(interval=None)

        guilds = len(self.bot.guilds)
        users = sum(g.member_count or 0 for g in self.bot.guilds)
        cmds = len([c for c in self.bot.walk_commands()])
        latency = round(self.bot.latency * 1000)
        uptime = self.get_uptime()
        py_ver = platform.python_version()
        dpy_ver = discord.__version__
        os_name = f"{platform.system()} {platform.release()}"

        host = os.environ.get("HOST_NAME", "APZX Dedicated Node")

        view = ui.LayoutView()
        container = ui.Container(accent_color=None)

        container.add_item(ui.TextDisplay(f"# {Emoji.stats} System Statistics"))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        container.add_item(ui.TextDisplay(
            "## Engine\n"
            f"-# Core Logic\n**APZX GEN System**\n"
            f"-# Uptime\n`{uptime}`\n"
            f"-# Commands\n**{cmds}** Modules\n"
            f"-# Connection Latency\n`{latency}ms WebSocket`"
        ))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        container.add_item(ui.TextDisplay(
            "## Network\n"
            f"-# Servers\n**{guilds:,}** Guilds\n"
            f"-# Authorized Connections\n**{users:,}** Users"
        ))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        container.add_item(ui.TextDisplay(
            "## System Status\n"
            f"-# Runtime\n`Python {py_ver}` | `discord.py {dpy_ver}`\n"
            f"-# Core Allocation\n`RAM Usage: {mem_pct:.2f}%` | `CPU Usage: {cpu_pct:.2f}%`\n"
            f"-# Server Host\n`{host}` | `{os_name}`"
        ))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        refresh_btn = ui.Button(
            label="Refresh Stats",
            style=discord.ButtonStyle.secondary,
            custom_id="stats_refresh"
        )
        action_row = ui.ActionRow(refresh_btn)
        container.add_item(action_row)

        container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))

        view.add_item(container)
        return view

    @commands.hybrid_command(name="ping", description="Check the bot's latency protocol")
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        view = ui.LayoutView()
        container = ui.Container(accent_color=None)
        container.add_item(ui.TextDisplay(f"# {Emoji.stats} Connection Status"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"**Gateway Latency:** `{latency}ms`\n**Shard Sector:** `{ctx.guild.shard_id if ctx.guild else 0}`"))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
        view.add_item(container)
        await ctx.send(view=view)

    @commands.hybrid_command(name="stock", description="Check live account availability across all generator sectors")
    async def stock(self, ctx: commands.Context):
        counts = await db.get_all_stock_counts()

        view = ui.LayoutView()
        container = ui.Container(accent_color=None)

        container.add_item(ui.TextDisplay(f"# {Emoji.stats} Live Stock Inventory"))
        container.add_item(ui.Separator())

        free_stock = "\n".join([f"> **{name.title()}**: `{count}`" for name, count in counts['free'].items()]) if counts['free'] else "> *No free services initialized.*"
        container.add_item(ui.TextDisplay(f"### {Emoji.free} Free Gen Stock\n{free_stock}"))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        booster_stock = "\n".join([f"> **{name.title()}**: `{count}`" for name, count in counts['booster'].items()]) if counts['booster'] else "> *No booster services initialized.*"
        container.add_item(ui.TextDisplay(f"### {Emoji.booster} Booster Gen Stock\n{booster_stock}"))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        premium_stock = "\n".join([f"> **{name.title()}**: `{count}`" for name, count in counts['premium'].items()]) if counts['premium'] else "> *No premium services initialized.*"
        container.add_item(ui.TextDisplay(f"### {Emoji.premium} Premium Gen Stock\n{premium_stock}"))

        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))

        view.add_item(container)
        await ctx.send(view=view)

    @commands.hybrid_command(name="stats", description="View comprehensive system diagnostics and bot statistics")
    async def stats(self, ctx: commands.Context):
        view = self.build_stats_view()
        await ctx.send(view=view, ephemeral=False)

    @commands.hybrid_command(name="uptime", description="Show how long the bot has been online")
    async def uptime(self, ctx):
        uptime_str = self.get_uptime()
        view = ui.LayoutView()
        container = ui.Container(accent_color=None)
        container.add_item(ui.TextDisplay(f"# {Emoji.online} Bot Uptime"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(
            f"**Uptime:** `{uptime_str}`\n"
            f"**Started:** `{self.bot.start_time.strftime('%Y-%m-%d %H:%M:%S')}`\n"
            f"**Status:** `Operational` {Emoji.success}"
        ))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
        view.add_item(container)
        await ctx.send(view=view)

    @commands.hybrid_command(name="vouch", description="Check your vouch status — are you pending, vouched, or exempt?")
    async def vouch(self, ctx):
        from database.db import DB_PATH
        import aiosqlite

        async with aiosqlite.connect(DB_PATH) as conn:
            cursor = await conn.execute(
                "SELECT vouched, last_service, last_tier, generated_at FROM vouch_tracking WHERE user_id = ?",
                (ctx.author.id,)
            )
            row = await cursor.fetchone()

        view = ui.LayoutView()
        container = ui.Container(accent_color=None)
        container.add_item(ui.TextDisplay(f"# {Emoji.lock} Vouch Status"))
        container.add_item(ui.Separator())

        vouch_channel_id = await db.get_setting("vouch_channel_id")
        vouch_mention = f"<#{vouch_channel_id}>" if vouch_channel_id else "`#vouch-channel`"

        if not row:
            container.add_item(ui.TextDisplay(
                f"**Status:** `NO RECORD` {Emoji.info}\n"
                f"You haven't generated anything yet or all records have expired.\n\n"
                f"Generate an account and vouch in {vouch_mention} with `legit got <service>`."
            ))
        else:
            vouched, service, tier, generated_at = row
            if vouched == 1:
                container.add_item(ui.TextDisplay(
                    f"**Status:** `VOUCHED` {Emoji.success}\n"
                    f"**Service:** {service.title()} ({tier})\n"
                    f"You have successfully vouched. No action needed."
                ))
            else:
                try:
                    gen_time = datetime.fromisoformat(generated_at) if isinstance(generated_at, str) else generated_at
                    elapsed = int((datetime.now() - gen_time).total_seconds())
                except Exception:
                    elapsed = 300
                remaining = max(0, 300 - elapsed)
                m, s = divmod(remaining, 60)
                container.add_item(ui.TextDisplay(
                    f"**Status:** `PENDING` {Emoji.warning}\n"
                    f"**Service:** {service.title()} ({tier})\n"
                    f"**Time Remaining:** `{m}m {s}s`\n\n"
                    f"Vouch now in {vouch_mention} with `legit got {service}`!"
                ))

        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
        view.add_item(container)
        await ctx.send(view=view)

    @commands.hybrid_command(name="history", description="View your recent generation history")
    async def history(self, ctx):
        from database.db import get_user_history
        rows = await get_user_history(ctx.author.id, limit=10)

        view = ui.LayoutView()
        container = ui.Container(accent_color=None)
        container.add_item(ui.TextDisplay(f"# {Emoji.arrow} Generation History"))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        if not rows:
            container.add_item(ui.TextDisplay("**Status:** `No history found`\nYou haven't generated anything yet."))
        else:
            lines = []
            for service, tier, gen_at in rows:
                lines.append(f"- {Emoji.dot} **{service.title()}** ({tier}) — {gen_at}")
            container.add_item(ui.TextDisplay("\n".join(lines)))
            container.add_item(ui.TextDisplay(f"\nShowing last **{len(rows)}** of your generations."))

        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
        view.add_item(container)
        await ctx.send(view=view, ephemeral=True)

    @commands.hybrid_command(name="topgen", description="View top generators leaderboard")
    async def topgen(self, ctx):
        from database.db import get_top_generators
        rows = await get_top_generators(limit=10)

        view = ui.LayoutView()
        container = ui.Container(accent_color=None)
        container.add_item(ui.TextDisplay(f"# {Emoji.gold} Top Generators"))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        if not rows:
            container.add_item(ui.TextDisplay("**No generation data yet.** Be the first!"))
        else:
            medals = {1: Emoji.gold, 2: Emoji.crown, 3: Emoji.shield}
            lines = []
            for rank, (user_id, total) in enumerate(rows, 1):
                member = ctx.guild.get_member(int(user_id)) if ctx.guild else None
                name = member.display_name if member else f"User {user_id}"
                medal = medals.get(rank, Emoji.dot)
                lines.append(f"{medal} **#{rank}** — {name} ({total} gen{'s' if total != 1 else ''})")
            container.add_item(ui.TextDisplay("\n".join(lines)))

        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
        view.add_item(container)
        await ctx.send(view=view)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Handle button interactions."""
        if interaction.type == discord.InteractionType.component and interaction.data.get("custom_id") == "stats_refresh":
            view = self.build_stats_view()
            await interaction.response.edit_message(view=view)

    @commands.hybrid_command(name="cstatus", description="Opt-in/out of automated status/invite monitoring for the Free Gen role")
    async def cstatus(self, ctx):
        req_cog = self.bot.get_cog("RequirementEvents")
        if not req_cog:
            return await ctx.send(f"{Emoji.error} Requirement System Offline.", ephemeral=True)

        is_mon = await db.is_monitored(ctx.author.id)

        if is_mon:
            await db.remove_monitor(ctx.author.id)

            fgen_role_id = await db.get_setting("fgen_role_id")
            if fgen_role_id:
                try:
                    role = ctx.guild.get_role(int(fgen_role_id))
                    if role and role in ctx.author.roles:
                        await ctx.author.remove_roles(role, reason="Manual Monitor Deactivation")
                except discord.Forbidden:
                    pass
                except Exception:
                    pass

            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.shield} Monitor Status"))
            container.add_item(ui.TextDisplay(f"**Status:** `DEACTIVATED` {Emoji.error}\nYou have opted out of automated monitoring and your access has been revoked."))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
            view.add_item(container)
            return await ctx.send(view=view, ephemeral=True)

        status_req = await db.get_setting("status_req")
        invite_req_str = await db.get_setting("invite_req")
        invite_req = int(invite_req_str) if invite_req_str and invite_req_str.isdigit() else 0

        invite_counts = {}
        if ctx.guild.me.guild_permissions.manage_guild:
            try:
                invites = await ctx.guild.invites()
                for inv in invites:
                    if inv.inviter:
                        invite_counts[inv.inviter.id] = invite_counts.get(inv.inviter.id, 0) + inv.uses
            except Exception:
                pass

        has_status, has_invites, status_text, user_invites = await req_cog.check_eligibility(
            ctx.author, status_req, invite_req, invite_counts
        )

        view = ui.LayoutView()
        container = ui.Container(accent_color=None)
        container.add_item(ui.TextDisplay(f"## {Emoji.shield} Monitor Setup"))

        if has_status and has_invites:
            await db.add_monitor(ctx.author.id)

            fgen_role_id = await db.get_setting("fgen_role_id")
            if fgen_role_id:
                try:
                    role = ctx.guild.get_role(int(fgen_role_id))
                    if role:
                        await ctx.author.add_roles(role, reason="Initial Setup Met")
                except discord.Forbidden:
                    view_err = ui.LayoutView()
                    container_err = ui.Container(accent_color=None)
                    container_err.add_item(ui.TextDisplay(f"## {Emoji.warning} Setup Error"))
                    container_err.add_item(ui.TextDisplay(f"I cannot assign the **Free Gen** role directly. Please ensure my bot role is higher than the role I'm trying to assign."))
                    view_err.add_item(container_err)
                    return await ctx.send(view=view_err, ephemeral=True)
                except Exception:
                    pass

            container.add_item(ui.TextDisplay(
                f"**Status:** `ACTIVATED` {Emoji.success}\n"
                f"Setup successful. You have been granted the **Free Gen** role.\n"
                f"Note: If you remove your status or invites, your access will be revoked within 60 seconds."
            ))
        else:
            reasons = []
            if not has_status:
                reasons.append(f"- Missing `{status_req}` in status (Current: `{status_text}`)")
            if not has_invites:
                reasons.append(f"- Need `{invite_req}` invites (Currently have `{user_invites}`)")

            reasons_text = "\n".join(reasons)
            container.add_item(ui.TextDisplay(
                f"**Status:** `FAILED` {Emoji.error}\n"
                f"Requirements not met:\n{reasons_text}\n\n"
                f"Please fix the above and try again."
            ))

        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
        view.add_item(container)
        await ctx.send(view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(GeneralCommands(bot))

"""
Project Name: APZX GEN Bot
Creator: 4iuc
GitHub: https://github.com/apzxcore
"""
