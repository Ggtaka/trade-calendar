import sqlite3

def init_db():
    conn = sqlite3.connect("trades.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            symbol TEXT,
            qty INTEGER,
            pnl REAL,
            timestamp TEXT
        )
    """)
    conn.commit()
    return conn

def insert_trade(conn, trade):
    conn.execute(
        "INSERT INTO trades (date, symbol, qty, pnl, timestamp) VALUES (?, ?, ?, ?, ?)",
        trade
    )
    conn.commit()

def get_all_trades(conn):
    return conn.execute("SELECT * FROM trades").fetchall()

def get_trades_by_date(conn, date):
    return conn.execute("SELECT * FROM trades WHERE date = ?", (date,)).fetchall()

def delete_all_trades(conn):
    conn.execute("DELETE FROM trades")
    conn.commit()
