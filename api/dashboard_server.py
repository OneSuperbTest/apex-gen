from fastapi import FastAPI, HTTPException, Request, Depends, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse, HTMLResponse
import os
import json
import hmac
import hashlib
import base64
import time
import aiohttp
from database import db
import config
import uvicorn
import asyncio

app = FastAPI()

# ── Auth Helpers ──────────────────────────────────────────────────────────────

def create_token(user_id: str) -> str:
    """Create an HMAC-signed JWT-like token valid for 7 days."""
    payload = {"user_id": user_id, "exp": time.time() + (86400 * 7)}
    dump = json.dumps(payload)
    encoded = base64.urlsafe_b64encode(dump.encode()).decode().rstrip("=")
    signature = hmac.new(config.JWT_SECRET.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"

def verify_token(token: str) -> str | None:
    """Verify token signature and expiry. Returns user_id or None."""
    try:
        if "." not in token:
            return None
        encoded, signature = token.split(".")
        expected_sig = hmac.new(config.JWT_SECRET.encode(), encoded.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None

        padded = encoded + "=" * ((4 - len(encoded) % 4) % 4)
        dump = base64.urlsafe_b64decode(padded.encode()).decode()
        payload = json.loads(dump)
        if payload.get("exp", 0) < time.time():
            return None
        return payload.get("user_id")
    except Exception:
        return None

async def get_current_user(request: Request) -> str:
    """FastAPI dependency: enforce owner-only access."""
    token = request.cookies.get("apzx_auth")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user_id = verify_token(token)
    if not user_id or int(user_id) not in config.OWNER_IDS:
        raise HTTPException(status_code=403, detail="Forbidden")
    return user_id

# ── Static Files ─────────────────────────────────────────────────────────────

if os.path.exists("./dashboard"):
    app.mount("/static", StaticFiles(directory="./dashboard"), name="static")

# ── Pages ────────────────────────────────────────────────────────────────────

@app.get("/")
async def serve_dashboard(request: Request):
    """Serve the main dashboard or redirect to login."""
    token = request.cookies.get("apzx_auth")
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    if not token or not verify_token(token):
        return FileResponse("./dashboard/login.html", headers=headers)
    return FileResponse("./dashboard/index.html", headers=headers)

# ── Auth Endpoints ───────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "bot": "APZX GEN Bot"}

@app.get("/api/auth/login")
async def auth_login():
    auth_url = (
        f"https://discord.com/api/oauth2/authorize?client_id={config.DISCORD_CLIENT_ID}"
        f"&redirect_uri={config.DISCORD_REDIRECT_URI}&response_type=code&scope=identify"
    )
    return RedirectResponse(auth_url)

@app.get("/api/auth/callback")
async def auth_callback(code: str, response: Response):
    data = {
        'client_id': config.DISCORD_CLIENT_ID,
        'client_secret': config.DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': config.DISCORD_REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    async with aiohttp.ClientSession() as session:
        async with session.post('https://discord.com/api/oauth2/token', data=data, headers=headers) as res:
            if res.status != 200:
                return JSONResponse({"error": "Failed to get token"}, status_code=400)
            token_data = await res.json()
            access_token = token_data['access_token']

        async with session.get('https://discord.com/api/users/@me', headers={'Authorization': f'Bearer {access_token}'}) as res:
            user_data = await res.json()
            user_id = user_data['id']

    if int(user_id) not in config.OWNER_IDS:
        return HTMLResponse("<h1>Access Denied</h1><p>You are not an authorized owner.</p>", status_code=403)

    token = create_token(user_id)
    resp = RedirectResponse("/")
    resp.set_cookie(key="apzx_auth", value=token, httponly=True, path="/", samesite="strict")
    return resp

# ── Protected API Endpoints ──────────────────────────────────────────────────

@app.get("/api/auth/me", dependencies=[Depends(get_current_user)])
async def auth_me(request: Request):
    user_id = verify_token(request.cookies.get("apzx_auth"))
    bot = request.app.state.bot

    await bot.wait_until_ready()

    if not bot.user.avatar:
        raise HTTPException(status_code=500, detail="Bot does not have a custom avatar set. Please set an avatar to continue.")

    user = await bot.fetch_user(int(user_id))
    return {
        "id": str(user.id),
        "username": user.name,
        "avatar": str(user.display_avatar.url),
        "bot_avatar": str(bot.user.display_avatar.url)
    }

@app.get("/api/get-settings", dependencies=[Depends(get_current_user)])
async def get_all_settings():
    keys = [
        "bot_status", "bot_activity_type", "bot_activity_text",
        "status_req", "invite_req",
        "premium_enabled", "invite_system_enabled",
        "fgen_channel_id", "fgen_role_id", "fgen_cooldown",
        "pgen_channel_id", "pgen_role_id", "pgen_cooldown",
        "bgen_channel_id", "bgen_role_id", "bgen_cooldown",
        "vouch_channel_id", "logs_channel_id", "restock_channel_id",
        "restock_ping_enabled", "restock_role_id"
    ]
    result = {}
    for k in keys:
        result[k] = await db.get_setting(k)
    return result

@app.get("/api/stats", dependencies=[Depends(get_current_user)])
async def get_stats():
    return await db.get_all_stock_counts()

@app.get("/api/setup-status")
async def setup_status():
    return {"setup_completed": await db.get_setup_status()}

@app.get("/api/public/bot-info")
async def get_bot_info(request: Request):
    bot = request.app.state.bot
    await bot.wait_until_ready()
    if not bot.user:
        return {"name": "APZX GEN BOT", "avatar": ""}
    return {
        "name": bot.user.name,
        "avatar": str(bot.user.display_avatar.url) if bot.user.display_avatar else ""
    }

@app.get("/api/guild/channels", dependencies=[Depends(get_current_user)])
async def get_channels(request: Request):
    bot = request.app.state.bot
    await bot.wait_until_ready()
    try:
        guild_id = int(config.GUILD_ID)
        guild = bot.get_guild(guild_id)
    except (ValueError, TypeError):
        guild = None
    if not guild:
        guild = bot.guilds[0] if bot.guilds else None
    return [{"id": str(c.id), "name": c.name} for c in guild.text_channels] if guild else []

@app.get("/api/guild/roles", dependencies=[Depends(get_current_user)])
async def get_roles(request: Request):
    bot = request.app.state.bot
    await bot.wait_until_ready()
    try:
        guild_id = int(config.GUILD_ID)
        guild = bot.get_guild(guild_id)
    except (ValueError, TypeError):
        guild = None
    if not guild:
        guild = bot.guilds[0] if bot.guilds else None
    return [{"id": str(r.id), "name": r.name} for r in guild.roles if r.name != "@everyone"] if guild else []

@app.get("/api/guild/free-users", dependencies=[Depends(get_current_user)])
async def get_free_users(request: Request):
    bot = request.app.state.bot
    await bot.wait_until_ready()
    try:
        guild_id = int(config.GUILD_ID)
        guild = bot.get_guild(guild_id)
    except (ValueError, TypeError):
        guild = None
    if not guild:
        return []

    role_id_str = await db.get_setting("fgen_role_id")
    if not role_id_str:
        return []

    role = guild.get_role(int(role_id_str))
    if not role:
        return []

    users = []
    for m in role.members:
        users.append({
            "name": m.display_name,
            "username": m.name,
            "avatar": str(m.display_avatar.url)
        })
    return users

@app.post("/api/setup", dependencies=[Depends(get_current_user)])
async def run_setup(request: Request):
    data = await request.json()
    print(f"[DASH] Saving Settings: {data}")
    for key, value in data.items():
        await db.set_setting(key, value)
    return {"status": "success"}

@app.get("/api/services/{tier}", dependencies=[Depends(get_current_user)])
async def get_services(tier: str):
    return {"services": await db.get_services(tier)}

@app.post("/api/services/create", dependencies=[Depends(get_current_user)])
async def create_service(request: Request):
    data = await request.json()
    success = await db.create_service(data.get("name"), data.get("tier"), data.get("type", "account"))
    return {"success": success}

@app.get("/api/stock/view/{tier}/{service}", dependencies=[Depends(get_current_user)])
async def view_stock(tier: str, service: str):
    items = await db.get_raw_stock(service, tier)
    return {"items": items}

# ── Add Stock (Web + Ping) ──────────────────────────────────────────────────

@app.post("/api/stock/add", dependencies=[Depends(get_current_user)])
async def add_stock(request: Request):
    data = await request.json()
    service_name = data.get("service")
    tier = data.get("tier")
    items = data.get("items", [])

    count = await db.add_stock(service_name, tier, items)

    if count > 0:
        bot = request.app.state.bot
        token = request.cookies.get("apzx_auth")
        user_id = verify_token(token)
        admin_user = await bot.fetch_user(int(user_id)) if user_id else None
        admin_name = admin_user.name if admin_user else "Web Admin"
        admin_mention = admin_user.mention if admin_user else "`Web Admin`"

        from utils.logger import logger
        services = await db.get_services(tier)
        new_total = 0
        for name, _ in services:
            if name.lower() == service_name.lower():
                counts = await db.get_all_stock_counts()
                new_total = counts.get(tier, {}).get(service_name, 0)
                break

        await logger.log_event(bot, "STOCK_REFRESH", {
            "admin_name": admin_name,
            "service": service_name,
            "tier": tier,
            "added": count,
            "new_total": new_total,
            "items": items
        })

        ping_enabled = await db.get_setting("restock_ping_enabled", "0")
        if ping_enabled != "1":
            print(f"[PING] Skipping restock ping: disabled in settings (value: {ping_enabled!r})")
        else:
            restock_cid = await db.get_setting("restock_channel_id")
            if not restock_cid:
                print("[PING] Skipping restock ping: restock_channel_id not set")
            else:
                restock_channel = bot.get_channel(int(restock_cid))
                if not restock_channel:
                    try:
                        restock_channel = await bot.fetch_channel(int(restock_cid))
                    except Exception as e:
                        print(f"[PING] fetch_channel failed: {e}")
                        restock_channel = None
                if restock_channel:
                    from discord.ui import LayoutView, Container, TextDisplay, Separator, Section, Thumbnail
                    from utils.emojis import emoji as Emoji
                    import discord

                    restock_role_id = await db.get_setting("restock_role_id")

                    restock_view = LayoutView()
                    restock_container = Container(accent_color=None)

                    if restock_role_id:
                        restock_container.add_item(TextDisplay(f"<@&{restock_role_id}>"))

                    restock_container.add_item(TextDisplay(
                        f"## {Emoji.sparkle}  New Stock Has Arrived!  {Emoji.sparkle}"
                    ))
                    restock_container.add_item(Separator())

                    t_lower = tier.lower()
                    tier_emoji = getattr(Emoji, t_lower, Emoji.dot)

                    info_section = Section(
                        TextDisplay(
                            f"{tier_emoji} **Service:** `{service_name.title()}`\n"
                            f"{Emoji.plus} **Added:** `+{count}` Units\n"
                            f"{Emoji.stats} **Stock Status:** `{new_total}` Total"
                        ),
                        accessory=Thumbnail(
                            media=discord.UnfurledMediaItem(url=bot.user.display_avatar.url),
                            description="APZX GEN Security"
                        )
                    )
                    restock_container.add_item(info_section)

                    restock_container.add_item(Separator(spacing=discord.SeparatorSpacing.small))
                    restock_container.add_item(TextDisplay(
                        f"{Emoji.apzx_icon} **Handled by:** {admin_mention}\n"
                        f"{Emoji.success} **Successfully updated! Go grab yours now.**\n"
                        f"-# {Emoji.blue_crown} 4iuc | APZX GEN Bot — Inventory Protocol"
                    ))
                    restock_view.add_item(restock_container)

                    mentions = discord.AllowedMentions(roles=True, everyone=False, users=False)

                    try:
                        await restock_channel.send(
                            view=restock_view,
                            allowed_mentions=mentions
                        )
                        print(f"[PING] Restock ping sent successfully to #{restock_channel.name}")
                    except Exception as e:
                        print(f"[PING] Send failed: {e}")
                else:
                    print(f"[PING] Channel {restock_cid} not found")

    return {"added": count}

# ── Server Startup ───────────────────────────────────────────────────────────

async def start_server(bot_instance):
    """Start the FastAPI uvicorn server. Must be called with the bot instance."""
    app.state.bot = bot_instance
    config_server = uvicorn.Config(app, host="0.0.0.0", port=config.DASHBOARD_PORT, log_level="error")
    server = uvicorn.Server(config_server)
    await server.serve()

"""
Project Name: APZX GEN Bot
Creator: 4iuc
GitHub: https://github.com/apzxcore
"""
