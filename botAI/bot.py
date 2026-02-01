import logging
import re
import requests
import sys
import sqlite3
import random
import json
import os
import asyncio
import io
import traceback
import time as time_module 
from datetime import datetime, time, timedelta, timezone
from groq import Groq
import discord
from discord.ext import commands
import aiohttp
import string
from threading import Thread
from flask import Flask, jsonify
from dotenv import load_dotenv

# Load environment variables dari .env file
load_dotenv()

# --- MYSQL IMPORTS ---
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    print("⚠️ Module 'mysql-connector-python' tidak ditemukan. Install: pip install mysql-connector-python")

# --- FIREBASE IMPORTS (SAFE MODE) ---
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("⚠️ Module 'firebase-admin' tidak ditemukan. Install: pip install firebase-admin")

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    JobQueue
)
from telegram.request import HTTPXRequest
from simpleeval import simple_eval

# TIDAK PERLU .env - CREDENTIALS LANGSUNG DI SINI
# ==========================================
# KONFIGURASI UTAMA (DARI .env FILE)
# ==========================================

# --- TOKEN & API KEYS ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# --- MYSQL CONFIGURATION ---
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', ''),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', '')
}

# --- FIREBASE CONFIGURATION (FIRESTORE) ---
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
FIREBASE_APP_ID = os.getenv("FIREBASE_APP_ID", "")
SERVICE_ACCOUNT_KEY_PATH = os.getenv("SERVICE_ACCOUNT_KEY_PATH", "serviceAccountKey.json")
TARGET_FIRESTORE_USER_ID = os.getenv("TARGET_FIRESTORE_USER_ID", "")

# --- IDs & LINKS ---
ADMIN_USER_IDS = [int(x.strip()) for x in os.getenv("ADMIN_USER_IDS", "1642493057,777000").split(",")]
TARGET_TELEGRAM_CHAT_ID = int(os.getenv("TARGET_TELEGRAM_CHAT_ID", "-1002492065356"))

# ID Discord Channels
ID_DISCORD_BRIDGE = int(os.getenv("ID_DISCORD_BRIDGE", "1463438272440172641"))
ID_DISCORD_YOUTUBE = int(os.getenv("ID_DISCORD_YOUTUBE", "1463439746989690942"))
ID_DISCORD_TWITTER = int(os.getenv("ID_DISCORD_TWITTER", "1463574822540804137"))
ID_VERIFIKASI = int(os.getenv("ID_VERIFIKASI", "1463490143561449483"))
ID_WELCOME = int(os.getenv("ID_WELCOME", "1463592510797385974"))
ID_CHAT_INDO = int(os.getenv("ID_CHAT_INDO", "1463440826750206109"))
ID_CHAT_ENGLISH = int(os.getenv("ID_CHAT_ENGLISH", "1463440920522395743"))
NAMA_ROLE_VERIFIED = os.getenv("NAMA_ROLE_VERIFIED", "Pejuang WEB3")

# Branding Links
REF_LINK = os.getenv("REF_LINK", "https://bingx.pro/invite/JFQMWM")
TWITTER_LINK = os.getenv("TWITTER_LINK", "https://twitter.com/inokrambol")

# --- FLASK API CONFIGURATION ---
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"

# --- SETTINGS ---
JSON_FILE = "airdrop_recap.json"
JAKARTA_TZ = timezone(timedelta(hours=7))

# DAFTAR HASHTAG YANG AKAN DIPROSES OLEH BOT
ALLOWED_HASHTAGS = [
    '#airdrop', '#waitlist', '#update', '#instant', '#info', 
    '#yapping', '#testnet', '#garapan', '#retro', '#youtube', '#twitter'
]

# DAFTAR KATA KUNCI SPAM (AUTO DELETE)
SPAM_KEYWORDS = [
    'six figs', 'stay fucking poor', 'stay poor', 'giveaway', 
    'shilled by', 'join my channel', 'dm me for', 'profit', 
    'investment', 'invest', 'crypto pump', '1000$', '$1000',
    'bundle', 'trenches', 'making money', 'passive income',
    'click link below', 'prize pool',
    # --- SPAM BARU DARI USER ---
    'degen', 'degensmokers', 'every candle tells a story', 'stay grind',
    'alpha team', 'launching today', 'make sure you\'re not fading',
    '156x', '35x', '23x', 'massive marketing push',
    'dex boosts', 'join the channel', 'don\'t miss the launch',
    'samplayportal', 'personal buying', 'futures signal',
    'signal channel', 'minimal risk', 'just needs potential',
    'pump and dump', 'shitcoin', 'rugpull', 'exit scam',
    # --- CRYPTO PUMP & DUMP PATTERNS ---
    'degen fuel', 'pure degen', 'oil solana', 'u.s oil',
    'mc:', 'liq:', 'vol:', 'age:', 'mc - ', 'liquidity -',
    'shilled', 'shill by', '@molfieguns', 'contract:',
    'early', 'liquid and moving', 'moon soon', 'to the moon',
    'microcap', 'low cap', 'gem found', 'rare gem',
    'narrative', 'solana speed', 'solana network',
    'contract address', 'wallet address', 'token address'
]

PROCESSED_MSG_IDS = set()
MAX_CACHE_SIZE = 200

# ==========================================
# SETUP LOGGING & DATABASE
# ==========================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler(sys.stdout)]
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("discord").setLevel(logging.WARNING)

# ==========================================
# DATABASE FUNCTIONS (HYBRID: SQLite + MySQL)
# ==========================================

# Init SQLite (untuk backup lokal)
def init_sqlite_db():
    conn = sqlite3.connect('airdrop.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS airdrops
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  date TEXT, 
                  content TEXT, 
                  link TEXT)''')
    try: c.execute("SELECT poster FROM airdrops LIMIT 1")
    except sqlite3.OperationalError: c.execute("ALTER TABLE airdrops ADD COLUMN poster TEXT")
    try: c.execute("SELECT message_id FROM airdrops LIMIT 1")
    except sqlite3.OperationalError: c.execute("ALTER TABLE airdrops ADD COLUMN message_id INTEGER")
    try: c.execute("SELECT telegram_link FROM airdrops LIMIT 1")
    except sqlite3.OperationalError: c.execute("ALTER TABLE airdrops ADD COLUMN telegram_link VARCHAR(500)")
    try: c.execute("SELECT discord_link FROM airdrops LIMIT 1")
    except sqlite3.OperationalError: c.execute("ALTER TABLE airdrops ADD COLUMN discord_link VARCHAR(500)")
    try: c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_message_id ON airdrops(message_id)")
    except sqlite3.OperationalError: pass
    
    # Tabel untuk track recap message IDs (untuk auto-reply esok hari)
    c.execute('''CREATE TABLE IF NOT EXISTS recap_messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  recap_date TEXT UNIQUE,
                  telegram_msg_id BIGINT,
                  discord_msg_id BIGINT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()
    print("✅ SQLite initialized")

init_sqlite_db()

# Init MySQL (Production Database)
def init_mysql_db():
    global mysql_available
    if not MYSQL_AVAILABLE or not all(MYSQL_CONFIG.values()):
        print("⚠️ MySQL not configured. Skipping MySQL initialization.")
        return False
    
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS airdrops
                     (id INT AUTO_INCREMENT PRIMARY KEY,
                      date VARCHAR(255),
                      content LONGTEXT,
                      link VARCHAR(500),
                      poster VARCHAR(255),
                      message_id BIGINT UNIQUE,
                      source VARCHAR(255),
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        c.close()
        conn.close()
        print("✅ MySQL initialized")
        return True
    except Exception as e:
        print(f"❌ MySQL Connection Error: {e}")
        return False

mysql_available = init_mysql_db()

# Init Firebase Firestore
firestore_db = None
def init_firebase():
    global firestore_db, firebase_available
    if not FIREBASE_AVAILABLE:
        print("⚠️ Firebase not available. Skipping Firebase initialization.")
        return False
    
    try:
        # Cek apakah file credentials ada
        if not os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
            print(f"⚠️ Firebase credentials file '{SERVICE_ACCOUNT_KEY_PATH}' tidak ditemukan!")
            print("📝 Download dari Firebase Console (Service Account Key) ke folder project")
            return False
        
        # Initialize Firebase dengan credentials file
        cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
        firebase_admin.initialize_app(cred)
        firestore_db = firestore.client()
        
        print(f"✅ Firebase Firestore Connected: {FIREBASE_PROJECT_ID}")
        return True
    except Exception as e:
        print(f"❌ Firebase Connection Error: {e}")
        return False

firebase_available = init_firebase()

# Insert to MySQL
def insert_to_mysql(date, content, link, poster, message_id, source):
    if not mysql_available: return
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        c = conn.cursor()
        c.execute("""INSERT INTO airdrops 
                     (message_id, source_name, project_name, description, link, poster, posted_at) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s)
                     ON DUPLICATE KEY UPDATE 
                     posted_at=VALUES(posted_at)""",
                  (message_id, source, "", content[:255], link, poster, date))
        conn.commit()
        c.close()
        conn.close()
        logging.info("✅ Inserted to MySQL")
    except Exception as e:
        logging.error(f"❌ MySQL Insert Error: {e}")

# Insert to Firebase Firestore (Dual Storage)
def insert_to_firestore(date, content, link, poster, message_id, source):
    if not firestore_db or TARGET_FIRESTORE_USER_ID == "MASUKKAN_UID_USER_DARI_WEBSITE_DISINI": 
        return
    
    def save_to_firestore():
        try:
            urls = re.findall(r"https?://[^\s,\]\)]+", content)
            real_link = urls[0] if urls else link
            first_line = content.split('\n')[0].replace('*', '').replace('_', '').strip()
            project_name = first_line[:40] if len(first_line) > 40 else first_line
            
            tags = re.findall(r"#(\w+)", content)
            web_allowed = [tag.replace('#', '') for tag in ALLOWED_HASHTAGS]
            final_tags = [t.lower() for t in tags if t.lower() in web_allowed] or ['unknown']
            
            # Firestore path: artifacts/{FIREBASE_APP_ID}/users/{USER_ID}/tasks
            firestore_db.collection('artifacts').document(FIREBASE_APP_ID)\
                .collection('users').document(TARGET_FIRESTORE_USER_ID)\
                .collection('tasks').add({
                    "project": project_name,
                    "task": content[:1500],
                    "chain": "Unknown",
                    "link": real_link,
                    "source": source,
                    "tags": final_tags,
                    "walletId": "all",
                    "frequency": "Once",
                    "priority": "High",
                    "status": "Pending",
                    "createdAt": firestore.SERVER_TIMESTAMP,
                    "lastDoneDate": None,
                    "message_id": message_id,
                    "date": date
                })
            logging.info("✅ Synced to Firestore")
        except Exception as e:
            logging.error(f"❌ Firestore Error: {e}")
    
    # Run in background thread
    Thread(target=save_to_firestore, daemon=True).start()

# Init Groq
try:
    client = Groq(api_key=GROQ_API_KEY)
    print("✅ Groq AI Connected")
except Exception as e:
    print(f"❌ Groq Error: {e}")
    client = None

# ==========================================
# FLASK API CONFIGURATION
# ==========================================

app = Flask(__name__)
airdrops_data = []

@app.route('/api/airdrops', methods=['GET'])
def get_airdrops():
    """Return all airdrop data as JSON"""
    return jsonify(airdrops_data)

def start_flask():
    """Start Flask server in background"""
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, use_reloader=False, threaded=True)

# ==========================================
# BAGIAN DISCORD
# ==========================================

class CaptchaModal(discord.ui.Modal):
    def __init__(self, correct_code):
        super().__init__(title='Verifikasi Manusia')
        self.correct_code = correct_code
        self.captcha_input = discord.ui.TextInput(
            label=f'Ketik: {self.correct_code}', placeholder='Kode...', required=True, min_length=6, max_length=6
        )
        self.add_item(self.captcha_input)

    async def on_submit(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name=NAMA_ROLE_VERIFIED)
        if not role: return await interaction.response.send_message(f"❌ Role {NAMA_ROLE_VERIFIED} tidak ditemukan!", ephemeral=True)
        if self.captcha_input.value.upper() == self.correct_code:
            try:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f"✅ Sukses! Selamat datang.", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ Gagal beri role: {e}", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Kode salah.", ephemeral=True)

class VerifyView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label='Verifikasi', style=discord.ButtonStyle.green, custom_id='btn_v', emoji='🛡️')
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name=NAMA_ROLE_VERIFIED)
        if role in interaction.user.roles:
            await interaction.response.send_message("✅ Kamu sudah terverifikasi!", ephemeral=True)
            return
        await interaction.response.send_modal(CaptchaModal(''.join(random.choices(string.ascii_uppercase + string.digits, k=6))))

class CryptoDiscordBot(commands.Bot):
    def __init__(self): 
        intents = discord.Intents.all()
        super().__init__(command_prefix='!', intents=intents)
    async def setup_hook(self): self.add_view(VerifyView())
    async def on_ready(self): print(f"✅ Discord Login: {self.user}")
    async def on_member_join(self, member):
        ch = self.get_channel(ID_WELCOME)
        if ch:
            embed = discord.Embed(title="🚀 Selamat Datang di CryptoSRoom!", description=f"Halo {member.mention}, selamat bergabung!\n\n1️⃣ **Langkah Pertama:** Verifikasi di <#{ID_VERIFIKASI}>\n2️⃣ **Chat:** <#{ID_CHAT_INDO}> (ID) / <#{ID_CHAT_ENGLISH}> (EN)\n", color=discord.Color.blue())
            if member.display_avatar: embed.set_thumbnail(url=member.display_avatar.url)
            await ch.send(content=member.mention, embed=embed)
    async def on_message(self, message):
        if message.author.bot: return
        if "https://x.com/" in message.content or "https://twitter.com/" in message.content:
            pattern = r"https?://(x|twitter)\.com/[a-zA-Z0-9_]+/status/[0-9]+"
            match = re.search(pattern, message.content)
            if match:
                fixed_link = match.group(0).replace("x.com", "vxtwitter.com").replace("twitter.com", "vxtwitter.com")
                await message.reply(f"🔧 **Twitter Fixer:**\n{fixed_link}", mention_author=False)
        await self.process_commands(message)

discord_bot = CryptoDiscordBot()

@discord_bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    deskripsi_pesan = (
        "Selamat datang di **CryptoSRoom**! 🚀\n\n"
        "Untuk mendapatkan akses penuh ke komunitas, silakan verifikasi diri Anda dengan menekan tombol di bawah ini.\n\n"
        "**Apa yang akan Anda dapatkan di sini?**\n"
        "📚 **Belajar Web3 & Blockchain:** Panduan dari pemula hingga mahir.\n"
        "🪂 **Info Airdrop Terbaru:** Update garapan testnet, retro, dan instant airdrop.\n"
        "📈 **Analisa Trading:** Insight teknikal dan fundamental untuk trader.\n"
        "📰 **Berita Crypto Terupdate:** Jangan ketinggalan tren pasar terkini.\n"
        "💼 **Lowongan Kerja Web3:** Info karir dan freelance di dunia blockchain.\n\n"
        "👇 **Klik tombol Verifikasi di bawah untuk bergabung!**"
    )

    embed = discord.Embed(
        title="🛡️ Verifikasi Keamanan CryptoSRoom", 
        description=deskripsi_pesan, 
        color=discord.Color.blue()
    )
    embed.set_footer(text="CryptoSRoom Security System • Powered by Inokrambol")

    await ctx.send(embed=embed, view=VerifyView())
    await ctx.message.delete()

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def format_idr(value):
    try: return "Rp {:,.2f}".format(value).replace(',', 'X').replace('.', ',').replace('X', '.')
    except: return "Rp 0"

def get_usd_to_idr():
    try: return requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5).json()['rates']['IDR']
    except: return 16000.0

def get_binance_price(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol.upper()}USDT"
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5).json()
        if 'code' in resp: return None
        return {'symbol': symbol.upper(), 'last_price': float(resp['lastPrice']), 'change_percent': float(resp['priceChangePercent'])}
    except: return None

def is_admin(user_id): return user_id in ADMIN_USER_IDS
def escape_markdown(text): return text.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('`', '\\`') if text else ""

# --- JSON EXPORT FUNCTION ---
def export_to_json():
    try:
        conn = sqlite3.connect('airdrop.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT id, date, content, link, poster, message_id FROM airdrops ORDER BY date DESC")
        rows = c.fetchall()
        conn.close()

        json_data = []
        for row in rows:
            content_text = row[2]
            tags = re.findall(r"#(\w+)", content_text)
            tags_formatted = [f"#{t}" for t in tags]

            item = {
                "id": row[5] if row[5] else row[0], 
                "date": row[1],
                "link": row[3], 
                "source": row[4] if row[4] else "Admin", 
                "tags_detected": tags_formatted,
                "content": {
                    "full_text": content_text,
                    "has_media": False, 
                    "views": 0 
                }
            }
            json_data.append(item)

        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logging.error(f"JSON Export Error: {e}")
        return False

# --- AI RECAP FUNCTION (SHORT & CONCISE) ---
def get_ai_recap(rows):
    if not client: return None
    data_str = "\n".join([f"{i+1}. {r[1]} | {r[2]}" for i, r in enumerate(rows)])
    
    system_prompt = (
        "Bot crypto admin. Ubah data jadi list singkat untuk Telegram.\n"
        "ATURAN:\n"
        "1. Format Markdown: `No. [Judul](Link)` - HANYA INI\n"
        "2. Judul max 5 kata, dari konten pertama\n"
        "3. Gunakan LINK yang diberikan\n"
        "4. Langsung list nomor, no pembuka/penutup"
    )
    
    try:
        return client.chat.completions.create(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": data_str}],
            model="llama-3.3-70b-versatile", temperature=0.3
        ).choices[0].message.content
    except: return None

def get_ai_recap_with_links(rows):
    """AI Recap dengan link Telegram (untuk /rekap dan /rekaphari)"""
    if not client: return None
    data_str = "\n".join([f"{i+1}. {r[2][:50]} | {r[3]}" for i, r in enumerate(rows)])
    
    system_prompt = (
        "Bot crypto admin. Ubah data jadi list singkat untuk Telegram.\n"
        "ATURAN:\n"
        "1. Format Markdown: `No. [Judul](Link Telegram)` - HANYA INI\n"
        "2. Judul max 5 kata, dari konten airdrop\n"
        "3. Gunakan LINK TELEGRAM yang diberikan (bukan website)\n"
        "4. Langsung list nomor, no pembuka/penutup"
    )
    
    try:
        return client.chat.completions.create(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": data_str}],
            model="llama-3.3-70b-versatile", temperature=0.3
        ).choices[0].message.content
    except: return None

# ==========================================
# TELEGRAM HANDLERS
# ==========================================

async def delete_message_job(context: ContextTypes.DEFAULT_TYPE):
    try: await context.bot.delete_message(chat_id=context.job.data['chat_id'], message_id=context.job.data['message_id'])
    except: pass

async def unified_listener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global PROCESSED_MSG_IDS
    msg = update.effective_message
    if not msg: return
    text = msg.text or msg.caption or ""
    text_lower = text.lower()
    user_id = msg.from_user.id if msg.from_user else 0
    
    # DEBUG: Log semua message dengan hashtag
    if '#' in text:
        tags_found = re.findall(r"#(\w+)", text)
        logging.info(f"[DEBUG] Message received - Tags: {tags_found}, Text preview: {text[:100]}")

    # --- 0. ANTI SPAM (Satpam Otomatis) ---
    if not is_admin(user_id):
        if any(spam_word in text_lower for spam_word in SPAM_KEYWORDS):
            try:
                await msg.delete()
                logging.info(f"🚫 Spam deleted from {user_id}: {text[:50]}...")
            except Exception as e:
                logging.error(f"❌ Failed to delete spam: {e}")
            return

    # --- 0B. CRYPTO PRICE CHECKER (1 btc, 100 eth, etc) ---
    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔥 BingX", url=REF_LINK),
        InlineKeyboardButton("🐦 Twitter", url=TWITTER_LINK)
    ]])
    
    txt = text.strip()
    match = re.match(r'^(\d+(\.\d+)?)\s+([a-z0-9]+)$', txt)
    if match:
        amt, sym = float(match.group(1)), match.group(3)
        rate = get_usd_to_idr()
        
        if sym == 'usdt': 
            res = amt * rate
            await msg.reply_text(f"🇺🇸 {amt} USDT = {format_idr(res)}\n\n_Powered by Inokrambol_", parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
            return
        elif (d := get_binance_price(sym)): 
            arrow = "🟢" if d['change_percent'] >= 0 else "🔴"
            sign = "+" if d['change_percent'] >= 0 else ""
            msg_text = f"📊 **{d['symbol']} Price**\n💵 Price: `{d['last_price']} USDT`\n{arrow} 24h: `{sign}{d['change_percent']}%`\n💰 Est: `{format_idr(amt*d['last_price']*rate)}`\n\n_Powered by Inokrambol_"
            await msg.reply_text(msg_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
            return
    
    # --- Calculator mode (jika input seperti "1+1" atau "10*5") ---
    elif re.match(r'^[\d\s\.\+\-\*\/]+$', txt): 
        try: 
            res = simple_eval(txt)
            await msg.reply_text(f"🧮 Hasil: `{res}`\n\n_Powered by Inokrambol_", parse_mode=ParseMode.MARKDOWN)
            return
        except: 
            pass

    # --- 0C. AUTO AI RESPONSE (Hanya jika di-reply/di-tag atau mention INO AI) ---
    # Deteksi apakah bot di-reply atau di-mention
    is_reply_to_bot = msg.reply_to_message and msg.reply_to_message.from_user.is_bot
    is_mentioned = '@' in text_lower and ('ino' in text_lower or 'ai' in text_lower)
    has_ino_ai_tag = 'ino ai' in text_lower or 'ini ai' in text_lower
    
    # Respond hanya jika: di-reply ke bot, di-mention, atau ada "INO AI" di text
    if (is_reply_to_bot or is_mentioned or has_ino_ai_tag) and not any(tag in text_lower for tag in ALLOWED_HASHTAGS):
        if client and len(text) > 2:
            try:
                system_prompt = """Kamu adalah INO AI - bot crypto yang gaul, tengil, dan bikin kocak. 
Gaya: Jaksel casual, slightly sassy, entertaining.
RULES:
- Pakai bahasa Jakarta/gaul tapi tetap paham crypto
- Sesekali sombong/tengil tapi masih ramah
- Buat jawaban menghibur dan bikin orang ketawa
- Max 2-3 baris, ringkas tapi memorable
- Boleh pakai emoji yang cocok
- Jika dipanggil "INO AI", jawab dengan antusias dan sedikit sombong
- Hanya respond jika di-tag/di-reply/di-mention

Jawab dengan gaya INO AI yang gaul!"""
                
                response = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text}
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.7,
                    max_tokens=200
                )
                jawaban = response.choices[0].message.content
                await msg.reply_text(f"😎 {jawaban}")
                return
            except Exception as e:
                logging.error(f"❌ AI Error: {e}")
                return

    # --- 1. FILTER UTAMA (Admin & Hashtag Airdrop) ---
    if not any(tag in text_lower for tag in ALLOWED_HASHTAGS): return
    if not is_admin(user_id): return
    
    # Cek duplikat proses
    if msg.message_id in PROCESSED_MSG_IDS: return
    PROCESSED_MSG_IDS.add(msg.message_id)
    if len(PROCESSED_MSG_IDS) > MAX_CACHE_SIZE: PROCESSED_MSG_IDS.pop()

    link_utama = msg.link or f"https://t.me/c/{str(msg.chat.id).replace('-100', '')}/{msg.message_id}"
    poster = msg.from_user.username or "Admin"
    source_name = update.effective_chat.title or "Telegram Group"

    # 1. ADD TO FLASK API MEMORY
    try:
        urls = re.findall(r"(https?://[^\s,\]\)]+)", text)
        real_link = urls[0] if urls else link_utama
        tags = re.findall(r"#(\w+)", text)
        
        airdrops_data.append({
            "id": msg.message_id,
            "date": datetime.now(JAKARTA_TZ).strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": int(datetime.now(JAKARTA_TZ).timestamp()),
            "link": real_link,
            "sender_id": msg.from_user.id if msg.from_user else 0,
            "tags_detected": tags,
            "text": text,
            "source": source_name
        })
        logging.info("✅ Added to API memory")
    except Exception as e:
        logging.error(f"❌ API Memory Error: {e}")

    # 2. SQLITE & MYSQL & JSON & DISCORD
    try:
        conn = sqlite3.connect('airdrop.db')
        c = conn.cursor()
        c.execute("SELECT id FROM airdrops WHERE message_id = ?", (msg.message_id,))
        if not c.fetchone():
            date_str = datetime.now(JAKARTA_TZ).strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO airdrops (date, content, link, poster, message_id) VALUES (?, ?, ?, ?, ?)",
                      (date_str, text[:2000], link_utama, poster, msg.message_id))
            conn.commit()
            
            # Insert to MySQL dan Firestore (Dual Storage)
            insert_to_mysql(date_str, text[:2000], link_utama, poster, msg.message_id, source_name)
            insert_to_firestore(date_str, text[:2000], link_utama, poster, msg.message_id, source_name)
            
            export_to_json()
        conn.close()
    except Exception as e: 
        logging.error(f"DB Error: {e}")

    # 3. DISCORD FORWARD (gunakan Thread karena discord_bot tidak async-friendly)
    try:
        # Simpan photo info untuk Thread
        photo_file_id = msg.photo[-1].file_id if msg.photo else None
        
        def send_to_discord():
            try:
                # Ekstrak hashtag dan link dari text
                tags = re.findall(r"#(\w+)", text)
                urls = re.findall(r"https?://[^\s,\]\)]+", text)
                real_link = urls[0] if urls else link_utama
                
                # Format Discord message - keep link
                msg_text = f"{text}\n\n---\nPowered by Inokrambol"
                
                embed = discord.Embed(description=msg_text, color=0x0099ff)
                
                # Jika ada photo, download dan attach ke Discord (gambar di atas)
                file_obj = None
                if photo_file_id:
                    try:
                        from io import BytesIO
                        
                        # Step 1: Get file path dari Telegram API
                        file_info_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={photo_file_id}"
                        file_info_resp = requests.get(file_info_url, timeout=10).json()
                        
                        if file_info_resp.get('ok'):
                            file_path = file_info_resp['result']['file_path']
                            # Step 2: Download file
                            download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
                            photo_data = requests.get(download_url, timeout=15).content
                            file_obj = discord.File(BytesIO(photo_data), filename="image.png")
                            embed.set_image(url="attachment://image.png")
                    except Exception as e:
                        logging.warning(f"Photo download error: {e}")
                
                # Tentukan channel Discord berdasarkan hashtag
                channel_id = ID_DISCORD_BRIDGE  # Default channel
                
                # Routing berdasarkan hashtag
                tags_lower = [tag.lower() for tag in tags]
                logging.info(f"[ROUTING] Tags detected: {tags_lower}, Full text: {text[:100]}")
                
                if 'youtube' in tags_lower:
                    channel_id = ID_DISCORD_YOUTUBE
                    logging.info(f"✅ [ROUTING] MATCHED YOUTUBE! Routing to YouTube channel: {ID_DISCORD_YOUTUBE}")
                elif 'twitter' in tags_lower:
                    channel_id = ID_DISCORD_TWITTER
                    logging.info(f"✅ [ROUTING] MATCHED TWITTER! Routing to Twitter channel: {ID_DISCORD_TWITTER}")
                else:
                    logging.info(f"[ROUTING] No specific match - Routing to Bridge channel (default): {ID_DISCORD_BRIDGE}")
                
                # Kirim ke Discord ke channel yang sesuai
                ch = discord_bot.get_channel(channel_id)
                if ch:
                    if file_obj:
                        asyncio.run_coroutine_threadsafe(ch.send(embed=embed, file=file_obj), discord_bot.loop)
                        logging.info(f"Forward to Discord ({channel_id}) dengan photo")
                    else:
                        asyncio.run_coroutine_threadsafe(ch.send(embed=embed), discord_bot.loop)
                        logging.info(f"Forward to Discord ({channel_id}): {text[:50]}")
                else:
                    logging.warning(f"Channel {channel_id} tidak ditemukan!")
            except Exception as e:
                logging.error(f"Discord send error: {e}")
        
        # Jalankan di background thread
        Thread(target=send_to_discord, daemon=True).start()
    except Exception as e:
        logging.error(f"Discord Forward Error: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot aktif!\nKirim #airdrop untuk auto-forward.")

async def recap_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("❌ Hanya admin yang bisa pakai command ini!")
        return
    
    try:
        conn = sqlite3.connect('airdrop.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT date, content, link FROM airdrops ORDER BY date DESC LIMIT 10")
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            await update.message.reply_text("Belum ada airdrop yang tercatat")
            return
        
        recap = get_ai_recap(rows)
        if recap:
            await update.message.reply_text(f"📋 **Recap Airdrop Terbaru (10 terakhir):**\n\n{recap}", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("❌ AI Error, coba lagi nanti")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("❌ Hanya admin yang bisa pakai command ini!")
        return
    
    try:
        conn = sqlite3.connect('airdrop.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM airdrops")
        total = c.fetchone()[0]
        conn.close()
        
        await update.message.reply_text(f"📊 **Statistics:**\nTotal Airdrop: {total}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def tanya_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /tanya - User bisa bertanya apapun"""
    if not context.args:
        await update.message.reply_text("🤔 Mau tanya apa sir?")
        return
    
    pertanyaan = ' '.join(context.args)
    
    if not client:
        await update.message.reply_text("❌ AI tidak tersedia saat ini")
        return
    
    try:
        system_prompt = """Kamu adalah INO AI - bot crypto yang gaul, tengil, dan bikin kocak. 
Gaya: Jaksel casual, slightly sassy, entertaining.
RULES:
- Pakai bahasa Jakarta/gaul tapi tetap paham crypto
- Sesekali sombong/tengil tapi masih ramah
- Buat jawaban menghibur dan bikin orang ketawa
- Max 3 baris, ringkas tapi memorable
- Boleh pakai emoji yang cocok

Contoh gaya:
Q: "Apa itu Bitcoin?" 
A: "Lah itu sih uang digital yang bikin orang kaya atau bangkrut. Gw sih tim hodl 💎"

Q: "Berapa harga ETH?"
A: "Bro, ETH tuh coin favorit smart people. Harganya? Cek CoinGecko, gw gak jadi teller bank 😎"

Jawab dengan gaya INO AI yang gaul!"""
        
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": pertanyaan}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=200
        )
        
        jawaban = response.choices[0].message.content
        await update.message.reply_text(f"😎 {jawaban}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error AI: {str(e)[:100]}")

async def show_recap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /rekap - Tampilkan 10 airdrop terakhir dengan link Telegram"""
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("❌ Hanya admin!")
        return
    
    try:
        conn = sqlite3.connect('airdrop.db')
        rows = conn.execute("SELECT id, date, content, telegram_link, poster FROM airdrops ORDER BY id DESC LIMIT 10").fetchall()
        conn.close()
        
        if not rows:
            await update.message.reply_text("📭 Belum ada airdrop")
            return
        
        # Format manual jika AI tidak jalan
        txt_manual = "\n".join([f"{i+1}. [{r[2][:40]}...]({r[3]})" for i, r in enumerate(rows)])
        txt = get_ai_recap_with_links(rows) or f"Manual Mode:\n{txt_manual}"
        
        kb = [
            [InlineKeyboardButton("🔥 BingX", url=REF_LINK)],
            [InlineKeyboardButton("🐦 Twitter", url=TWITTER_LINK)]
        ]
        
        await update.message.reply_text(
            f"📋 **REKAP TERBARU**\n\n{txt}\n\n_Powered by Inokrambol_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(kb),
            disable_web_page_preview=True
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")

async def show_daily_recap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /rekaphari - Tampilkan airdrop hari ini dengan link Telegram"""
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("❌ Hanya admin!")
        return
    
    try:
        msg = await update.message.reply_text("⏳ Loading...")
        
        today = datetime.now(JAKARTA_TZ).strftime("%Y-%m-%d")
        
        conn = sqlite3.connect('airdrop.db')
        rows = conn.execute("SELECT id, date, content, telegram_link, discord_link, poster FROM airdrops WHERE date LIKE ? ORDER BY id DESC", (f"{today}%",)).fetchall()
        conn.close()
        
        if not rows:
            return await msg.edit_text(f"📭 Kosong hari ini ({today})")
        
        txt_manual = "\n".join([f"{i+1}. [{r[2][:40]}...]({r[3]})" for i, r in enumerate(rows)])
        txt = get_ai_recap_with_links(rows) or f"Manual Mode:\n{txt_manual}"
        
        final = f"☀️ **REKAP {today}**\n\n{txt}\n\n_Powered by Inokrambol_"
        
        await msg.edit_text(final, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)[:100]}")

async def recap_now_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /recap_now - Manual trigger scheduler untuk posting recap ke group (admin only)"""
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("❌ Hanya admin yang bisa trigger /recap_now!")
        return
    
    try:
        msg = await update.message.reply_text("⏳ Posting recap ke group sekarang...")
        
        # Trigger scheduler job ke TARGET_TELEGRAM_CHAT_ID (group/channel)
        await send_daily_recap_job(context, chat_id=None)
        
        await msg.edit_text("✅ Recap berhasil diposting ke group & Discord!")
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)[:100]}")
        logging.error(f"recap_now error: {e}")

async def recap_me_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /recap_me - Kirim recap ke private chat user (siapa saja bisa)"""
    user_id = update.message.from_user.id
    
    try:
        msg = await update.message.reply_text("⏳ Generate recap dan kirim ke private chat Anda...")
        
        # Trigger scheduler job ke private chat user
        await send_daily_recap_job(context, chat_id=user_id)
        
        await msg.edit_text("✅ Recap berhasil dikirim ke private chat Anda!")
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)[:100]}")
        logging.error(f"recap_me error: {e}")

async def clear_recap_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /hapus_rekap - Hapus semua airdrop (admin only)"""
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("❌ Hanya admin!")
        return
    
    try:
        conn = sqlite3.connect('airdrop.db')
        conn.execute("DELETE FROM airdrops")
        conn.commit()
        conn.close()
        await update.message.reply_text("🗑️ Semua airdrop sudah dihapus!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")

async def send_daily_recap_job(context: ContextTypes.DEFAULT_TYPE, chat_id: int = None):
    """Scheduler job - Kirim rekap harian per kategori hashtag ke Telegram & Discord
    
    Args:
        context: Telegram context
        chat_id: Optional - Jika ada, kirim ke chat_id ini. Jika None, kirim ke TARGET_TELEGRAM_CHAT_ID (default)
    """
    try:
        # Default: kirim ke TARGET_TELEGRAM_CHAT_ID (group)
        destination_chat_id = chat_id or TARGET_TELEGRAM_CHAT_ID
        
        logging.info(f"[SCHEDULER] Starting daily recap job at {datetime.now(JAKARTA_TZ)}")
        logging.info(f"[SCHEDULER] Destination: {destination_chat_id}")
        
        yesterday = (datetime.now(JAKARTA_TZ) - timedelta(days=1)).strftime("%Y-%m-%d")
        logging.info(f"[SCHEDULER] Querying data for {yesterday}")
        
        # Query dari SQLite - data sebenarnya ada di sini
        conn_sqlite = sqlite3.connect('airdrop.db')
        rows = conn_sqlite.execute(
            "SELECT id, content, date, link, poster FROM airdrops WHERE date LIKE ? ORDER BY id ASC",
            (f"{yesterday}%",)
        ).fetchall()
        conn_sqlite.close()
        
        logging.info(f"[SCHEDULER] Found {len(rows)} entries for {yesterday}")
        
        # Jika tidak ada airdrop, tetap posting pesan kosong (jangan return)
        if not rows:
            logging.info(f"📭 Tidak ada airdrop untuk {yesterday}")
            rows = []
        
        # Kategorisasi per hashtag - lengkap
        categories = {
            'info': [],
            'whitelist': [],
            'update': [],
            'youtube': [],
            'twitter': [],
            'airdrop': [],
            'retro': [],
            'testnet': [],
            'node': [],
            'daily': [],
            'landing': [],
            'other': []
        }
        
        for row in rows:
            # row structure from SQLite: (id, content, date, link, poster)
            content = row[1]
            telegram_link = row[3] if row[3] else "https://t.me/Warkop_CR"
            
            if not telegram_link or telegram_link == "None":
                logging.warning(f"Link kosong untuk: {content[:50]}")
                telegram_link = "https://t.me/Warkop_CR"
            
            # Ambil judul dari baris pertama
            title = content.split('\n')[0].strip()
            title = re.sub(r'#\w+\s?', '', title).strip()
            if not title:
                title = content[:40]
            
            # Kategorisasi per hashtag - prioritas dari atas ke bawah
            content_lower = content.lower()
            if '#info' in content_lower:
                categories['info'].append((title, telegram_link))
            elif '#whitelist' in content_lower or '#waitlist' in content_lower:
                categories['whitelist'].append((title, telegram_link))
            elif '#update' in content_lower:
                categories['update'].append((title, telegram_link))
            elif '#youtube' in content_lower:
                categories['youtube'].append((title, telegram_link))
            elif '#twitter' in content_lower:
                categories['twitter'].append((title, telegram_link))
            elif '#retro' in content_lower or '#retroactive' in content_lower:
                categories['retro'].append((title, telegram_link))
            elif '#testnet' in content_lower:
                categories['testnet'].append((title, telegram_link))
            elif '#node' in content_lower:
                categories['node'].append((title, telegram_link))
            elif '#daily' in content_lower:
                categories['daily'].append((title, telegram_link))
            elif '#landing' in content_lower or '#landingpage' in content_lower:
                categories['landing'].append((title, telegram_link))
            elif '#airdrop' in content_lower:
                categories['airdrop'].append((title, telegram_link))
            else:
                categories['other'].append((title, telegram_link))
        
        # Format untuk Telegram - semua kategori
        msg_tg = f"Halo Penghuni CryptoSRoom! Berikut garapan {yesterday}:\n\n"
        has_content = False
        
        if categories['info']:
            msg_tg += "ℹ️ Info Project\n"
            for i, (title, link) in enumerate(categories['info'], 1):
                msg_tg += f"{i}. [{title}]({link})\n"
            msg_tg += "\n"
            has_content = True
        
        if categories['whitelist']:
            msg_tg += "📋 Garapan Whitelist\n"
            for i, (title, link) in enumerate(categories['whitelist'], 1):
                msg_tg += f"{i}. [{title}]({link})\n"
            msg_tg += "\n"
            has_content = True
        
        if categories['update']:
            msg_tg += "📊 Garapan Update\n"
            for i, (title, link) in enumerate(categories['update'], 1):
                msg_tg += f"{i}. [{title}]({link})\n"
            msg_tg += "\n"
            has_content = True
        
        if categories['youtube']:
            msg_tg += "📺 YouTube Update\n"
            for i, (title, link) in enumerate(categories['youtube'], 1):
                msg_tg += f"{i}. [{title}]({link})\n"
            msg_tg += "\n"
            has_content = True
        
        if categories['twitter']:
            msg_tg += "🐦 Twitter Update\n"
            for i, (title, link) in enumerate(categories['twitter'], 1):
                msg_tg += f"{i}. [{title}]({link})\n"
            msg_tg += "\n"
            has_content = True
        
        if categories['retro']:
            msg_tg += "🔄 Garapan Retro\n"
            for i, (title, link) in enumerate(categories['retro'], 1):
                msg_tg += f"{i}. [{title}]({link})\n"
            msg_tg += "\n"
            has_content = True
        
        if categories['testnet']:
            msg_tg += "🧪 Garapan Testnet\n"
            for i, (title, link) in enumerate(categories['testnet'], 1):
                msg_tg += f"{i}. [{title}]({link})\n"
            msg_tg += "\n"
            has_content = True
        
        if categories['node']:
            msg_tg += "🖥️ Garapan Node\n"
            for i, (title, link) in enumerate(categories['node'], 1):
                msg_tg += f"{i}. [{title}]({link})\n"
            msg_tg += "\n"
            has_content = True
        
        if categories['daily']:
            msg_tg += "📅 Garapan Daily\n"
            for i, (title, link) in enumerate(categories['daily'], 1):
                msg_tg += f"{i}. [{title}]({link})\n"
            msg_tg += "\n"
            has_content = True
        
        if categories['airdrop']:
            msg_tg += "🚀 Garapan Airdrops\n"
            for i, (title, link) in enumerate(categories['airdrop'], 1):
                msg_tg += f"{i}. [{title}]({link})\n"
            msg_tg += "\n"
            has_content = True
        
        if categories['landing']:
            msg_tg += "🎯 Garapan Landing\n"
            for i, (title, link) in enumerate(categories['landing'], 1):
                msg_tg += f"{i}. [{title}]({link})\n"
            msg_tg += "\n"
            has_content = True
        
        if categories['other']:
            msg_tg += "📌 Garapan Lainnya\n"
            for i, (title, link) in enumerate(categories['other'], 1):
                msg_tg += f"{i}. [{title}]({link})\n"
            msg_tg += "\n"
            has_content = True
        
        if has_content:
            msg_tg += f"---\nPowered by Inokrambol\n[🐦 Twitter]({TWITTER_LINK})\n[📺 YouTube](https://www.youtube.com/@DiscussionAirdrops)\nRekap: {yesterday}"
        else:
            msg_tg = f"📭 Tidak ada garapan untuk {yesterday}"
        
        # Kirim ke Telegram
        try:
            logging.info(f"[SCHEDULER] Sending recap to Telegram chat {destination_chat_id}")
            await context.bot.send_message(
                destination_chat_id,
                text=msg_tg,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            logging.info(f"✅ [SCHEDULER] Recap successfully sent to Telegram (chat_id: {destination_chat_id}) for {yesterday}")
        except Exception as e:
            logging.error(f"❌ [SCHEDULER] Telegram recap error: {str(e)}")
            logging.error(f"Chat ID: {destination_chat_id}, Message length: {len(msg_tg)}")
    
    except Exception as e:
        logging.error(f"❌ [SCHEDULER] Daily recap job error: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())

# ==========================================
# MAIN SETUP
# ==========================================

def main():
    # ==========================================
    # CRITICAL: Prevent Multiple Bot Instances
    # ==========================================
    import os
    pid_file = "/tmp/airdrop_bot.pid"
    
    # Check jika ada instance bot yang sudah jalan
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            # Check apakah process dengan PID lama masih jalan
            os.kill(old_pid, 0)  # Jika error, process sudah dead
            logging.error(f"❌ Bot sudah jalan dengan PID: {old_pid}. STOP existing instance dulu!")
            logging.error(f"❌ Gunakan: kill {old_pid}")
            return  # Exit tanpa start bot baru
        except (OSError, ValueError):
            pass  # Process lama sudah dead, lanjut
    
    # Simpan PID bot saat ini
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    logging.info(f"✅ Bot instance started with PID: {os.getpid()}")
    
    # Start Flask in background
    flask_thread = Thread(target=start_flask, daemon=True)
    flask_thread.start()
    logging.info("✅ Flask API started")
    
    # Telegram Bot
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).request(HTTPXRequest(read_timeout=30)).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("recap", recap_command))
    app.add_handler(CommandHandler("rekap", show_recap))
    app.add_handler(CommandHandler("rekaphari", show_daily_recap))
    app.add_handler(CommandHandler("recap_now", recap_now_command))
    app.add_handler(CommandHandler("recap_me", recap_me_command))
    app.add_handler(CommandHandler("hapus_rekap", clear_recap_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("tanya", tanya_command))
    app.add_handler(MessageHandler(filters.TEXT | filters.CAPTION, unified_listener))
    
    # Setup Daily Recap Scheduler (jam 00:00 / 12 malam, timezone Jakarta)
    job_queue = app.job_queue
    job_queue.start()  # PENTING: Scheduler harus di-start!
    
    # Check: Prevent duplikasi scheduler job jika bot restart/multiple instance
    existing_jobs = job_queue.jobs()
    has_daily_job = any(job.callback == send_daily_recap_job for job in existing_jobs)
    
    if not has_daily_job:
        job_queue.run_daily(
            send_daily_recap_job,
            time=time(hour=0, minute=0, tzinfo=JAKARTA_TZ),
            days=[0, 1, 2, 3, 4, 5, 6]
        )
        logging.info("✅ Daily recap scheduler CREATED (00:00 setiap hari, timezone: Jakarta)")
    else:
        logging.info("⚠️ Daily recap scheduler ALREADY EXISTS - skipping duplicate")
    
    logging.info(f"📊 Total active jobs: {len(job_queue.jobs())}")
    
    # Discord Bot
    discord_thread = Thread(target=discord_bot.run, args=(DISCORD_BOT_TOKEN,), daemon=True)
    discord_thread.start()
    logging.info("✅ Discord Bot started")
    
    # Telegram Bot
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 INOKRAMBOL BOT STARTING...")
    print("=" * 50)
    print(f"✅ Telegram: Connected")
    print(f"✅ Discord: Connected")
    print(f"✅ Groq AI: Connected")
    print(f"✅ SQLite: Connected")
    print(f"✅ MySQL: {'Connected' if mysql_available else 'Pending'}")
    print("=" * 50)
    main()
