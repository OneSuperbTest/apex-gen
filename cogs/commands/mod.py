import discord
from discord import ui
from discord.ext import commands
from database import db
from utils.emojis import emoji as Emoji
import config

class ModCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _moderator_check(self, ctx: commands.Context) -> bool:
        """Returns True if user has admin perms, else sends error and returns False."""
        if not ctx.author.guild_permissions.administrator:
            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.error} Access Denied"))
            container.add_item(ui.TextDisplay("You do not have permission to use moderation commands."))
            view.add_item(container)
            await ctx.send(view=view, ephemeral=True)
            return False
        return True

    @commands.hybrid_command(name="ban", description="Permanently ban a user from the generator")
    async def ban(self, ctx: commands.Context, user: discord.User, *, reason: str = "No reason provided"):
        """Permanently ban a user from all generator commands."""
        if not await self._moderator_check(ctx):
            return

        await db.ban_user(user.id, reason)

        view = ui.LayoutView()
        container = ui.Container(accent_color=None)
        container.add_item(ui.TextDisplay(f"## {Emoji.trash} User Banned"))
        container.add_item(ui.TextDisplay(f"**User:** {user.mention} (`{user.id}`)\n**Reason:** {reason}\n**Type:** Permanent"))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
        view.add_item(container)
        await ctx.send(view=view)

    @commands.hybrid_command(name="tempban", description="Temporarily ban a user from the generator")
    async def tempban(self, ctx: commands.Context, user: discord.User, duration_seconds: int, *, reason: str = "No reason provided"):
        """Temporarily ban a user. Duration is in seconds."""
        if not await self._moderator_check(ctx):
            return

        if duration_seconds < 60:
            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.error} Invalid Duration"))
            container.add_item(ui.TextDisplay("Duration must be at least 60 seconds."))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
            view.add_item(container)
            await ctx.send(view=view, ephemeral=True)
            return

        await db.ban_user(user.id, reason, duration_seconds)

        view = ui.LayoutView()
        container = ui.Container(accent_color=None)
        container.add_item(ui.TextDisplay(f"## {Emoji.warning} Temporary Ban"))
        container.add_item(ui.TextDisplay(
            f"**User:** {user.mention}\n"
            f"**Duration:** `{duration_seconds}` seconds (`{duration_seconds // 60}` minutes)\n"
            f"**Reason:** {reason}"
        ))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
        view.add_item(container)
        await ctx.send(view=view)

    @commands.hybrid_command(name="unban", description="Unban a user from the generator")
    async def unban(self, ctx: commands.Context, user: discord.User):
        """Remove a ban from a user. Owner only."""
        if ctx.author.id not in config.OWNER_IDS:
            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.error} Access Denied"))
            container.add_item(ui.TextDisplay("Only the bot owner can unban users."))
            view.add_item(container)
            await ctx.send(view=view, ephemeral=True)
            return

        await db.unban_user(user.id)

        view = ui.LayoutView()
        container = ui.Container(accent_color=None)
        container.add_item(ui.TextDisplay(f"## {Emoji.success} User Unbanned"))
        container.add_item(ui.TextDisplay(f"Successfully removed generator ban for {user.mention}."))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
        view.add_item(container)
        await ctx.send(view=view)

async def setup(bot):
    await bot.add_cog(ModCommands(bot))

"""
Project Name: APZX GEN Bot
Creator: 4iuc
GitHub: https://github.com/apzxcore
"""
