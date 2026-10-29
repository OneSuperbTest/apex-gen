import discord
from discord import ui
from discord.ext import commands
from database import db
import config
from utils.emojis import emoji as Emoji

class DeleteCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _handle_delete(self, ctx: commands.Context, tier: str):
        if ctx.guild.id != config.GUILD_ID:
            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.error} Access Denied"))
            container.add_item(ui.TextDisplay("This bot is not configured for use in this server."))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
            view.add_item(container)
            await ctx.send(view=view, ephemeral=True)
            return

        services = await db.get_services(tier)

        if not services:
            view = ui.LayoutView()
            container = ui.Container(accent_color=None)
            container.add_item(ui.TextDisplay(f"## {Emoji.error} No Services Found"))
            container.add_item(ui.TextDisplay(f"No **{tier}** services exist yet. Use `/create{tier[0]}gen` first."))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
            view.add_item(container)
            await ctx.send(view=view, ephemeral=True)
            return

        view = GeneratorView(services, "delete", tier)

        await ctx.send(view=view, ephemeral=True)

    @commands.hybrid_command(name="deletefgen", description="Delete a free gen category")
    async def deletefgen(self, ctx):
        if ctx.author.id not in config.OWNER_IDS: return
        await self._handle_delete(ctx, "free")

    @commands.hybrid_command(name="deletepgen", description="Delete a premium gen category")
    async def deletepgen(self, ctx):
        if ctx.author.id not in config.OWNER_IDS: return
        await self._handle_delete(ctx, "premium")

    @commands.hybrid_command(name="deletebgen", description="Delete a booster gen category")
    async def deletebgen(self, ctx):
        if ctx.author.id not in config.OWNER_IDS: return
        await self._handle_delete(ctx, "booster")

async def setup(bot):
    await bot.add_cog(DeleteCommands(bot))
"""
Project Name: APZX GEN Bot
Creator: 4iuc
GitHub: https://github.com/apzxcore
"""
