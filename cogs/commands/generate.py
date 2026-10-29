import discord
from discord import ui
from discord.ext import commands
from database import db
import config
from utils.emojis import emoji as Emoji
from typing import Optional

class GenerateCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._user_commands: dict[int, list[float]] = {}  # anti-spam tracker

    async def _handle_gen(self, ctx: commands.Context, service: str, tier: str, cooldown: int, role_id: int, channel_id: int):
        # Anti-spam: max 3 gen attempts per 10 seconds per user
        now = time.time()
        user_cmds = self._user_commands.get(ctx.author.id, [])
        user_cmds = [t for t in user_cmds if now - t < 10]  # keep last 10s
        user_cmds.append(now)
        self._user_commands[ctx.author.id] = user_cmds
        if len(user_cmds) > 3:
            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.error} Rate Limited"))
            container.add_item(ui.TextDisplay("You're generating too fast. Please wait a moment before trying again."))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
            view.add_item(container)
            await ctx.send(view=view, ephemeral=True)
            return

        try:
            await ctx.defer(ephemeral=True)
        except Exception as e:
            print(f"Defer Failed: {e}")
            return

        if tier.lower() == "premium":
            premium_enabled = await db.get_setting("premium_enabled", "1")
            if premium_enabled != "1":
                view = ui.LayoutView()
                container = ui.Container()
                container.add_item(ui.TextDisplay(f"## {Emoji.error} Access Restricted"))
                container.add_item(ui.TextDisplay(
                    f"The **Premium Generation** module is currently disabled by an administrator.\n"
                    f"Please check back later or contact support for further information."
                ))
                container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
                container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
                view.add_item(container)

                if ctx.interaction: await ctx.interaction.followup.send(view=view, ephemeral=True)
                else: await ctx.send(view=view)
                return

        banned, reason = await db.is_banned(ctx.author.id)
        if banned:
            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.error} Access Denied"))
            container.add_item(ui.TextDisplay(f"You have been banned from using the generator.\n**Reason:** {reason}"))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
            view.add_item(container)

            if ctx.interaction: await ctx.interaction.followup.send(view=view, ephemeral=True)
            else: await ctx.send(view=view)
            return

        if ctx.channel.id != channel_id:
            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.error} Wrong Channel"))
            container.add_item(ui.TextDisplay(
                f"This command can only be used in <#{channel_id}>.\n"
                f"Please navigate to the correct channel to generate **{tier.title()}** accounts."
            ))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
            view.add_item(container)

            if ctx.interaction: await ctx.interaction.followup.send(view=view, ephemeral=True)
            else: await ctx.send(view=view)
            return

        if ctx.guild.id != config.GUILD_ID:
            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.error} Access Denied"))
            container.add_item(ui.TextDisplay("This bot is not configured for use in this server."))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
            view.add_item(container)

            if ctx.interaction: await ctx.interaction.followup.send(view=view, ephemeral=True)
            else: await ctx.send(view=view)
            return

        has_role = any(role.id == int(role_id) for role in ctx.author.roles)
        if not has_role:
            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.error} Subscription Required"))
            container.add_item(ui.TextDisplay(f"You do not have the required role to use the **{tier.upper()}** generator."))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
            view.add_item(container)

            if ctx.interaction: await ctx.interaction.followup.send(view=view, ephemeral=True)
            else: await ctx.send(view=view)
            return

        can_gen, remaining = await db.check_cooldown(ctx.author.id, tier, cooldown)
        if not can_gen:
            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.loading} Cooldown in Effect"))
            container.add_item(ui.TextDisplay(
                f"You're generating too fast! You can use this generator again in **{round(remaining/60, 1)} minutes**."
            ))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
            view.add_item(container)

            if ctx.interaction: await ctx.interaction.followup.send(view=view, ephemeral=True)
            else: await ctx.send(view=view)
            return

        services = await db.get_services(tier)
        if service.lower() not in [s[0].lower() for s in services]:
            services_list = ", ".join([s[0] for s in services]) if services else "None"
            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.info} Service Unrecognized"))
            container.add_item(ui.TextDisplay(f"The service **{service}** was not found in the **{tier}** tier.\n**Available:** {services_list}"))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
            view.add_item(container)

            if ctx.interaction: await ctx.interaction.followup.send(view=view, ephemeral=True)
            else: await ctx.send(view=view)
            return

        item, service_type = await db.generate_item(service, tier)
        if not item:
            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.error} Out of Stock"))
            container.add_item(ui.TextDisplay(f"Sorry, **{service.title()}** ({tier}) is currently out of stock."))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
            view.add_item(container)

            if ctx.interaction: await ctx.interaction.followup.send(view=view, ephemeral=True)
            else: await ctx.send(view=view)
            return

        await db.set_cooldown(ctx.author.id, tier)
        await db.log_generation(ctx.author.id, service, tier)
        await db.track_generation(ctx.author.id, service, tier)

        from utils.logger import logger
        await logger.log_event(self.bot, "GEN_SUCCESS", {
            "user_name": ctx.author.name,
            "user_id": ctx.author.id,
            "user_avatar": ctx.author.avatar.url if ctx.author.avatar else None,
            "service": service,
            "tier": tier,
            "channel_id": ctx.channel.id
        })

        vouch_id = await db.get_setting("vouch_channel_id")
        vouch_channel_mention = f"<#{vouch_id}>" if vouch_id else "`#vouch-channel`"

        dm_view = ui.LayoutView()
        dm_container = ui.Container(accent_color=None)
        dm_container.add_item(ui.TextDisplay(f"# {service.title()} ({tier.title()}) Generated"))
        dm_container.add_item(ui.Separator())

        display_text = ""
        if service_type == "account":
            try:
                email, password = item.split("|", 1)
                display_text = f"### Credentials\n> **Email:** ||`{email}`||\n> **Password:** ||`{password}`||"
            except:
                display_text = f"### Details\n||```\n{item}\n```||"
        elif service_type == "vcc":
            try:
                card, mm, yy, cvv = item.split("|", 3)
                display_text = (
                    f"### VCC Information\n"
                    f"> **Card No:** ||`{card}`||\n"
                    f"> **Expiry:** ||`{mm}/{yy}`||\n"
                    f"> **CVV:** ||`{cvv}`||"
                )
            except:
                display_text = f"### VCC Details\n||```\n{item}\n```||"
        elif service_type == "code":
            display_text = f"### Redeem Code\n||`{item}`||"
        else:
            display_text = f"### Details\n||```\n{item}\n```||"

        dm_container.add_item(ui.TextDisplay(display_text))
        dm_container.add_item(ui.TextDisplay(f"### Vouching Requirement"))
        dm_container.add_item(ui.TextDisplay(
            f"After generating, you must vouch in {vouch_channel_mention} within **5 minutes** to avoid a temporary ban.\n"
            f"**Format:** `legit got {service}`\n"
            f"-# Failure to vouch may result in restricted access."
        ))
        dm_container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        dm_container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
        dm_view.add_item(dm_container)

        feedback_view = ui.LayoutView()
        feedback_container = ui.Container(accent_color=None)
        feedback_container.add_item(ui.TextDisplay(f"## {Emoji.success} Success"))
        feedback_container.add_item(ui.TextDisplay(f"Generated **{service.title()}**. Check your DMs!"))
        feedback_container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        feedback_container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
        feedback_view.add_item(feedback_container)

        try:
            await ctx.author.send(view=dm_view)
            if ctx.interaction:
                await ctx.interaction.followup.send(view=feedback_view, ephemeral=True)
            else:
                await ctx.send(view=feedback_view)
        except discord.Forbidden:
            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.error} Delivery Blocked"))
            container.add_item(ui.TextDisplay(f"I cannot send you a DM. Please enable DMs from server members to receive your **{service.title()}** account."))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
            view.add_item(container)

            if ctx.interaction: await ctx.interaction.followup.send(view=view, ephemeral=True)
            else: await ctx.send(view=view)

    @commands.hybrid_command(name="fgen", description="Generate from free gen stock")
    async def fgen(self, ctx, service: str):
        c_id = await db.get_setting("fgen_channel_id")
        r_id = await db.get_setting("fgen_role_id")
        if not c_id or not r_id:
            return await ctx.send(f"{Emoji.error} Free Gen mapping incomplete. Please configure via the Staff Dashboard.", ephemeral=True)

        cooldown_min = int(await db.get_setting("fgen_cooldown", "60"))
        await self._handle_gen(ctx, service, "free", cooldown_min * 60, int(r_id), int(c_id))

    @commands.hybrid_command(name="pgen", description="Generate from premium gen stock")
    async def pgen(self, ctx, service: str):
        c_id = await db.get_setting("pgen_channel_id")
        r_id = await db.get_setting("pgen_role_id")
        if not c_id or not r_id:
            return await ctx.send(f"{Emoji.error} Premium Gen mapping incomplete. Please configure via the Staff Dashboard.", ephemeral=True)

        cooldown_min = int(await db.get_setting("pgen_cooldown", "30"))
        await self._handle_gen(ctx, service, "premium", cooldown_min * 60, int(r_id), int(c_id))

    @commands.hybrid_command(name="bgen", description="Generate from booster gen stock")
    async def bgen(self, ctx, service: str):
        c_id = await db.get_setting("bgen_channel_id")
        r_id = await db.get_setting("bgen_role_id")
        if not c_id or not r_id:
            return await ctx.send(f"{Emoji.error} Booster Gen mapping incomplete. Please configure via the Staff Dashboard.", ephemeral=True)

        cooldown_min = int(await db.get_setting("bgen_cooldown", "30"))
        await self._handle_gen(ctx, service, "booster", cooldown_min * 60, int(r_id), int(c_id))

async def setup(bot):
    await bot.add_cog(GenerateCommands(bot))
"""
Project Name: APZX GEN Bot
Creator: 4iuc
GitHub: https://github.com/apzxcore
"""
