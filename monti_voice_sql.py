#!/data/data/com.termux/files/usr/bin/python
import whisper
import sqlite3
import sys

DB_PATH = "/data/data/com.termux/files/home/montidroid.db"

def voice_to_sql(audio_file):
    model = whisper.load_model("tiny", device="cpu")
    result = model.transcribe(audio_file)
    text = result["text"].lower()
    print(f"Recognised: {text}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if "top addresses" in text:
        cur.execute("SELECT from_addr, COUNT(*) FROM blockchain_transactions GROUP BY from_addr ORDER BY COUNT(*) DESC LIMIT 5")
        for row in cur.fetchall():
            print(f"Address {row[0]}: {row[1]} txns")
    elif "total transactions" in text:
        cur.execute("SELECT COUNT(*) FROM blockchain_transactions")
        print(f"Total transactions: {cur.fetchone()[0]}")
    else:
        print("Command not recognised. Try 'top addresses' or 'total transactions'")
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python monti_voice_sql.py <audio.wav>")
    else:
        voice_to_sql(sys.argv[1])
