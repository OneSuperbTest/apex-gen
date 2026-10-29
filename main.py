import discord
from discord.ext import commands
import time
from datetime import datetime
from discord.ext import commands
from dotenv import load_dotenv
from database import db
import config
from colorama import Fore, Style, init
from api.dashboard_server import app
import uvicorn
import asyncio
import os
import sys

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

init(autoreset=True)
load_dotenv()

class GeneratorBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        self.start_time = datetime.now()

        super().__init__(
            command_prefix=config.PREFIX,
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        os.system('cls' if os.name == 'nt' else 'clear')

        try:
            with open('ansi.txt', 'r', encoding='utf-8') as f:
                print(f"{Fore.CYAN}{f.read()}{Style.RESET_ALL}")
        except FileNotFoundError:
            print(f"""
{Fore.CYAN}
 ╔══════════════════════════════════════════╗
 ║    APZX GEN BOT  |  Dev: 4iuc            ║
 ║    github.com/apzxcore                   ║
 ╚══════════════════════════════════════════╝
{Style.RESET_ALL}
            """)

        print(f"{Fore.YELLOW}[SYSTEM]{Style.RESET_ALL} Initializing Core Services...")
        await db.init_db()
        time.sleep(0.5)

        cogs_dir = './cogs'
        loaded = 0
        failed = 0
        for root, dirs, files in os.walk(cogs_dir):
            for filename in files:
                if filename.endswith('.py') and not filename.startswith('__'):
                    relative_path = os.path.relpath(os.path.join(root, filename), '.')
                    ext_path = relative_path.replace(os.sep, '.')[:-3]
                    try:
                        await self.load_extension(ext_path)
                        print(f"  {Fore.GREEN}»{Style.RESET_ALL} Loaded: {ext_path}")
                        loaded += 1
                    except Exception as e:
                        print(f"  {Fore.RED}»{Style.RESET_ALL} Failed: {ext_path} ({e})")
                        failed += 1

        try:
            synced = await self.tree.sync()
            print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Sync Failed: {e}")

        if failed > 0:
            print(f"{Fore.RED}[WARN]{Style.RESET_ALL} {failed} cog(s) failed to load. Check logs above.")

        # Start Dashboard
        app.state.bot = self
        config_server = uvicorn.Config(app, host="0.0.0.0", port=config.DASHBOARD_PORT, log_level="error")
        server = uvicorn.Server(config_server)
        asyncio.create_task(server.serve())
        dash_url = getattr(config, 'DASHBOARD_URL', f'http://localhost:{config.DASHBOARD_PORT}')
        print(f"{Fore.MAGENTA}[DASH]{Style.RESET_ALL} Panel active on {dash_url}")

        # Live Status Loop
        asyncio.create_task(self.status_updater())

    async def status_updater(self):
        """Update bot status/activity every 60 seconds based on DB settings."""
        await self.wait_until_ready()
        print(f"{Fore.YELLOW}[SYSTEM]{Style.RESET_ALL} Status Updater active.")
        while not self.is_closed():
            try:
                status_str = await db.get_setting("bot_status", "online")
                act_type_str = await db.get_setting("bot_activity_type", "watching")
                act_text = await db.get_setting("bot_activity_text", "APZX | Generators")

                status_map = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd}
                act_map = {
                    "watching": discord.ActivityType.watching,
                    "playing": discord.ActivityType.playing,
                    "listening": discord.ActivityType.listening,
                    "competing": discord.ActivityType.competing
                }

                status = status_map.get(status_str, discord.Status.online)
                act_type = act_map.get(act_type_str, discord.ActivityType.watching)

                activity = discord.Activity(type=act_type, name=act_text)
                await self.change_presence(status=status, activity=activity)
            except Exception as e:
                print(f"Status Update Error: {e}")
            await asyncio.sleep(60)

    async def on_ready(self):
        print(f"""
{Fore.MAGENTA}╔════════════════════════════════════════════╗
║  APZX GEN BOT — Fully Operational           ║
║  Identity:   {self.user.name}#{self.user.discriminator}
║  ID:         {self.user.id}
║  Guilds:     {len(self.guilds)}
║  Developer:  4iuc | github.com/apzxcore
║  Status:     ONLINE
{Fore.MAGENTA}╚════════════════════════════════════════════╝
{Fore.CYAN}Credits: APZX GEN Bot™ — Developed by 4iuc{Style.RESET_ALL}
        """)

        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="APZX | Generators"
        )
        await self.change_presence(activity=activity)

    def get_guild_prefix(self, guild_id: int):
        return config.PREFIX

def validate_config() -> bool:
    """Validate config.py before starting. Returns True if valid."""
    issues = []

    if not config.PREFIX:
        issues.append("PREFIX is empty")
    if not isinstance(config.PREFIX, str):
        issues.append("PREFIX must be a string")
    if not isinstance(config.OWNER_IDS, list) or not config.OWNER_IDS:
        issues.append("OWNER_IDS must be a non-empty list")
    if not isinstance(config.GUILD_ID, int) or config.GUILD_ID <= 0:
        issues.append("GUILD_ID must be a positive integer")
    if not isinstance(config.VOUCH_BAN_DURATION, int) or config.VOUCH_BAN_DURATION < 0:
        issues.append("VOUCH_BAN_DURATION must be a non-negative integer")
    if config.DISCORD_CLIENT_ID and config.DISCORD_CLIENT_SECRET:
        pass  # OAuth2 is optional for basic bot use
    if not config.JWT_SECRET or config.JWT_SECRET == "Add_Your_JWT_Secret_Here":
        issues.append("JWT_SECRET is not set (required for dashboard OAuth2)")

    if issues:
        print(f"{Fore.RED}[CONFIG]{Style.RESET_ALL} Validation failed:")
        for issue in issues:
            print(f"  {Fore.RED}✗{Style.RESET_ALL} {issue}")
        return False

    return True

def main():
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print(f"{Fore.RED}[CRITICAL]{Style.RESET_ALL} Token missing from .env file")
        print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Add DISCORD_TOKEN=your_token_here to .env")
        return

    if not validate_config():
        print(f"{Fore.RED}[CRITICAL]{Style.RESET_ALL} Config validation failed. Fix issues above before starting.")
        return

    bot = GeneratorBot()
    bot.run(token)

if __name__ == '__main__':
    main()

"""
Project Name: APZX GEN Bot
Creator: 4iuc
GitHub: https://github.com/apzxcore
"""
