import sqlite3
from datetime import date

DB = "pretiosus.db"

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            lang TEXT DEFAULT 'ru',
            cash INTEGER DEFAULT 1000,
            crystals INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            games INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            last_daily TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            user_id INTEGER,
            item TEXT,
            PRIMARY KEY (user_id, item)
        )
    """)
    conn.commit()
    conn.close()

def ensure_player(user_id, username, first_name):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM players WHERE user_id = ?", (user_id,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO players (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name)
        )
        conn.commit()
    conn.close()

def get_player(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row

def set_lang(user_id, lang):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE players SET lang = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()
    conn.close()

def get_lang(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT lang FROM players WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else "ru"

def add_cash(user_id, amount):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE players SET cash = cash + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def add_crystals(user_id, amount):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE players SET crystals = crystals + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def spend(user_id, cash=0, crystals=0):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT cash, crystals FROM players WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False
    cur_cash, cur_cryst = row
    if cur_cash < cash or cur_cryst < crystals:
        conn.close()
        return False
    cur.execute(
        "UPDATE players SET cash = cash - ?, crystals = crystals - ? WHERE user_id = ?",
        (cash, crystals, user_id)
    )
    conn.commit()
    conn.close()
    return True

def add_item(user_id, item):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO inventory (user_id, item) VALUES (?, ?)", (user_id, item))
    conn.commit()
    conn.close()

def get_inventory(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT item FROM inventory WHERE user_id = ?", (user_id,))
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows

def consume_item(user_id, item):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM inventory WHERE user_id = ? AND item = ?", (user_id, item))
    conn.commit()
    conn.close()

def inc_game(user_id, win=False):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    if win:
        cur.execute("UPDATE players SET games = games + 1, wins = wins + 1, streak = streak + 1 WHERE user_id = ?", (user_id,))
    else:
        cur.execute("UPDATE players SET games = games + 1, streak = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def claim_daily(user_id):
    today = date.today().isoformat()
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT last_daily FROM players WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if row and row[0] == today:
        conn.close()
        return False
    cur.execute("UPDATE players SET last_daily = ?, cash = cash + 500, crystals = crystals + 1 WHERE user_id = ?",
                (today, user_id))
    conn.commit()
    conn.close()
    return True

def top_players(limit=10):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT first_name, username, wins, games FROM players ORDER BY wins DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows
