#!/data/data/com.termux/files/usr/bin/python
import sqlite3
import json
import urllib.request
import time

DB = "/data/data/com.termux/files/home/montidroid.db"

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS blockchain_transactions (
            hash TEXT PRIMARY KEY,
            utime INTEGER,
            in_msg TEXT,
            from_addr TEXT,
            to_addr TEXT,
            amount TEXT
        );
        CREATE TABLE IF NOT EXISTS blockchain_messages (
            id TEXT PRIMARY KEY,
            op_code INTEGER,
            decoded_op TEXT,
            utime INTEGER
        );
        CREATE TABLE IF NOT EXISTS blockchain_accounts (
            id TEXT PRIMARY KEY,
            human_readable TEXT
        );
    """)
    conn.commit()
    conn.close()

def fetch_and_store():
    # Example: fetch last 50 transactions from a well‑known TON wallet
    address = "EQCD39VS5jcptHL8vMjEXrzGaRcCVYrq6zZ-3fX9U4pVq5N"
    url = f"https://toncenter.com/api/v2/getTransactions?address={address}&limit=50"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read())
    except Exception as e:
        print(f"API error: {e}")
        return

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    for tx in data.get("result", []):
        tx_hash = tx.get("transaction_id", {}).get("hash")
        utime = tx.get("utime")
        in_msg = tx.get("in_msg", {})
        from_addr = in_msg.get("source")
        to_addr = in_msg.get("destination")
        amount = in_msg.get("value")
        cur.execute("INSERT OR IGNORE INTO blockchain_transactions VALUES (?,?,?,?,?,?)",
                    (tx_hash, utime, json.dumps(in_msg), from_addr, to_addr, amount))
        # Insert a dummy message for op code queries
        cur.execute("INSERT OR IGNORE INTO blockchain_messages (id, utime) VALUES (?,?)",
                    (tx_hash + ":msg", utime))
    conn.commit()
    count = cur.execute("SELECT COUNT(*) FROM blockchain_transactions").fetchone()[0]
    print(f"✅ Imported {count} transactions")
    conn.close()

if __name__ == "__main__":
    init_db()
    fetch_and_store()
