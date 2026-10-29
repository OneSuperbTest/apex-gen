import discord
from discord import ui
from discord.ext import commands
from database import db
import config
from utils.emojis import emoji as Emoji

class CreateCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _handle_create(self, ctx: commands.Context, service: str, tier: str, service_type: str):
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

        created = await db.create_service(service, tier, service_type)

        view = ui.LayoutView()
        container = ui.Container(accent_color=None)
        if created:
            container.add_item(ui.TextDisplay(f"## {Emoji.success} Service Created"))
            container.add_item(ui.TextDisplay(f"Successfully created **{tier.upper()}** service: **{service.title()}** (`{service_type}`)"))
        else:
            container.add_item(ui.TextDisplay(f"## {Emoji.error} Creation Failed"))
            container.add_item(ui.TextDisplay(f"Service **{service}** already exists in **{tier}** tier!"))

        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))
        view.add_item(container)
        await ctx.send(view=view)

    @commands.hybrid_command(name="createfgen", description="Create a category for free stock")
    @discord.app_commands.choices(service_type=[
        discord.app_commands.Choice(name="Account (email|pass)", value="account"),
        discord.app_commands.Choice(name="VCC (card|mm|yy|cvv)", value="vcc"),
        discord.app_commands.Choice(name="Redeem Code", value="code")
    ])
    async def createfgen(self, ctx, service: str, service_type: str):
        if ctx.author.id not in config.OWNER_IDS: return
        await self._handle_create(ctx, service, "free", service_type)

    @commands.hybrid_command(name="createpgen", description="Create a category for premium stock")
    @discord.app_commands.choices(service_type=[
        discord.app_commands.Choice(name="Account (email|pass)", value="account"),
        discord.app_commands.Choice(name="VCC (card|mm|yy|cvv)", value="vcc"),
        discord.app_commands.Choice(name="Redeem Code", value="code")
    ])
    async def createpgen(self, ctx, service: str, service_type: str):
        if ctx.author.id not in config.OWNER_IDS: return
        await self._handle_create(ctx, service, "premium", service_type)

    @commands.hybrid_command(name="createbgen", description="Create a category for booster stock")
    @discord.app_commands.choices(service_type=[
        discord.app_commands.Choice(name="Account (email|pass)", value="account"),
        discord.app_commands.Choice(name="VCC (card|mm|yy|cvv)", value="vcc"),
        discord.app_commands.Choice(name="Redeem Code", value="code")
    ])
    async def createbgen(self, ctx, service: str, service_type: str):
        if ctx.author.id not in config.OWNER_IDS: return
        await self._handle_create(ctx, service, "booster", service_type)

async def setup(bot):
    await bot.add_cog(CreateCommands(bot))
"""
Project Name: APZX GEN Bot
Creator: 4iuc
GitHub: https://github.com/apzxcore
"""
