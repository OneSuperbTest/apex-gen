import discord
from discord import ui
from discord.ext import commands
import config
from utils.emojis import emoji as Emoji
from database import db
from io import BytesIO
import os

class AdminUtility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="uploadstock", description="Bulk upload accounts from a text file")
    @commands.has_permissions(administrator=True)
    async def uploadstock(self, ctx: commands.Context, tier: str, service: str, file: discord.Attachment):
        """Bulk upload accounts from a .txt file attachment."""
        if tier.lower() not in ["free", "premium", "booster"]:
            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.error} Selection Error"))
            container.add_item(ui.TextDisplay(f"The tier **{tier}** is invalid.\n**Valid options:** `free`, `premium`, `booster`"))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
            view.add_item(container)
            await ctx.send(view=view, ephemeral=True)
            return

        if not file.filename.endswith('.txt'):
            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.error} File Error"))
            container.add_item(ui.TextDisplay(f"Unsupported file format: `{file.filename}`.\nPlease upload a `.txt` file containing credentials."))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
            view.add_item(container)
            await ctx.send(view=view, ephemeral=True)
            return

        await ctx.defer(ephemeral=True)

        try:
            content = await file.read()
            items = content.decode('utf-8').splitlines()
            items = [i.strip() for i in items if i.strip()]

            if not items:
                view = ui.LayoutView()
                container = ui.Container(accent_color=None)
                container.add_item(ui.TextDisplay(f"## {Emoji.warning} Import Error"))
                container.add_item(ui.TextDisplay("The uploaded file is empty or contains no valid credentials."))
                container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
                container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
                view.add_item(container)
                await ctx.send(view=view, ephemeral=True)
                return

            added = await db.add_stock(service, tier, items)

            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.success} Bulk Upload Successful"))
            container.add_item(ui.TextDisplay(f"Added **{added}** accounts to **{service.title()}** ({tier.title()})."))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
            view.add_item(container)
            await ctx.send(view=view, ephemeral=True)
        except Exception as e:
            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.error} Critical Failure"))
            container.add_item(ui.TextDisplay(f"Failed to process inventory upload: `{str(e)}`"))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
            view.add_item(container)
            await ctx.send(view=view, ephemeral=True)

    @commands.hybrid_command(name="addstock", description="Add stock directly via inline text")
    @commands.has_permissions(administrator=True)
    async def addstock(self, ctx: commands.Context, tier: str, service: str, *, items: str):
        """Add stock directly by typing items separated by newlines."""
        if tier.lower() not in ["free", "premium", "booster"]:
            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.error} Selection Error"))
            container.add_item(ui.TextDisplay(f"The tier **{tier}** is invalid.\n**Valid options:** `free`, `premium`, `booster`"))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
            view.add_item(container)
            await ctx.send(view=view, ephemeral=True)
            return

        parsed_items = [line.strip() for line in items.split('\n') if line.strip()]

        if not parsed_items:
            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.warning} Empty Input"))
            container.add_item(ui.TextDisplay("No valid items provided. Separate each item with a new line."))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
            view.add_item(container)
            await ctx.send(view=view, ephemeral=True)
            return

        added = await db.add_stock(service, tier, parsed_items)

        view = ui.LayoutView()
        container = ui.Container(accent_color=None)
        container.add_item(ui.TextDisplay(f"## {Emoji.success} Stock Added"))
        container.add_item(ui.TextDisplay(f"Added **{added}** item(s) to **{service.title()}** ({tier.title()})."))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
        view.add_item(container)
        await ctx.send(view=view, ephemeral=True)

    @commands.hybrid_command(name="restock", description="Announce a new stock update with a role ping")
    @commands.has_permissions(administrator=True)
    async def restock(self, ctx: commands.Context, tier: str, service: str):
        """Post a formatted restock announcement with optional role ping."""
        await ctx.defer()

        view = ui.LayoutView()
        container = ui.Container(accent_color=None)

        header = ui.Section(
            ui.TextDisplay(f"# {Emoji.sparkle} **New Stock Announcement** {Emoji.sparkle}"),
            ui.TextDisplay(f"Our inventory has just been refreshed! Get your accounts now."),
            accessory=ui.Thumbnail(media=discord.UnfurledMediaItem(url=self.bot.user.display_avatar.url))
        )
        container.add_item(header)
        container.add_item(ui.Separator())

        container.add_item(ui.TextDisplay(
            f"### {Emoji.stock} **Restock Details**\n"
            f"> **Service:** {service.title()}\n"
            f"> **Tier:** {tier.title()}\n"
            f"> **Status:** `Online` {Emoji.online}"
        ))

        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"-# Use `/fgen`, `/pgen`, or `/bgen` to generate.\n-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))

        view.add_item(container)

        ping_role = ctx.guild.get_role(config.RESTOCK_ROLE_ID)
        ping_text = ping_role.mention if ping_role else "@everyone"

        await ctx.send(content=ping_text, view=view)

    @commands.hybrid_command(name="resetcooldown", description="Reset a user's generation cooldown")
    @commands.has_permissions(administrator=True)
    async def resetcooldown(self, ctx: commands.Context, user: discord.User, tier: str = None):
        """Reset cooldown for a user. If tier is omitted, resets all tiers."""
        tier_param = tier.lower() if tier else None
        await db.reset_cooldown(user.id, tier_param)

        tier_label = f"`{tier.title()}` tier" if tier_param else "all tiers"
        view = ui.LayoutView()
        container = ui.Container(accent_color=None)
        container.add_item(ui.TextDisplay(f"## {Emoji.gear} Cooldown Reset"))
        container.add_item(ui.TextDisplay(f"**User:** {user.mention}\n**Reset:** {tier_label}\n**Status:** `Success` {Emoji.success}"))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
        view.add_item(container)
        await ctx.send(view=view, ephemeral=True)

    @commands.hybrid_command(name="genlogs", description="View recent generation logs (admin only)")
    @commands.has_permissions(administrator=True)
    async def genlogs(self, ctx: commands.Context, limit: int = 10):
        """View recent generation logs."""
        if limit > 50:
            limit = 50
        from database.db import get_admin_logs
        rows = await get_admin_logs(limit=limit)

        view = ui.LayoutView()
        container = ui.Container(accent_color=None)
        container.add_item(ui.TextDisplay(f"# {Emoji.stats} Generation Logs"))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        if not rows:
            container.add_item(ui.TextDisplay("**No generation logs found.**"))
        else:
            lines = []
            for user_id, service, tier, gen_at in rows:
                member = ctx.guild.get_member(int(user_id)) if ctx.guild else None
                name = member.display_name if member else f"User {user_id}"
                lines.append(f"- {Emoji.dot} **{name}** → {service.title()} ({tier}) at {gen_at}")
            container.add_item(ui.TextDisplay("\n".join(lines)))

        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
        view.add_item(container)
        await ctx.send(view=view)

    @commands.hybrid_command(name="backup", description="Create a backup of the generator database")
    @commands.has_permissions(administrator=True)
    async def backup(self, ctx: commands.Context):
        """Create a timestamped backup of the SQLite database."""
        import shutil
        from datetime import datetime
        from database.db import DB_PATH

        backup_path = DB_PATH + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        try:
            shutil.copy2(DB_PATH, backup_path)
            file_size = os.path.getsize(backup_path) / 1024  # KB

            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.success} Backup Created"))
            container.add_item(ui.TextDisplay(
                f"**Location:** `{backup_path}`\n"
                f"**Size:** `{file_size:.1f} KB`"
            ))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
            view.add_item(container)
            await ctx.send(view=view, ephemeral=True)
        except Exception as e:
            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.error} Backup Failed"))
            container.add_item(ui.TextDisplay(f"Could not create backup: `{str(e)}`"))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
            view.add_item(container)
            await ctx.send(view=view, ephemeral=True)

    @commands.hybrid_command(name="setcooldown", description="Update the cooldown for a specific tier")
    @commands.has_permissions(administrator=True)
    async def setcooldown(self, ctx: commands.Context, tier: str, seconds: int):
        """Set generation cooldown in seconds for a tier."""
        tier = tier.lower()
        if tier not in ["free", "premium", "booster"]:
            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.error} Selection Error"))
            container.add_item(ui.TextDisplay(f"Tier **{tier}** is invalid.\n**Valid options:** `free`, `premium`, `booster`"))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
            view.add_item(container)
            await ctx.send(view=view, ephemeral=True)
            return

        cooldown_min = max(1, round(seconds // 60))

        if tier == "free":
            await db.set_setting("fgen_cooldown", str(cooldown_min))
        elif tier == "premium":
            await db.set_setting("pgen_cooldown", str(cooldown_min))
        elif tier == "booster":
            await db.set_setting("bgen_cooldown", str(cooldown_min))

        view = ui.LayoutView()
        container = ui.Container(accent_color=None)
        container.add_item(ui.TextDisplay(f"## {Emoji.gear} Synchronized"))
        container.add_item(ui.TextDisplay(f"Set **{tier.title()}** generation cooldown to `{seconds}` seconds (`{cooldown_min}` minutes).\n**Status:** `Committed to DB` {Emoji.success}"))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
        view.add_item(container)
        await ctx.send(view=view)

async def setup(bot):
    await bot.add_cog(AdminUtility(bot))

"""
Project Name: APZX GEN Bot
Creator: 4iuc
GitHub: https://github.com/apzxcore
"""
