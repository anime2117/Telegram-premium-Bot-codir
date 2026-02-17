python -m uvicorn main:app --host 0.0.0.0 --port 8000
import os
import sqlite3
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# ===================== SHOP SETTINGS =====================
SHOP_NAME = "𝐒𝐞𝐜𝐮𝐫𝐞 𝐒𝐮𝐫𝐟 𝐙𝐨𝐧𝐞"
BKASH_NUMBER = "01642012385"
NAGAD_NUMBER = "01788098356"
DB_PATH = "shop.db"

# ===================== ENV (Railway Safe) =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Admin ID must be int. Defaults to 0 if not found.
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

def get_public_url() -> str:
    manual = os.getenv("PUBLIC_URL", "").strip()
    if manual:
        return manual.rstrip("/")
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if railway_domain:
        return f"https://{railway_domain}".rstrip("/")
    return ""

PUBLIC_URL = get_public_url()

# ===================== CHECKOUT STATES =====================
NAME, PHONE, PAYMENT, TRX = range(4)

# ===================== APP =====================
tg_app = Application.builder().token(BOT_TOKEN).build()

# ===================== DB HELPERS =====================
def db():
    return sqlite3.connect(DB_PATH)

def init_db():
    with db() as con:
        cur = con.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            duration_days INTEGER NOT NULL DEFAULT 30,
            desc TEXT DEFAULT ''
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            duration_days INTEGER NOT NULL,
            total INTEGER NOT NULL,
            payment_method TEXT NOT NULL,
            trx_id TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS user_state(
            user_id INTEGER PRIMARY KEY,
            live_chat INTEGER NOT NULL DEFAULT 0
        )
        """)
    
            ]
            cur.executemany("INSERT INTO products(name,price,stock,duration_days,desc) VALUES (?,?,?,?,?)", seed)
        con.commit()

def set_live_chat(user_id: int, enabled: bool):
    with db() as con:
        cur = con.cursor()
        cur.execute("""
        INSERT INTO user_state(user_id, live_chat)
        VALUES (?,?)
        ON CONFLICT(user_id) DO UPDATE SET live_chat=excluded.live_chat
        """, (user_id, 1 if enabled else 0))
        con.commit()

def is_live_chat(user_id: int) -> bool:
    with db() as con:
        cur = con.cursor()
        cur.execute("SELECT live_chat FROM user_state WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        return bool(row and row[0] == 1)

# ===================== UI HELPERS =====================
def money(n: int) -> str:
    return f"{n}৳"

def is_admin(update: Update) -> bool:
    return update.effective_user and update.effective_user.id == ADMIN_CHAT_ID

def kb_main():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍 Shop", callback_data="shop")],
        [InlineKeyboardButton("💬 Live Chat", callback_data="livechat")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
    ])

# [Note: Rest of the KB and Command logic remains similar but cleaned up for consistency]

# ===================== FASTAPI LIFESPAN =====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set in environment variables!")
    
    init_db()
    await tg_app.initialize()
    if PUBLIC_URL:
        await tg_app.bot.set_webhook(url=f"{PUBLIC_URL}/webhook")
        print(f"Webhook set to: {PUBLIC_URL}/webhook")
    await tg_app.start()
    yield
    await tg_app.stop()
    await tg_app.shutdown()

api = FastAPI(lifespan=lifespan)

@api.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return Response(status_code=200)

@api.get("/")
def home():
    return {"status": "running", "shop": SHOP_NAME}

# [Keep your Handlers and Conversation logic as it was, they were well-structured!]
