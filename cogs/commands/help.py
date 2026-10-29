import discord
from discord import ui
from discord.ext import commands
import config
from utils.emojis import emoji as Emoji

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="View the full APZX GEN Bot command guide")
    async def help(self, ctx):
        prefix = config.PREFIX
        client_id = self.bot.user.id

        view = ui.LayoutView()
        container = ui.Container(accent_color=None)

        header = ui.Section(
            ui.TextDisplay(f"# {Emoji.shield} **APZX GEN Bot Command Guide**"),
            ui.TextDisplay("Welcome to the official APZX GEN terminal. Use the commands below to navigate our systems."),
            accessory=ui.Thumbnail(
                media=discord.UnfurledMediaItem(url=self.bot.user.display_avatar.url),
                description="APZX Logo"
            )
        )
        container.add_item(header)
        container.add_item(ui.Separator())

        gen_text = (
            f"### {Emoji.sparkle} **Account Generation**\n"
            f"> `{prefix}fgen <service>` {Emoji.arrow} Generate from Free stock.\n"
            f"> `{prefix}bgen <service>` {Emoji.arrow} Generate from Booster stock.\n"
            f"> `{prefix}pgen <service>` {Emoji.arrow} Generate from Premium stock."
        )
        container.add_item(ui.TextDisplay(gen_text))

        status_text = (
            f"### {Emoji.stats} **Stock & Status**\n"
            f"> `{prefix}stock` {Emoji.arrow} View live account availability.\n"
            f"> `{prefix}cstatus` {Emoji.arrow} Check your status requirements."
        )
        container.add_item(ui.TextDisplay(status_text))

        vouch_text = (
            f"### {Emoji.lock} **Vouching Protocol**\n"
            f"After generating, you must vouch in <#{getattr(config, 'VOUCH_CHANNEL_ID', 1493194221463666788)}> within **5 minutes** to avoid a temporary ban.\n"
            f"**Format:** `legit got <service>`"
        )
        container.add_item(ui.TextDisplay(vouch_text))

        if ctx.author.guild_permissions.administrator:
            admin_text = (
                f"### {Emoji.crown} **Admin Operations**\n"
                f"> `{prefix}createfgen/pgen/bgen` {Emoji.arrow} Create a new service category.\n"
                f"> `{prefix}uploadstock <tier> <service> <file>` {Emoji.arrow} Bulk add accounts.\n"
                f"> `{prefix}deletefgen/pgen/bgen` {Emoji.arrow} Delete a service category.\n"
                f"> `{prefix}uploadstock` {Emoji.arrow} Bulk upload via text file.\n"
                f"> `{prefix}restock` {Emoji.arrow} Announce updates with role ping.\n"
                f"> `{prefix}ban/unban/tempban` {Emoji.arrow} Manage generator access."
            )
            container.add_item(ui.TextDisplay(admin_text))

        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"-# {Emoji.crown} Developed by 4iuc — APZX GEN Bot"))

        view.add_item(container)
        await ctx.send(view=view)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
"""
Project Name: APZX GEN Bot
Creator: 4iuc
GitHub: https://github.com/apzxcore
"""
